#!/usr/bin/env python
# -*-coding:utf-8 -*-
# @author: yanghao 
# @created:
## Description:


from __future__ import absolute_import

from tornado.gen import coroutine, Return
from tornado.log import app_log

from handlers import BaseProxyHandler, Route
from core import context, cache_client

import datetime
import json
import uuid
from bson import ObjectId

from .model import CategoryModel, ParamModel, APiModel, RecordAPiModel, RecordModel


class BaseMongoHandler(BaseProxyHandler):
    @property
    def db(self):
        return context['dbconn']

    def write_models(self, models):
        """write json, add key[datas] to the obj list"""
        try:
            # objects_list = [obj.to_primitive() for obj in models]
            objects_list = []
            for obj in models:
                if obj:
                    objects_list.append(obj.to_primitive())
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
class ApiAuthenticatedHandler(BaseMongoHandler):
    @coroutine
    def get(self):
        self.write_ok()


@Route("m/api/category")
class CategoryModelHandler(BaseMongoHandler):
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
            yield CategoryModel({"name": name, "href": href, "description": description}).update(
                query={"_id": ObjectId(_id)})
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
class ParamModelHandler(BaseMongoHandler):
    @coroutine
    def get(self):
        objects = []
        _id = self.get_argument('id', None)
        if _id:
            obj = yield ParamModel.find_one(self.db, {"_id": _id})
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
        """ add more; 新增加的api_id暂时传递给前端使用"""
        bodys = json.loads(self.request.body)
        # print bodys
        id_rows = []
        api_id = str(uuid.uuid1())

        for body in bodys:
            type_ = body["type_"]
            _id = body["_id"]  # 直接使用前端传来的_id
            parent_id = body.get("parent_id")
            if parent_id:
                continue
                # parent_id不为null/None的根param，只是前端展示加入的Mock数据，跳过

            subParamsIdList = []  # children -> subParamsIdList
            # json字段，单独处理，目前不支持多层嵌套。
            if type_ == "json":
                children = body["children"]
                for child in children:
                    child_id = child["_id"]  # 直接使用前端传来的_id
                    subParamsIdList.append(child_id)
                    # print _id, child["parent_id"]
                    assert _id == child["parent_id"]
                    yield ParamModel({
                        "name": child["name"],
                        "required": child["required"],
                        "default": child["default"],
                        "type_": child["type_"],
                        "description": child["description"],
                        "parent_id": child["parent_id"],
                        "category_href": child["category_href"],
                        "subParamsIdList": [],
                        "_id": child_id,
                        "api_id": api_id
                    }).save()

            yield ParamModel({
                "name": body["name"],
                "required": body["required"],
                "default": body["default"],
                "type_": type_,
                "description": body["description"],
                "parent_id": None,
                "category_href": body["category_href"],
                "subParamsIdList": subParamsIdList,
                "_id": _id,
                "api_id": api_id
            }).save()
            id_rows.append(str(_id))

        self.write_rows(rows={
            "param_ids": id_rows,
            "temp_api_id": api_id
        })

    @coroutine
    def put(self):
        """ update
        跟post比较大的不同，我在前端多封装了一层，封装了一个api_id和rows
        """
        bodys = json.loads(self.request.body)
        if bodys:
            api_id = bodys["api_id"]
            id_rows = []
            for body in bodys["rows"]:  # body这个沿袭自post变量名其实不合适
                type_ = body["type_"]
                _id = body["_id"]  # 不管是新建的，还是以前存在的，都有从前端传来的_id
                parent_id = body.get("parent_id")
                if parent_id:
                    continue
                    # parent_id不为null/None的根param，只是前端展示加入的Mock数据，跳过

                subParamsIdList = []  # children -> subParamsIdList
                # json字段，单独处理，目前不支持多层嵌套。
                if type_ == "json":
                    children = body["children"]
                    for child in children:
                        child_id = child["_id"]  # 直接使用前端传来的_id
                        subParamsIdList.append(child_id)
                        # print _id, child["parent_id"]
                        assert _id == child["parent_id"]
                        yield ParamModel({
                            "name": child["name"],
                            "required": child["required"],
                            "default": child["default"],
                            "type_": child["type_"],
                            "description": child["description"],
                            "parent_id": child["parent_id"],
                            "category_href": child["category_href"],
                            "subParamsIdList": [],
                            "_id": child_id,
                            "api_id": api_id
                        }).save()

                yield ParamModel({
                    "name": body["name"],
                    "required": body["required"],
                    "default": body["default"],
                    "type_": type_,
                    "description": body["description"],
                    "parent_id": None,
                    "category_href": body["category_href"],
                    "subParamsIdList": subParamsIdList,
                    "api_id": api_id,
                    "_id": _id
                }).save()
                id_rows.append(_id)

            self.write_rows(rows=id_rows)
        else:
            self.write_failure(msg="no bodys to load.")


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
class APiModelHandler(BaseMongoHandler):
    @coroutine
    def parse_param_sub_list(self, sub_list):
        res_list = []
        for id_param in sub_list:
            object_param = yield ParamModel.find_one(self.db, {"_id": id_param})
            if object_param:
                result = yield object_param.to_primitive_fix()
                res_list.append(result)
            pass # 不加这句，自动format会把下面这堆注释缩进一个Tab
            # # 下面是把children代为mock数据append，这种会有问题！
            # # 还是到前端去append吧，还是同一个对象，处理也省事好多，不需要单独去同步数据
            # for sub_id_param in object_param.subParamsIdList:
            #     assert object_param.type_ == 'json'
            #     object_param_sub = yield ParamModel.find_one(self.db, {"_id": sub_id_param})
            #     if object_param_sub:
            #         result = yield object_param_sub.to_primitive_fix()
            #         res_list.append(result)
        raise Return(res_list)

    @coroutine
    def parse_param_one(self, item):
        paramsIdList = item.pop("paramsIdList")
        paramsList = yield self.parse_param_sub_list(paramsIdList)
        responseIdList = item.pop("responseIdList")
        responseList = yield self.parse_param_sub_list(responseIdList)
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
        """ delete  同时删除api里面两个param子项参数list"""
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
        # app_log.info(body)
        _id = ObjectId()
        model = APiModel({
            "name": body["name"],
            "url": body["url"],
            "method": body["method"],
            "description": body["description"],
            "paramsIdList": body["paramsIdList"],
            "responseIdList": body["responseIdList"],
            "requestUrlDemo": body["requestUrlDemo"],
            "requestParamsDemo": body["requestParamsDemo"],
            "responseDemo": body["responseDemo"],
            "category_href": body["category_href"],
            "_id": _id
        })
        yield model.save()
        app_log.info(("save APiModel:", str(_id)))

        # update temp api_id (from param: uuid)
        temp_api_ids = body["temp_api_ids"]
        for temp_api_id in temp_api_ids:
            cursor = ParamModel.get_cursor(self.db, {"api_id": temp_api_id})
            param_objects = yield ParamModel.find(cursor)
            for obj in param_objects:
                obj.api_id = str(_id)
                # yield obj.update(self.db)
                yield obj.save(self.db)

        item = yield self.parse_param_one(model.to_primitive())
        self.write_rows(rows=item)

    @coroutine
    def put(self):
        """ update """
        body = json.loads(self.request.body)
        # app_log.info(body)
        _id = body["_id"]
        model = APiModel({
            "name": body["name"],
            "url": body["url"],
            "method": body["method"],
            "description": body["description"],
            "paramsIdList": body["paramsIdList"],
            "responseIdList": body["responseIdList"],
            "requestUrlDemo": body["requestUrlDemo"],
            "requestParamsDemo": body["requestParamsDemo"],
            "responseDemo": body["responseDemo"],
            "category_href": body["category_href"],
            "_id": _id
        })
        yield model.save()
        app_log.info(("update APiModel:", _id))

        item = yield self.parse_param_one(model.to_primitive())
        self.write_rows(rows=item)


@Route("m/api/record/api")
class RecordApiModelHandler(BaseMongoHandler):
    @coroutine
    def get(self):
        objects = []
        _id = self.get_argument('id', None)
        if _id:
            obj = yield RecordAPiModel.find_one(self.db, {"_id": _id})
            objects.append(obj)
        else:
            cursor = RecordAPiModel.get_cursor(self.db, {})
            objects = yield RecordAPiModel.find(cursor)
        if objects:
            self.write_models(objects)
        else:
            self.write_ok(msg="no result")

    @coroutine
    def post(self):
        bodys = json.loads(self.request.body)
        id_rows = []
        for body in bodys:
            _id = ObjectId()
            yield RecordAPiModel({
                "name": body["name"],
                "category_href": body["category_href"],
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "content": body["content"],
                "api_id": body["api_id"],
                "_id": _id  # _id是这个RecordApiModel本身的_id, api_id 是对应的api的_id
            }).save()
            id_rows.append(str(_id))
        self.write_rows(rows=id_rows)


@Route("m/api/record")
class RecordModelHandler(BaseMongoHandler):
    @coroutine
    def get(self):
        """ db.getCollection('record').find({"category_href": {"$ne":null}}) """
        objects = []
        _id = self.get_argument('id', None)
        if _id:
            obj = yield RecordModel.find_one(self.db, {"_id": _id})
            objects.append(obj)
        else:
            href = self.get_argument('href', {"$ne": None})
            cursor = RecordModel.get_cursor(self.db, {"category_href": href})
            objects = yield RecordModel.find(cursor)

        if objects:
            self.write_models(objects)
        else:
            self.write_ok(msg="no result")

    @coroutine
    def post(self):
        body = json.loads(self.request.body)
        yield RecordModel({
            "name": body["name"],
            "version": body["version"],
            "category_href": body["category_href"],
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "RecordApiIdList": body["RecordApiIdList"],
            "_id": ObjectId()
        }).save()
        self.write_ok()

    @coroutine
    def put(self):
        """ 只允许，修改版本 version """
        body = json.loads(self.request.body)
        yield RecordModel({
            "name": body["name"],
            "version": body["version"],
            "category_href": body["category_href"],
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "RecordApiIdList": body["RecordApiIdList"],
            "_id": ObjectId()
        }).save()
        self.write_ok()
