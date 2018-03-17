#!/usr/bin/env python
#-*-coding:utf-8 -*-
# @author:yanghao
# @created:20170712
## Description: export models.



from __future__ import absolute_import

from tornado.gen import coroutine
from tornado.log import app_log

from handlers import BaseProxyHandler, Route
from core import context, cache_client
from config import settings
from config import BASE_URL

import json


from handlers.fetcher import *


@Route("m")
class ApiSaveHandler(BaseProxyHandler):

    def get(self):
        base_url = BASE_URL

        test = [
                    'm/api/type',
                    'm/api/param',
                    'm/api',
               ]

        api =  [
                     'm/api/save',
                     'm/api/delete',
              ]

        route = {
                   "update_time": "2018-03-17",
                   "test": [base_url + "/api/v1/" + url for url in test],
                   "api": [base_url + "/api/v1/" + url for url in api]
                }

        self.write(route)


@Route("m/api/save")
class ApiSaveHandler(BaseProxyHandler):

    @coroutine
    def post(self):
        is_log = False
        body = json.loads(self.request.body)  #, encoding='utf-8')
        print body


@Route("m/api/delete")
class ApiDeleteHandler(BaseProxyHandler):

    @coroutine
    def post(self):
 
        is_log = False
        body = json.loads(self.request.body)  #, encoding='utf-8')
        print body




"""

<?php
/**
 * Created by PhpStorm.
 * User: danghongyang
 * Date: 13-12-26
 * Time: 下午11:41
 */
$href = $_POST["href"];

$content = json_decode($content, true);
$content = json_encode($content);

$filename = "../data/".$href.".json";

copy($filename, "../data/".$href."-".date("Y-m-d")."-".time().".json");

unlink($filename);


<?php
/**
 * Created by PhpStorm.
 * User: danghongyang
 * Date: 13-12-26
 * Time: 下午11:41
 */

$content = $_POST["content"];
$href = $_POST["href"];

$content = json_decode($content, true);
$content = json_encode($content);

$r = file_put_contents("../data/".$href.".json", $content);
$r = file_put_contents("../data/".$href."-".date("Y-m-d")."-".time().".json", $content);

"""

