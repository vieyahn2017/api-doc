# -*- coding:utf-8 -*-
import time
import utils
import constant
from tornado.log import app_log
from core import EventHub, cache_client, SystemStatus, context

class BaseWatcher(object):
    def __init__(self):
        self._evthub = EventHub()
        self.register_user_evts()

    def register_user_evts(self):
        pass

    @classmethod
    def install(watcher):
        watcher()
        app_log.debug("Event Hook [%s] install ok" % watcher)

class SystemAlertWatcher(BaseWatcher):
    def register_user_evts(self):
        self._evthub.hook("cacheserver.down", self.cacheserver_down)
        self._evthub.hook("cacheserver.up", self.cacheserver_up)
        self._evthub.hook("database.down", self.database_down)

    def cacheserver_down(self, data):
        if SystemStatus.cache_server_up():
            app_log.error("Cache Server was Down!!!")
            SystemStatus.set_cache_server_status(constant.CACHE_SERVER_DOWN)
            context["executor"].submit(self._check_cache_state)

    def _check_cache_state(self):
        from utils import getmc
        app_log.debug("start memcached state check thread")
        while 1:
            try:
                client = getmc()
                client.get_stats()
                app_log.debug("memcached come back!")
                self._evthub.emit_system_notify("cacheserver.up", "")
                break
            except:
                app_log.warn("memcached still down!")
            time.sleep(5)

    def cacheserver_up(self, data):
        SystemStatus.set_cache_server_status(constant.CACHE_SERVER_UP)
        app_log.error("Cache Server was UP")

    def database_down(self, data):
        pass


class UserLoginWatcher(BaseWatcher):

    def register_user_evts(self):
        self._evthub.hook("user.logined", self.user_login_event)

    def user_login_event(self, user):
        app_log.debug("%s logined" % user.username)


class SyncSystemMessage(BaseWatcher):
    def register_user_evts(self):
        self._evthub.hook("user.logined", self._sync_system_msg)

    def _sync_system_msg(self, user):
        from models import Notice
        context.get("executor").submit(Notice.pull_mynotice, user.id)


class CacheFlushWatcher(BaseWatcher):

    def __init__(self):
        super(CacheFlushWatcher, self).__init__()
        self._cache = cache_client()

    def register_user_evts(self):
        self._evthub.hook("model.created", self.flush_model)
        self._evthub.hook("model.deleted", self.flush_model)
        self._evthub.hook("model.updated", self.flush_model)

    def flush_model(self, model, *extra):
        if SystemStatus.cache_server_down():
            return
        table = model.__storm_table__
        model_cls = model.__class__
        tables = utils.table_name(model_cls.get_cache_keys())
        relation_tables = utils.tables_key(tables)
        need_remove_keys = self._cache.get_multi(relation_tables) or []

        if need_remove_keys:
            final_keys = []
            for table_key, rel_key_list in need_remove_keys.iteritems():
                final_keys.append(table_key)
                for rel_key in rel_key_list:
                    final_keys.append(rel_key)

            app_log.debug(
                        "invalidate model cache %s with keys %s " % \
                                            (table, str(final_keys)))
            self._cache.delete_multi(final_keys)


class UserWatcher(CacheFlushWatcher):

    def __init__(self):
        super(UserWatcher, self).__init__()

    def register_user_evts(self):
        self._evthub.hook("student.created", self._student_created)
        self._evthub.hook("student.updated", self._student_updated)
        self._evthub.hook("student.deleted", self._student_deleted)
        self._evthub.hook("teacher.created", self._teacher_created)
        self._evthub.hook("teacher.updated", self._teacher_updated)
        self._evthub.hook("teacher.deleted", self._teacher_deleted)
        self._evthub.hook("password.changed", self._password_changed)
        self._evthub.hook("profile.changed", self._profile_changed)

    def _student_created(self, student, *data):
        self.flush_model(student, *data)
        app_log.debug("student %s created" % student.username)

    def _student_updated(self, student, *data):
        self.flush_model(student, *data)
        app_log.debug("student %s updated" % student.username)

    def _student_deleted(self, student, *data):
        self.flush_model(student, *data)
        app_log.debug("student %s deleted" % student.username)

    def _teacher_created(self, teacher, *data):
        self.flush_model(teacher, *data)

    def _teacher_updated(self, teacher, *data):
        self.flush_model(teacher, *data)

    def _teacher_deleted(self, teacher, *data):
        self.flush_model(teacher, *data)

    def _password_changed(self, userinfo):
        newpwd, loginid = userinfo
        userinfo = self._cache.get(loginid)
        if userinfo:
            userinfo.userpwd = newpwd
            self._cache.set(loginid, userinfo)
            app_log.debug("%s password changed" % loginid)

    def _profile_changed(self, user):
        maybe_loginid = (user.nickname, user.userid)
        for loginid in maybe_loginid:
            userinfo = self._cache.get(loginid)
            if userinfo:
                userinfo.usermail = user.usermail
                userinfo.usersex = user.usersex
                userinfo.userphone = user.userphone
                userinfo.userphoto = user.userphoto
                self._cache.set(loginid, userinfo)
                app_log.debug("invalidate %s profile" % loginid)


class NoticeWatcher(BaseWatcher):
    def register_user_evts(self):
        self._evthub.hook("sendto.user", self._sendmsg)
        self._evthub.hook("sendto.class", self._send_to_class)

    def _sendmsg(self, msg):
        who, user_id, title, body = msg
        app_log.debug("send %s to userid:%d" % (body, user_id))

    def _send_to_class(self, msg):
        who, schoolcls, title, body = msg
        app_log.debug("send %s:%s to banji:%s" % (title, body, str(schoolcls)))
