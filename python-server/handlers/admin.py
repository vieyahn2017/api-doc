#!/usr/bin/env python
# -*-coding:utf-8 -*-
import json
from __future__ import absolute_import
from tornado.gen import coroutine
from tornado.log import app_log
from core import context, Session
from . import Route, BaseHandler
from .model_admin import user_model


@Route(r"/api/register")
class RegisterHandler(BaseHandler):

    def get(self):
        Session.logout(self)
        self.write_response()


@Route(r'/api/login')
class LoginHandler(BaseHandler):

    @coroutine
    def post(self):
        body = json.loads(self.request.body)  #, encoding='utf-8')
        # assert "username" in body, "missing argument <username> in body"
        # assert "password" in body, "missing argument <password>  in body"
        # username = body.get('username')
        # password = body.get('password')

        # username, password = "g283xxx", "123456"
        # session = Session.get_session(self)
        # session = self.get_session()

        # user = CloudUser(self)
        # session = Session.create_session(user ,self)
        # print session.get_token()
        # print session, user
        # from models import User
        # user = User.login(username, password)
        # if user:
        #     user["queryid"] = form.username.data
        #     Session.create_session(user, self)
        #     Session.get_session
        #     self.write_response(
        #             rights=user.rights,
        #             username=user.username,
        #             userphoto=user.userphoto,
        #             roles=user.roles
        #             )
        # else:
        #     self.write_user_error(code=404, msg="user information error")


@Route(r"/api/logout")
class LogoutHandler(BaseHandler):

    def get(self):
        Session.logout(self)
        self.write_response()

