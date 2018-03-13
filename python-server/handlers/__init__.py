#!/usr/bin/env python
#-*-coding:utf-8 -*-
#
#Author: tony - birdaccp at gmail.com
#Create by:2015-08-26 13:51:41
#Last modified:2017-05-26 17:13:32
#Filename:handlers.__init__.py
#Description:
from __future__ import absolute_import
from cStringIO import StringIO
import os
import re
import functools

import tornado.web
import tornado.httpclient
from tornado import httputil
from tornado.gen import coroutine
from tornado.web import asynchronous
from tornado.ioloop import IOLoop
from tornado.log import app_log

import utils
import config
import constant
from core import context, Session
from config import API_VERSION

class Route(object):
    urls = []

    def __call__(self, url, name=None):
        def _(cls):
            if url.startswith("/"):
                _url = r"%s" % url
            else:
                _url = r"/api/%s/%s" % (API_VERSION, url)
            self.urls.append(tornado.web.URLSpec(_url, cls, name=name))
            return cls
        return _
Route = Route()


class WireCallable(object):
    def __init__(self, callableobj, args, kwargs):
        self._callback = callableobj
        self._before = None
        self._after = None
        self._args = args
        self._kwargs = kwargs

    def __call__(self):
        if self._before:
            self._before()
        try:
            return self._callback(*self._args, **self._kwargs)
        except:
            raise
        finally:
            if self._after:
                self._after()

    def before_call(self, callback):
        self._before = callback
        return self

    def after_call(self, callback):
        self._after = callback
        return self


class BaseHandler(tornado.web.RequestHandler):

    def check_xsrf_cookie(self):
        return False

    def prepare(self):
        for middleware in context["middleware"]:
            middleware.process_request(self)

    def finish(self):
        for middleware in context["middleware"]:
            middleware.process_response(self)
        super(BaseHandler, self).finish()

    def getform(self):
        form_name = "__%sform__" % self.request.method.lower()
        assert hasattr(self, form_name), "%s not defined" % form_name
        form_cls = getattr(self, form_name)
        assert form_cls, "%s not be None" % form_name
        form = getattr(self, form_name)
        form_obj = form(self.request.arguments)
        if hasattr(form_obj, "uid") and self.current_user:
            form_obj.uid.data = self.current_user.id
        return form_obj

    def validate_input(self):
        form = self.getform()
        if not form.validate():
            raise ValueError(self.format_form_err(form))
        else:
            return form

    def format_form_err(self, form):
        errstr = []
        for field, err in form.errors.iteritems():
            errstr.append("[%s] %s" % (field, "".join(err)))
        return "".join(errstr)

    def write_error(self, status_code, **kwargs):
        exc_cls, exc_instance, trace = kwargs.get("exc_info")
        if not hasattr(exc_instance, "status_code"):
            exc_instance.status_code=500
        status_code = exc_instance.status_code
        if status_code not in httputil.responses:
            status_code = 500

        if len(exc_instance.args) == 2:
            _, errmsg = exc_instance.args
        else:
            if hasattr(exc_instance, "message"):
                errmsg = exc_instance.message
                if not errmsg and hasattr(exc_instance, "log_message"):
                    errmsg = exc_instance.log_message
            else:
                errmsg = exc_instance.log_message

        self.write(dict(msg=errmsg, code=status_code))
        self.set_status(status_code)

    def write_user_error(self, msg="", code=500):
        self.set_status(code)
        self.write(dict(msg=msg))

    def get_header(self, key):
        value = self.request.headers.get(key)
        return value if value and value != "null" else None

    def get_token(self):
        token_name = self.application.settings["token_name"]
        return self.get_header(token_name)

    def is_superuser(self):
        return self.current_user.is_superuser

    def has_roles(*roles):
        return True

    def has_role(self, role):
        return role in self.current_user.roles

    def has_perm(self, perm_names):
        path = self.request.path.split("/")[2]

        if isinstance(perm_names, (str, unicode)):
            perm_names = [perm_names]

        for rightinfo in self.current_user.rights:
            # [{"action":"CRUD", "url":"class"}]
            if path in rightinfo:
                actions = rightinfo["action"]
                for perm in perm_names:
                    if actions.find(perm) > -1:
                        return True
            return False
        else:
            return False

    def get_session(self):
        return Session.get_session(self)

    def get_current_user(self):
        session = self.get_session()
        if session:
            return session.user
            # return User.get(session)

    def is_login(self):
        return self.get_session() != None

    def need_login(self):
        self.write_user_error(code=403, msg="please relogin with your cred")

    def get_page_query(self, form):
        form_params = {
                    "curpage": form.curpage.data,
                    "perpage": form.perpage.data,
                    "totalpage": form.totalpage.data,
                    "keywords": form.keywords.data
                }
        return form_params

    def write_rows(self, code=1, msg='', form=None, rows=()):
        response = {"msg": msg, "code": code, "rows": rows}
        if form:
            response.update(self.get_page_query(form))
        self.write(response)

    def write_response(self, **kwargs):
        # kwargs.update(dict(code=200))
        self.write(kwargs)

    @property
    def executor(self):
        return self.application.settings["executor"]

    def async(self, callableobj, *args, **kwargs):
        wired_callback = WireCallable(callableobj, args, kwargs)
        wired_callback.before_call(self.before).after_call(self.after)
        future = self.executor.submit(wired_callback)
        return future

    def before(self):
        from core import cache_client
        return cache_client()

    def after(self):
        from core import remove_cache_client
        remove_cache_client()


class CrudAction(BaseHandler):
    __model__ = None

    def _getmodel(self):
        assert self.__model__ is not None, "__model__ not defined yet"
        return self.__model__

    def get(self, pid=None):
        form = self.getform()
        if form.validate():
            entry_model = self._getmodel()
            if not pid:
                if form.m.data == "f":
                    entry_list = entry_model.filter_by(form)
                else:
                    entry_list = entry_model.all(False, form)
                self.write_rows(form, entry_list)
            else:
                entry_detail = entry_model.get(int(pid), self)
                if entry_detail:
                    self.write_rows(rows=entry_detail)
                else:
                    self.write_user_error("object not found", 404)
        else:
            self.write_user_error(msg=self.format_form_err(form))

    @coroutine
    def post(self):
        form = self.getform()
        if form.validate():
            if hasattr(form, "id"):
                form.id.data = 0
            entry_model = self._getmodel()
            yield self.async(entry_model.save, form, self)
            self.write_response()
        else:
            self.write_user_error(msg=self.format_form_err(form))

    @coroutine
    def put(self, pid):
        form = self.getform()
        if form.validate():
            form.id.data = int(pid)
            entry_model = self._getmodel()
            yield self.async(entry_model.update, form, self)
            self.write_response()
        else:
            self.write_user_error(msg=self.format_form_err(form))

    @coroutine
    def delete(self, pid):
        entry_model = self._getmodel()
        yield self.async(entry_model.delete, int(pid), context=self)
        self.write_response()


from .fetcher import Fetcher, get_microcloud_url

class BaseProxyCCHandler(BaseHandler):
    """yanghao 20170616 from handlers"""

    def o__init__(self, **kwargs):
        """9.6 get_microcloud_url 
        这样设置5个fetcher属性应该是可行的
        不过貌似super的用法有问题，报错如下： 先暂停吧
        TypeError: __init__() takes exactly 1 argument (3 given)
        """
        self.webservices_fetcher =  Fetcher(get_microcloud_url(self, 'webservices'))
        self.compute_fetcher = Fetcher(get_microcloud_url(self, "compute"))
        self.network_fetcher = Fetcher(get_microcloud_url(self, "network"))
        self.storage_fetcher = Fetcher(get_microcloud_url(self, "storage"))
        self.images_fetcher = Fetcher(get_microcloud_url(self, "images"))
        super(BaseProxyCCHandler, self).__init__(**kwargs)

    # @property
    # def db(self):
    #     return context['dbconn'].compute

    def set_default_headers_0(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header("Access-Control-Allow-Headers", 'Content-Type')
        self.set_header('Access-Control-Allow-Methods', 'PUT, DELETE, POST, GET')
        self.set_header('Access-Control-Allow-Credentials',  "true")

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header(
            "Access-Control-Expose-Headers",
            'Content-Type, X-Xsrf-Token,x-xss-protection,'
            'content-length,X-Requested-With, content-length,X-Requested-With, verify_key'
        )
        self.set_header(
            "Access-Control-Allow-Headers",
            'Content-Type, X-Xsrf-Token,x-xss-protection,'
            'content-length,X-Requested-With, content-length,X-Requested-With, verify_key'
        )
        self.set_header("Access-Control-Allow-Methods", "PUT, DELETE, POST, GET, OPTIONS")
        self.set_header("Access-Control-Allow-Credentials", "true")

    def options(self, *args, **kwargs):
        self.set_status(204)
        self.finish()


    def write_ok(self, msg="success"):
        self.write_rows(code=1, msg=msg)
        # self.write({"code": 1, "msg": msg})

    def write_failure(self, msg='failed'):
        self.write_rows(code=-1, msg=msg)
        # self.write({"code": -1, "msg": msg})

    def write_libc_ret(self, ret):
        """ using for libc , 2017.7.21"""
        code = 1 if ret == 0 else -1
        self.write_rows(code=code, msg="the lsp_err_e code= {0}".format(ret))

    def write_libc_rets(self, rets):
        """ using for libc , rets~=[{"ip": ip, "ret": ret}] 2017.7.21"""
        code = -1 if False in map(lambda x: x["ret"] == 0, rets) else 1
        self.write_rows(code=code, msg="the lsp_err_e codes: {0}".format(rets))

    def parse_fetch(self, item):
        if item.get('code') in [404, 500]: # 404, 500
            #self.write_error(status_code=item.get('code'), exc_info=item)
            # item = {'url': 'http://10.0.0.252:30002/api/v1/compute/az', 'msg': '[Errno 111] Connection refused', 'code': 404}
            self.write(item)
            self.finish()
            # 目前 RuntimeError: Cannot write() after finish()
            return []
        if item.get("rows"):
            return item.get("rows")


    #@coroutine #有这个就会因为write而RuntimeError: Cannot write() after finish()
    @asynchronous
    def unblock(self, func, *args, **kwargs):
        """实现了传值rows， 不过还是有很大局限性, *args, **kwargs 是func的参数"""
        def _callback(future, rows, msg, code, callback):
            # future.set_result({"rows"=rows, "msg"=msg, "code"=code})
            # app_log.info(future.result()) # None
            if callback is not None:
                callback()
            self.write_rows(rows=rows, msg=msg, code=code)
            self.finish()
            #callback_done(rows)  # add a param: callback_done ?

        app_log.warn(("run in executor for unblocking:", self._request_summary()))
        rows = kwargs.get('rows', [])
        msg = kwargs.get('msg', '')
        code = kwargs.get('code', 1)
        callback = kwargs.get('callback', None)

        self.executor.submit(
                functools.partial(func, *args, **kwargs)
            ).add_done_callback(
                lambda future: IOLoop.instance().add_callback(
                    functools.partial(_callback, future, rows, msg, code, callback))
            )


@Route(r"/")
class IndexHandler(BaseHandler):
    def get(self):
        print self.application.handlers
        path = []
        for x in self.application.handlers[0][1]:
            path.append(x._path)
        self.write_rows(rows=path)



def unblock_wraps(f):
    @asynchronous
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        self = args[0]
 
        def callback(future):
            app_log.info(future.result())
            self.write_ok()
            self.finish()
 
        EXECUTOR = context["executor"]
        EXECUTOR.submit(
            functools.partial(f, *args, **kwargs)
        ).add_done_callback(
            lambda future: IOLoop.instance().add_callback(
                functools.partial(callback, future))
        )
 
    return wrapper


from . import admin
from handlers.Api import *
