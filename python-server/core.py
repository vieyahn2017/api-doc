#!/usr/bin/env python
#-*-coding:utf-8 -*-
#
#Author: tony - birdaccp at gmail.com
#Create by:2015-05-26 13:28:10
#Last modified:2017-05-26 15:59:50
#Filename:core.py
#Description:
import sys
import copy
import weakref
from tornado.log import app_log
from collections import defaultdict
from threading import local

from tornado.ioloop import IOLoop

import motor

import utils
import constant
from config import settings, mongodbConf

class ThreadLocalStore(local):
    __metaclass__ = utils.Singleton

    def __init__(self):
        self._store = {}

    def __contains__(self, key):
        return key in self._store

    def save(self, key, value):
        self._store[key] = value

    def get(self, key):
        if key in self:
            return self._store[key]

    def delete(self, key):
        if key in self:
            del self._store[key]

    @staticmethod
    def instance():
        return ThreadLocalStore._instance

localstore = ThreadLocalStore()

class Context(object):
    '''
    A Context class used to save global information
    '''
    __metaclass__ = utils.Singleton

    def __init__(self):
        self.store = {}

    def __setitem__(self, key, value):
        self.store[key] = value

    def __getitem__(self, key):
        return self.store[key]

    def __delitem__(self, key):
        if key in self.store:
            del self.store[key]

    def __contains__(self, key):
        return key in self.store

    def setdefault(self, key, value):
        if key not in self.store:
            self.store[key] = value
        return value

    def clear_keys(self, keylist):
        '''
        It used to clear special key in self.store
        '''
        for key in keylist:
            if key in self.store:
                del self.store[key]

    def clear_all(self):
        '''
        It used to clear all key in self.store
        '''
        keys = filter(lambda key:
                    key not in ("db", "mc") and (not key.startswith("config.")),
                    self.store.iterkeys()
                )

        for key in keys:
            del self.store[key]

    def get(self, key):
        '''
        get value for special key
        '''
        return self.store[key]

    def set(self, key, value):
        '''
        set value for special key
        '''
        self.store[key] = value

context = Context()

class SystemStatus(object):
    @staticmethod
    def cache_server_status():
        if "cache_server_status" in context:
            return context["cache_server_status"]

    @staticmethod
    def set_database_server_status(status):
        app_log.debug("set database server status to %s" % status)
        context["database_server_status"] = status

    @staticmethod
    def set_cache_server_status(status):
        app_log.debug("set cache server status to %s" % status)
        context["cache_server_status"] = status

    @staticmethod
    def cache_server_down():
        if "cache_server_status" in context:
            status = context["cache_server_status"]
            return status == constant.CACHE_SERVER_DOWN

    @staticmethod
    def cache_server_up():
        if "cache_server_status" in context:
            status = context["cache_server_status"]
            return status == constant.CACHE_SERVER_UP

    @staticmethod
    def database_server_status():
        if "database_server_status" in context:
            return context["database_server_status"]

def cache_client():
    if "cache" in localstore:
        return localstore.get("cache")
    else:
        from connproxy import get_proxy_mc
        cache = get_proxy_mc()
        localstore.save("cache", cache)
        return cache

def remove_cache_client():
    if "cache" in localstore:
        localstore.delete("cache")

def append_token(token, tokens):
    '''
    append token to token_list
    '''
    token_list = list(tokens)
    token_list.append(token)
    return tuple(token_list)

def remove_token(token, orgi_token):
    '''
    remove special token from token_list
    '''
    token_list = list(orgi_token)
    index = token_list.index(token)
    if index > -1:
        token_list.pop(index)
    return tuple(token_list)

class Session(object):
    def __init__(self, user, handler):
        self._user = user
        self._handler = weakref.ref(handler)
        self._token = self.get_token()
        self.build_session()
        self.set_auth_header()

    @property
    def user(self):
        return self._user

    @user.setter
    def user(self, userinfo):
        self._user = userinfo

    def build_session(self):
        cache = cache_client()
        queryid = str(self._user['_id']).encode("utf-8")
        user_token_key = "%s.token" % queryid
        token_num_key = "%s.token_num" % queryid
        token_userid = "%s.userid" % str(self._token)
        self._user["token"] = self._token
        submit_data = {
                        token_userid: str(self._user['_id']),
                        user_token_key: (self._token, ),
                        token_num_key: 1,
                        queryid: self._user
                        }
        cache.set_multi(submit_data, settings["token_duration"])
        context[self._token] = self

    def set_auth_header(self):
        handler = self._handler()
        if handler:
            handler.set_header(settings["token_name"], self._token)

    def get_token(self):
        factor = "%s_%s_%d" % (
                    repr(self._user['username']),
                    repr(self._user['_id']),
                    self._user['roles_id'])

        return utils.build_token(factor)

    def update(self):
        cache_client().set(self._token, self._user, settings["token_duration"])

    @staticmethod
    def create_session(user, handler):
        return Session(user, handler)

    @staticmethod
    def get_session(handler):
        token_value = handler.get_token()
        if token_value:
            token_userid = "%s.userid" % token_value
            queryid = cache_client().get(token_userid)
            if queryid:
                cached_user = cache_client().get(queryid)
                if not cached_user:
                    del context[token_value]
                    return
                if token_value in context:
                    session = context[token_value]
                    #session.roles = cached_user["roles"]
                    session.user = cached_user
                    session.update()
                    return session
                else:
                    return Session(cached_user, handler)

    @staticmethod
    def logout(handler):
        token = handler.get_token()
        if token not in context:
            return

        del context[token]
        token_userid = "%s.userid" % token
        userid = cache_client().get(token_userid)
        if not userid:
            return
        userid = userid.encode("utf-8")
        token_num_key = "%s.token_num" % userid
        user_token_key = "%s.token" % userid

        cache_client().delete_multi([token, token_userid, token_num_key, user_token_key])

class EventHub(object):
    __metaclass__ = utils.Singleton

    def __init__(self):
        self.evtpool = defaultdict(set)

    def emit_model_event(self, evtname, evtsrc, *data, **kwargs):
        loop = IOLoop.instance()
        if "force" in kwargs or utils.is_dirty(evtsrc):
            src = utils.copy_model(evtsrc)
            if isinstance(evtname, (list, tuple)):
                for evt in evtname:
                    loop.add_callback(self.emit, evt, src, *data)
            else:
                loop.add_callback(self.emit, evtname, src, *data)

    def emit_in_loop(self, evtname, evtsrc, *data, **kwargs):
        loop = IOLoop.instance()
        src = copy.deepcopy(evtsrc)
        loop.add_callback(self.emit, evtname, src, *data, **kwargs)

    def emit_system_notify(self, evtname, evtsrc):
        loop = IOLoop.instance()
        src = copy.deepcopy(evtsrc)
        loop.add_callback(self.emit, evtname, src)

    def emit(self, evtname, evtsrc, *data):
        callbacks = self.evtpool[evtname]
        for callback in callbacks:
            try:
                callback(evtsrc, *data)
            except:
                app_log.exception("call callback error")

    def hook(self, evtname, callback):
        self.evtpool[evtname].add(callback)

    def unhook(self, evtname, callback):
        callbacks = self.evtpool[evtname]
        if callback in callbacks:
            callbacks.remove(callback)

EVENTBUS = EventHub()

class Application(object):
    def __init__(self):
        from tornado.options import options
        self._options = options
        self._settings = settings
        self._beforecallback = None
        self._shutdown_callback = []
        self._app = None

    def call_shutdown_callback(self):
        for callback in self._shutdown_callback:
            callback()

    def init_settings(self):
        import tornado.options
        tornado.options.parse_command_line()
        self._settings["debug"] = self._options.debug
        self._settings['module'] = self._options.module
        if not self._settings['module']:
            print("the module parameter is required.")
            exit(0)
        else:
            context['module'] = self._settings['module']
        if self._settings["debug"]:
            self._settings["autoreload"] = True
            self.install_autoreload_hook()

        if not self._options.debug:
            args = sys.argv
            args.append("--log_file_prefix=%s" % settings['logfile'])
            tornado.options.parse_command_line(args)

    @property
    def options(self):
        return self._options

    @property
    def handlers(self):
        from urls import handlers
        return handlers

    @property
    def settings(self):
        return self._settings

    def get_app(self):
        self._beforecallback(self)
        self.init_settings()
        self.install_event_hooks()
        self.install_middleware()
        self.install_rbac()
        self.install_message_backend()
        context['dbconn'] = motor.motor_tornado.MotorClient('mongodb://%s' % mongodbConf['host'])
        # 6.16 add 
        from tornado.web import Application
        return Application(self.handlers, **self._settings)

    def install_middleware(self):
        from config import MIDDLEWARE_CLASSES
        context["middleware"] = set()
        for name in MIDDLEWARE_CLASSES:
            module = utils.module_resolver(name)
            if module:
                context["middleware"].add(module())
                app_log.debug("Middleware [%s] register ok" % name)
            else:
                app_log.error("Middleware [%s] cannot be resolved" % name)

    def install_event_hooks(self):
        from config import EVENT_HOOKS
        for hook_cls in EVENT_HOOKS:
            hook = utils.module_resolver(hook_cls)
            if hook:
                hook.install()
            else:
                app_log.error("Event Hook %s cannot be resolved" % hook_cls)

    def install_rbac(self):
        rbac_dict = utils.load_rbacfile()
        context["rbac"] = rbac_dict
        app_log.debug("RBAC module register ok")

    def install_message_backend(self):
        def shutdown_message_backend():
            context.get("message_backend").close()
            del context["message_backend"]
            app_log.debug("message backend closed!")
        try:
            import config
            backend_cls = utils.module_resolver(config.MESSAGE_BACKEND)
            context["message_backend"] = backend_cls(config)
            connection_future = context.get("message_backend").create_connection()
            IOLoop.instance().add_future(connection_future, lambda future: future.result())
            self._shutdown_callback.append(shutdown_message_backend)
            app_log.debug("%s install ok" % config.MESSAGE_BACKEND)
        except:
            pass

    def _sig_handler(self, sig, frame):
        self.call_shutdown_callback()
        import tornado.ioloop
        stop_server = tornado.ioloop.IOLoop.instance().stop
        tornado.ioloop.IOLoop.instance().add_callback_from_signal(stop_server)
        app_log.info("Shutdown Server...")

    def reg_shutdown_hook(self, shutdown_handler):
        import signal
        self._shutdown_callback.append(shutdown_handler)
        signal.signal(signal.SIGTERM, self._sig_handler)
        signal.signal(signal.SIGINT, self._sig_handler)

    def before(self, before_callback):
        self._beforecallback = before_callback
        return self

    def install_autoreload_hook(self):
        if self._options.debug:
            from tornado.autoreload import add_reload_hook
            add_reload_hook(self.call_shutdown_callback)

    def start(self):
        app = self.get_app()
        import tornado.httpserver
        http_server = tornado.httpserver.HTTPServer(app)
        http_server.listen(self._options.port, address=self._options.address)
        app_log.info("server listen on %s:%d" % (self._options.address, self._options.port))
        tornado.ioloop.IOLoop.instance().start()

class MiddleWare(object):
    def process_request(self, handler):
        pass

    def process_response(self, handler):
        pass

