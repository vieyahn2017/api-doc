#!/usr/bin/env python
#-*-coding:utf-8 -*-
# @author:yanghao
# @created:20170712
## Description: export models.



from __future__ import absolute_import

from tornado.gen import coroutine
from tornado.log import app_log

from handlers import BaseProxyCCHandler, Route
from core import context, cache_client
from config import settings

import json


from handlers.fetcher import *


@Route("cc")
class CCApiSaveHandler(BaseProxyCCHandler):


    def get(self):
        base_url = "http://10.0.0.161:30003"

        test = [
                    'cc/api/type',
                    'cc/api/param',
                    'cc/api',
               ]
        api =  [ 
                     'cc/api/save',
                     'cc/api/delete',
              ]


        route = {
                   "update_time": "2017-07-13",
                   "test": ["/api/v1/" + url for url in test],  
                   "api": ["/api/v1/" + url for url in api] 
                }

        self.write(route)


@Route("cc/api/save")
class CCApiSaveHandler(BaseProxyCCHandler):

    @coroutine
    def post(self):
 
        is_log = False
        body = json.loads(self.request.body)  #, encoding='utf-8')
        # yield cc_api_fetcher.fetch_post('cc/test/interface', body={"rows": [], "url": 'cc/xd/uuid'}, is_log=is_log)
        print body



@Route("cc/api/delete")
class CCApiDeleteHandler(BaseProxyCCHandler):


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

