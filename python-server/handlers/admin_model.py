#!/usr/bin/env python
#-*-coding:utf-8 -*-
# @author:yanghao 
# @created:20170524
## Description: model of  __init__.py  [@Route(r'/api/login') , etc...]

import time

from tornado.gen import coroutine, Return
from tornado.log import app_log

from connproxy import StoreContext
from models import BaseModel


class SmsModel(BaseModel):
    @coroutine
    def get_one_sms(self):
        res = yield self.get("SELECT account, password, url, content FROM sys_sms_config WHERE flag='1' LIMIT 1")
        raise Return(res)
sms_model = SmsModel()

class UserModel(BaseModel):

    @coroutine
    def check_user(self, user_name, password_add_token=None, is_log=False):
        """检查username是否存在，如果username存在，检查password是否正确"""
        if password_add_token is None:
            result = yield model.get("""SELECT _id  FROM webservice_user WHERE username=%s LIMIT 1;""",  (user_name,))
        else:
            result = yield model.get("""SELECT _id  FROM webservice_user WHERE username=%s AND password=%s LIMIT 1;
                                                 """,  (user_name, password_add_token))
        if is_log:
            app_log.info(result)
        raise Return(result)

    @coroutine
    def add_user(self, email, phone, password, is_log=False):
        """ 新注册用户，必须phone，email，password三者全部填写，初始暂时把username=email，后面提供修改的接口 """
        email_token = 'WDASA#WSCC#544345'
        reg_timestamp = int(time.time())
        with StoreContext() as store:
            ctx = yield store.begin()
            try:
                yield ctx.execute("""INSERT INTO webservice_user (username, email, phone, password, email_token, reg_date, flag) 
                                               VALUES (%s,%s,%s,%s,%s,%s, 0)""", 
                                               (email, email, phone, password, email_token, reg_timestamp))
                yield ctx.commit()
                flag = True
            except:
                yield ctx.rollback()
                flag = False
        if is_log:
            app_log.info(("add_user success ?", flag, email, phone))
        raise Return(flag)

    @coroutine
    def activate_user(self, user_id, is_log=False):
        """ activate user, set flag = 1   """
        with StoreContext() as store:
            ctx = yield store.begin()
            try:
                yield ctx.execute("UPDATE sys_user SET email_token='', flag='1' WHERE _id=%s;", (user_id))
                yield ctx.commit()
                flag = True
            except:
                yield ctx.rollback()
                flag = False
        if is_log:
            app_log.info(("activate_user success ? ", flag, user_id))
        raise Return(flag)

    @coroutine
    def update_password(self, user_id, old_password, new_password, is_log=True):
        res = yield self.get("SELECT _id FROM sys_user WHERE _id =3 AND password=%s", (user_id, old_password))
        err_code = 0
        if res:
            with StoreContext() as store:
                ctx = yield store.begin()
                try:
                    yield ctx.execute("UPDATE sys_user SET password=%s WHERE _id=%s", (new_password, user_id))
                    yield ctx.commit()
                    err_code = 1
                except Exception as e:
                    err_code = -1
                    app_log.error(("Update password failed! ", user_id, e))
                    yield ctx.rollback()
        if is_log:
            app_log.info(("Update password success ? ", err_code, user_id))
        raise Return(err_code)

    @coroutine
    def update_email(self, user_id, email, is_log=True):
        with StoreContext() as store:
            ctx = yield store.begin()
            try:
                yield ctx.execute("UPDATE sys_user SET email=%s WHERE _id=%s;", (email, user_id))
                yield ctx.commit()
                flag = True
            except Exception as e:
                app_log.error(("Update email failed! ", user_id, e))
                yield ctx.rollback()
                flag = False
        if is_log:
            app_log.info(("Update email success ? ", flag, user_id, email))
        raise Return(flag)

    @coroutine
    def update_phone(self, user_id, phone, is_log=True):
        with StoreContext() as store:
            ctx = yield store.begin()
            try:
                yield ctx.execute("UPDATE sys_user SET phone=%s WHERE _id=%s;", (phone, user_id))
                yield ctx.commit()
                flag = True
            except Exception as e:
                app_log.error(("update_phone failed! ", user_id, e))
                yield ctx.rollback()
                flag = False
        if is_log:
            app_log.info(("Update phone success? ", flag, user_id, phone))
        raise Return(flag)

    @coroutine
    def update_username(self, user_id, username, is_log=True):
        with StoreContext() as store:
            ctx = yield store.begin()
            try:
                yield ctx.execute("UPDATE sys_user SET username=%s WHERE _id=%s;", (username, user_id))
                yield ctx.commit()
                flag = True
            except Exception as e:
                app_log.error(("Update user name failed! ", user_id, e))
                yield ctx.rollback()
                flag = False
        if is_log:
            app_log.info(("Update user name success? ", flag, user_id, username))
        raise Return(flag)

    @coroutine
    def update_user_every_login(self, user_id, *args, **kwargs):
        """ 每次登陆（或者别的操作）对user的信息的修改,  包括登陆次数，上次登陆时间等 """
        pass

    @coroutine
    def update_user(self, user_id, key, vaule, is_log=False):
        """ key = password, email, phone, username 
           # 这些update本来想省事，合成一个接口
           Unknown column ''phone'' in 'field list' . 报错，update后面的表列字段不支持这样%s
        """
        if key not in ["password", "email", "phone", "username"]:
            app_log.error(("update_user error, the key is not supported ? ", key))
            raise Return(False)
        with StoreContext() as store:
            ctx = yield store.begin()
            try:
                yield ctx.execute("UPDATE webservice_user SET %s=%s WHERE _id=%s;", (key, vaule, user_id))
                yield ctx.commit()
                flag = True
            except Exception as e:
                app_log.error(("update_user failed! ", user_id, key, vaule, e))
                yield ctx.rollback()
                flag = False
        if is_log:
            app_log.info(("update_user success ? ", flag, user_id, key, vaule))
        raise Return(flag)

user_model = UserModel()

