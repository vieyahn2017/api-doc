#!/usr/bin/env python
#-*-coding:utf-8 -*-
# @author:yanghao
# @created:20170426
## Description: http_fetch

import json
import traceback
from tornado.gen import coroutine, Return
from tornado.log import app_log
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPError
from tornado import escape


class Fetcher(object):
    def __init__(self, host):
        self.host = host

    @coroutine
    def _fetch(self, url, method='get', body=None, is_log=True):
        fetch_url = "%s/%s" % (self.host, url)
        request = HTTPRequest(url=fetch_url, method=method.upper(), body=body)
        if is_log:
            app_log.info("fetch_%s at: %s" % (method, fetch_url))
        try:
            response = yield AsyncHTTPClient().fetch(request)
            response_body = escape.json_decode(response.body)
            code = response_body.get('code')
            rows = response_body.get('rows')
            if is_log:
                app_log.info(("receive_rows:" , rows, type(rows), "code: ", code, "msg: ", response_body.get("msg")))
            # app_log.debug("receive_rows:%s %s" % (rows, type(rows)))
            results = {
                "rows": rows,
                "msg": response_body.get("msg"),
                "code": code,
                "url": response.request.url
            }
        except HTTPError as e:
            app_log.error('{0}: {1}  Msg: {2}'.format(method.upper(), fetch_url, e))
            raise Return({"url": fetch_url, "code": -1, "msg": e})
        else:
            app_log.debug("{0}: {1}  Code: {2}  MSG: {3}".format(method.upper(), fetch_url, code, response_body.get('msg')))
            if is_log and body:
                app_log.info(escape.json_decode(body))
            raise Return(results)


    @coroutine
    def fetch_rows(self, url, is_log=False):
        results = yield self._fetch(url, is_log=is_log)
        raise Return(results)

    @coroutine
    def fetch_delete(self, url, is_log=False):
        results = yield self._fetch(url, 'delete', is_log=is_log)
        raise Return(results)

    @coroutine
    def fetch_post(self, url, body={}, is_log=False):
        results = yield self._fetch(url, 'post', body=json.dumps(body), is_log=is_log)
        if is_log:
            app_log.info(("the data of POST:", body))
        raise Return(results)

    @coroutine
    def fetch_put(self, url, body={}, is_log=False):
        results = yield self._fetch(url, 'put', body=json.dumps(body), is_log=is_log)
        if is_log:
            app_log.info(("the data of PUT:", body))
        raise Return(results)


LOCALHOST = '10.0.0.161'

CC_MODULES = {
    "Compute": (LOCALHOST, 30001),
    "Network": (LOCALHOST, 30002),
    "ApiModule": (LOCALHOST, 30003),
    "WebServices": (LOCALHOST, 30004)
}


def get_module_url(part, module):
    _url, _port = part[module]
    return "http://%s:%s/api/v1" %(_url, _port)


cc_compute_fetcher = Fetcher(get_module_url(CC_MODULES, "Compute"))
cc_network_fetcher = Fetcher(get_module_url(CC_MODULES, "Network"))
cc_api_fetcher = Fetcher(get_module_url(CC_MODULES, "ApiModule"))

# # use
# from handlers.fetcher import cc_compute_fetcher, cc_network_fetcher
