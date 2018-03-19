#!/usr/bin/env python
#-*-coding:utf-8 -*-
# @author: yanghao 
# @ date 20170606
## Description: cc_web.py


from __future__ import absolute_import

from tornado.gen import coroutine, Return
from tornado.ioloop import IOLoop
from tornado.log import app_log

from handlers import BaseProxyHandler, Route
from core import context, cache_client
from config import settings

import json
from bson import ObjectId

from .model import CategoryModel, ParamModel, APiModel


class BaseMongoHandler(BaseProxyHandler):

    @property
    def db(self):
        return context['dbconn']

    def write_models(self, models):
        """write json, add key[datas] to the obj list"""
        try:
            objects_list = [obj.to_primitive() for obj in models]
            self.write_rows(rows=objects_list)
        except:
            self.write_failure(msg="write_models error")

    def write_model(self, model):
        """write model"""
        try:
            self.write_rows(rows=model.to_primitive())
        except:
            self.write_failure(msg="write_model error")

false = False
true = True


@Route("m/api/authenticated")
class APiModelCheckExistHandler(BaseMongoHandler):

    @coroutine
    def get(self):
        self.write_failure()


@Route("m/api/category")
class CategoryModelTestHandler(BaseMongoHandler):

    @coroutine
    def get(self):
        """ by href"""
        objects = []
        href = self.get_argument('href', None)
        if href:
            obj = yield CategoryModel.find_one(self.db, {"href": href})
            objects.append(obj)
        else:
            cursor = CategoryModel.get_cursor(self.db, {})
            objects = yield CategoryModel.find(cursor)

        if objects:
            self.write_models(objects)
        else:
            self.write_ok(msg="no result")


@Route("m/api/param")
class ParamModelTestHandler(BaseMongoHandler):

    @coroutine
    def get(self):
        objects = []
        _id = self.get_argument('id', None)
        if _id:
            obj = yield ParamModel.find_one(self.db, {"_id": ObjectId(_id)})
            objects.append(obj)
        else:
            cursor = ParamModel.get_cursor(self.db, {})
            objects = yield ParamModel.find(cursor)

        if objects:
            self.write_models(objects)
        else:
            self.write_ok(msg="no result")


def cmp_by_object_id(x, y):
    """ using for mongodb - sort"""
    if x.get("_id") < y.get("_id"):
        return -1
    else:
        return 1


def cmp_by_object_id_desc(x, y):
    """ using for mongodb - sort"""
    if x.get("_id") > y.get("_id"):
        return -1
    else:
        return 1


@Route("m/api/exist")
class APiModelCheckExistHandler(BaseMongoHandler):

    @coroutine
    def get(self):
        name = self.get_argument('name')
        href = self.get_argument('href', None)
        query = {"category_href": href, "name": name} if href else {"name": name}
        cursor = APiModel.get_cursor(self.db, query)
        objects = yield APiModel.find(cursor)
        if len(objects) > 0:
            self.write_ok()
        else:
            self.write_failure()


@Route("m/api")
class APiModelTestHandler(BaseMongoHandler):

    @coroutine
    def parse_param_one(self, item):
        paramsIdList = item.pop("paramsIdList")
        paramsList = []
        for id_param in paramsIdList:
            query_param = {"_id": id_param}
            # cursor_param = ParamModel.get_cursor(self.db, query_param)
            # object_param = yield ParamModel.find(cursor_param)
            object_param = yield ParamModel.find_one(self.db, query_param)
            if object_param:
                paramsList.append(object_param.to_primitive())

        responseIdList = item.pop("responseIdList")
        responseList = []
        for id_param in responseIdList:
            query_param = {"_id" : id_param}
            object_param = yield ParamModel.find_one(self.db, query_param)
            if object_param:
                responseList.append(object_param.to_primitive())

        item["paramsList"] = paramsList
        item["responseList"] = responseList
        raise Return(item)

    @coroutine
    def get(self):
        objects_list = []
        href = self.get_argument('href', None)
        desc = self.get_argument('desc', False)
        query = {"category_href": href} if href else {}
        cursor = APiModel.get_cursor(self.db, query)
        objects = yield APiModel.find(cursor)
        for obj in objects:
            item = yield self.parse_param_one(obj.to_primitive())
            objects_list.append(item)
        if desc:
            self.write_rows(rows=sorted(objects_list, cmp_by_object_id_desc))
        else:
            self.write_rows(rows=sorted(objects_list, cmp_by_object_id))



