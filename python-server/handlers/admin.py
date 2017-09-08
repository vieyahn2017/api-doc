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

import tornado.web
import tornado.httpclient
from tornado.gen import coroutine
from tornado import httputil
from tornado.log import app_log

import utils
import config
import constant
from core import context, Session
from config import API_VERSION


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
        # body = json.loads(self.request.body)  #, encoding='utf-8')
        # assert "username" in body, "missing argument <username> in body"
        # assert "password" in body, "missing argument <password>  in body"
        # username = body.get('username')
        # password = body.get('password')

        username, password = "g283xxx", "123456"
        # session = Session.get_session(self)
        # session = self.get_session()

        user = CloudUser(self)
        session = Session.create_session(user ,self)
        print session.get_token()
        print session, user
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


@Route(r"/api/uploadstream")
@tornado.web.stream_request_body
class UploadStreamHandler(BaseHandler):

    def prepare(self):
        super(UploadStreamHandler, self).prepare()
        content_dispostion = self.get_header("Content-Disposition")
        content_length = self.get_header("Content-Length")
        content_type = self.get_header("Content-Type")
        if all([content_dispostion, content_length, content_type]):
            find_filename = re.compile('name="(.*)"')
            search_filename = find_filename.search(content_dispostion)
            if search_filename:
                name, ext = os.path.splitext(search_filename.groups()[0])
                self.tempfilename = "%s%s" % (utils.get_tempname(), ext)
                self.localfile = config.UPLOAD_PATH % self.tempfilename
                self.output = open(self.localfile, "wb")
        else:
            raise ValueError("param error")

    def data_received(self, data):
        self.output.write(data)

    def post(self):
        self.output.close()
        if utils.is_image(self.localfile):
            download_url = config.UPLOAD_URL % self.tempfilename
            self.write_response(err="", msg=download_url)
        else:
            app_log.warn("%s no image file" % self.localfile)
            self.write_user_error("image format error")


@Route(r"/api/uploadavatar")
@tornado.web.stream_request_body
class UploadAvatarHandler(UploadStreamHandler):
    def prepare(self):
        super(UploadAvatarHandler, self).prepare()
        self.tempfilename = "%s" % utils.get_tempname()
        self.localfile = config.UPLOAD_PATH % self.tempfilename
        self.output = open(self.localfile, "wb")

    def post(self):
        self.output.close()
        ext = utils.is_image(self.localfile)
        if ext:
            self.tempfilename = "%s.%s" % (self.tempfilename, ext)
            final_filename = config.UPLOAD_PATH % self.tempfilename
            utils.move_file(self.localfile, final_filename)
            download_url = config.UPLOAD_URL % self.tempfilename
            self.write_response(status=1, url=download_url)
        else:
            app_log.warn("%s no image file" % self.localfile)
            utils.rm_file(self.tempfilename)
            self.write_user_error(status=-1, msg="image format error")


@Route(r"/api/uploadurl")
class UploadUrl(BaseHandler):

    def write_img(self, response):
        if response.code == 200:
            ext = utils.is_image(stream=response.body)
            if not ext:
                return
            tempname = "%s.%s" % (utils.get_tempname(), ext)
            img_path = config.UPLOAD_PATH % tempname
            download_url = config.UPLOAD_URL % tempname
            self.files.append(download_url)
            with open(img_path, "wb") as img:
                img.write(response.body)

    @coroutine
    def post(self):
        url = self.get_argument("urls")
        self.files = []
        if url:
            url = url.split("|")
            if len(url) > 10:
                self.write_user_error(msg="too many url")
            else:
                httpclient = utils.async_client()
                imgs = yield [httpclient.fetch(img_url) for img_url in url]
                for img in imgs:
                    self.write_img(img)
                url_strings = "|".join(self.files)
                self.write(url_strings)


@Route(r"/api/upload")
@tornado.web.stream_request_body
class UploadHandler(BaseHandler):

    def prepare(self):
        super(UploadHandler, self).prepare()
        print self.request.headers
        self.mimetype = self.request.headers.get("Content-Type")
        if self.mimetype is None:
            raise Exception(500, "params error")
        self.boundary = "--%s" % (self.mimetype[self.mimetype.find("boundary")+9:])
        self.state = constant.PARSE_READY
        self.output = None
        self.find_filename = re.compile('filename="(.*)"')
        self.find_mimetype = re.compile('Content-Type: (.*)')
        self.find_field = re.compile('name="(.*)"')
        self.files = []

    def post(self):
        download_urls = [config.UPLOAD_URL % fname for fname in self.files]
        self.write_response(rows=download_urls)

    def valid_filename(self, ext):
        ext = ext.lower()
        if ext not in config.VALID_FILE_EXT:
            raise Exception(500, "invalid fiename")

    def createfile(self, filename):
        import tempfile
        import os
        filename, ext = os.path.splitext(filename)
        self.valid_filename(ext)
        tempfilename = "%s%s" % (next(tempfile._get_candidate_names()), ext)
        self.files.append(tempfilename)
        filename = config.UPLOAD_PATH % tempfilename
        self.output = open(filename, "wb")

    def data_received(self, data):
        buff = data.split(self.boundary)
        for index, part in enumerate(buff):
            if part:
                if part == "--\r\n":
                    break
                elif self.state == constant.PARSE_FILE_PENDING:
                    if len(buff) > 1:
                        self.output.write(part[:-2])
                        self.output.close()
                        self.state = constant.PARSE_READY
                    else:
                        self.output.write(part)

                elif self.state == constant.PARSE_READY:
                    stream = StringIO(part)
                    stream.readline()
                    form_data_type_line = stream.readline()
                    if form_data_type_line.find("filename") > -1:
                        filename = re.search(self.find_filename, form_data_type_line).groups()[0].strip()
                        self.createfile(filename)
                        content_type_line = stream.readline()
                        mimetype = re.search(self.find_mimetype, content_type_line).groups()[0]
                        app_log.debug("%s with %s" % (filename, mimetype.strip()))
                        stream.readline()
                        body = stream.read()
                        if len(buff) > index + 1:
                            self.output.write(body[:-2])
                            self.state = constant.PARSE_READY
                        else:
                            self.output.write(body)
                            self.state = constant.PARSE_FILE_PENDING
                    else:
                        stream.readline()
                        form_name = re.search(self.find_field, form_data_type_line).groups()[0]
                        form_value = stream.readline()
                        self.state = constant.PARSE_READY
                        app_log.debug("%s=%s" % (form_name.strip(), form_value.strip()))
