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

from .mg_model import CategoryModel, ParamModel, APiModel


class BaseMongoHandler(BaseProxyHandler):

    @property
    def db(self):
        return context['dbconn'].apidocs

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

    @coroutine
    def post(self):
        """ add & edit"""
        body = json.loads(self.request.body)
        name = body["name"]
        href = body["href"]
        description = body["description"]
        _id = body.get("_id", None)
        app_log.info((body, _id))
        if _id:
            yield CategoryModel({"name": name, "href": href, "description": description}).update(query={"_id": ObjectId(_id)})
            # 这里并不一定正确，还需要test
        else:
            yield CategoryModel({"name": name, "href": href, "description": description}).save()
        self.write_ok()

    @coroutine
    def delete(self):
        """ delete """
        href = self.get_argument("href")
        yield CategoryModel.remove_entries(self.db, {"href": href})
        self.write_ok()


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

    @coroutine
    def post(self):
        """ add more"""
        bodys = json.loads(self.request.body)
        id_rows = []

        for body in bodys:
            name = body["name"]
            required = body["required"]
            default = body["default"]
            type_ = body["type_"]
            description = body["description"]
            api_id = body.get("api_id", "-1")
            _id = ObjectId()
            yield ParamModel({
                    "name": name, 
                    "required": required, 
                    "default": default, 
                    "type_": type_, 
                    "description": description,
                    "api_id": api_id, 
                    "_id": _id
                }).save()
            id_rows.append(str(_id))
        self.write_rows(rows=id_rows)

    @coroutine
    def put(self):
        """ update todo"""
        bodys = json.loads(self.request.body)
        id_rows = []

        for body in bodys:
            name = body["name"]
            required = body["required"]
            default = body["default"]
            type_ = body["type_"]
            description = body["description"]
            api_id = body.get("api_id", "-1")
            _id = ObjectId()
            yield ParamModel({
                    "name": name,
                    "required": required,
                    "default": default,
                    "type_": type_,
                    "description": description,
                    "api_id": api_id,
                    "_id": _id
                }).save()
            id_rows.append(str(_id))
        self.write_rows(rows=id_rows)

        yield ParamModel({"api_id": str(_id)}).update(query={"api_id": "-1"}, multi=True)
        ## 这样会把ParamModel里面别的字段给搞成null

        # cursor = ParamModel.get_cursor(self.db, {"api_id": "-1"})
        # param_objects = yield ParamModel.find(cursor)
        # yield [obj.update(update={"api_id": str(_id)}) for obj in param_objects]

        # import pdb; pdb.set_trace()
        # for obj in param_objects:
        #     obj.api_id = str(_id)
        #     yield obj.update()
        #     app_log.info(("update ParamModel:", obj.to_primitive()))

        ## bug 2017.7.19  暂时搞不定，只影响后面的删除，所以暂时搁这吧。。。
        ## 在mongodb的shell里面手动修改吧：
        # db.getCollection('params').update({"api_id": "-1"}, {$set:{"api_id": "596ecb42f0881b24e51c3e1a"}} , {multi: true})

        # self.write_ok()
        #self.write_rows(rows={"_id": str(_id)})
        # item = yield self.parse_param_one(model.to_primitive())
        # self.write_rows(rows=item)


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
            # todo: obj is None, 
            #'NoneType' object has no attribute 'to_primitive'

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

    @coroutine
    def delete(self):
        """ delete  todo:还要删除api里面两个参数list的子项"""
        _id = self.get_argument("id", None)
        if _id:
            query = {"_id": _id}
            obj = yield APiModel.find_one(self.db, query)
            try:
                yield [ParamModel.remove_entries(self.db, {"_id": param_id}) for param_id in obj.paramsIdList]
                yield [ParamModel.remove_entries(self.db, {"_id": param_id}) for param_id in obj.responseIdList]
                app_log.info(("remove ParamModel success of ApiModel:", _id, obj.paramsIdList, obj.responseIdList))
            except Exception as e:
                app_log.info(("remove ParamModel error of ApiModel:", _id))
                app_log.error(e)
            yield APiModel.remove_entries(self.db, query)
            app_log.info(("remove APiModel:", _id))
        self.write_ok()

    @coroutine
    def post(self):
        """ add """
        body = json.loads(self.request.body)
        app_log.info(body)
        name = body["name"]
        url = body["url"]
        method = body["method"]
        description = body["description"]
        paramsIdList = body["paramsIdList"]
        responseIdList = body["responseIdList"]
        paramsDemo = body["paramsDemo"]
        responseDemo = body["responseDemo"]
        category_href = body["category_href"]
        _id = ObjectId()
        model = APiModel({
                "name": name, 
                "url": url, 
                "method": method, 
                "description": description, 
                "paramsIdList": paramsIdList, 
                "responseIdList": responseIdList, 
                "paramsDemo": paramsDemo, 
                "responseDemo": responseDemo,
                "category_href": category_href,
                "_id": _id
            })
        yield model.save()
        app_log.info(("save APiModel:", str(_id)))
        # self.write_ok()
        # self.write_rows(rows={"_id": str(_id)})
        item = yield self.parse_param_one(model.to_primitive())
        self.write_rows(rows=item)

    @coroutine
    def put(self):
        """ update """
        body = json.loads(self.request.body)
        app_log.info(body)
        name = body["name"]
        url = body["url"]
        method = body["method"]
        description = body["description"]
        paramsIdList = body["paramsIdList"]
        responseIdList = body["responseIdList"]
        paramsDemo = body["paramsDemo"]
        responseDemo = body["responseDemo"]
        category_href = body["category_href"]
        _id = ObjectId()
        model = APiModel({
                "name": name,
                "url": url,
                "method": method,
                "description": description,
                "paramsIdList": paramsIdList,
                "responseIdList": responseIdList,
                "paramsDemo": paramsDemo,
                "responseDemo": responseDemo,
                "category_href": category_href,
                "_id": _id
            })
        yield model.save()
        app_log.info(("save APiModel:", str(_id)))

        # yield ParamModel({"api_id": str(_id)}).update(query={"api_id": "-1"}, multi=True)
        ## 这样会把ParamModel里面别的字段给搞成null

        # cursor = ParamModel.get_cursor(self.db, {"api_id": "-1"})
        # param_objects = yield ParamModel.find(cursor)
        # yield [obj.update(update={"api_id": str(_id)}) for obj in param_objects]

        # import pdb; pdb.set_trace()
        # for obj in param_objects:
        #     obj.api_id = str(_id)
        #     yield obj.update()
        #     app_log.info(("update ParamModel:", obj.to_primitive()))

        ## bug 2017.7.19  暂时搞不定，只影响后面的删除，所以暂时搁这吧。。。
        ## 在mongodb的shell里面手动修改吧：
        # db.getCollection('params').update({"api_id": "-1"}, {$set:{"api_id": "596ecb42f0881b24e51c3e1a"}} , {multi: true})

        # self.write_ok()
        #self.write_rows(rows={"_id": str(_id)})
        item = yield self.parse_param_one(model.to_primitive())
        self.write_rows(rows=item)

