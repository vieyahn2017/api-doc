#!/usr/bin/env python
# -*-coding:utf-8 -*-
# @author:yanghao 
# @created:
# # Description: motor ORM by schematics, this file is the models.

from schematics.types import StringType, IntType, BooleanType
from schematics.types.compound import ListType, DictType
from schematics.contrib.mongo import ObjectIdType
from tornado.gen import coroutine, Return
from handlers.mongo_orm import BaseMongoModel
from core import context


# 想在公有类，实现这两个属性的自动化，未完成
# class MyBaseModel(BaseModel):
#     MONGO_COLLECTION = ""
#     _id = ObjectIdType(serialize_when_none=False)
#     def __init__(self):
#         MONGO_COLLECTION = self.__class__.__name__[:-5]

class BaseAPIModel(BaseMongoModel):
    def __init__(self, *args, **kwargs):
        super(BaseAPIModel, self).__init__(*args, **kwargs)
        default_db = context['dbconn']
        self.set_db(kwargs.pop('db', default_db))


class CategoryModel(BaseAPIModel):
    name = StringType()
    href = StringType()
    description = StringType()

    _id = ObjectIdType(serialize_when_none=False)
    MONGO_COLLECTION = 'category'


class ParamModel(BaseAPIModel):
    _id = StringType()
    name = StringType()
    required = BooleanType()
    default = StringType()
    type_ = StringType()
    description = StringType()
    subParamsIdList = ListType(StringType)  # type_=="json"，此项有值。
    parent_id = StringType()  # 如果是api_id的直系节点。此字段为None；【与之对应的是type_=="json"类型参数的子节点】
    api_id = StringType()
    category_href = StringType()

    # _id = ObjectIdType(serialize_when_none=False)
    MONGO_COLLECTION = 'params'

    @coroutine
    def to_primitive_fix(self):
        """ # subParamsIdList -> children """
        result = self.to_primitive()
        children = []
        if len(self.subParamsIdList):
            assert self.type_ == 'json'
        for sub_id in self.subParamsIdList:
            query = {"_id": sub_id}
            sub_obj = yield self.find_one(self.db, query)
            sub_result = sub_obj.to_primitive()
            sub_result.update({"children": []})
            del sub_result["subParamsIdList"]
            children.append(sub_result)
        result.update({"children": children})
        del result["subParamsIdList"]
        # print "to_primitive_fix===", result
        raise Return(result)


class APiModel(BaseAPIModel):
    name = StringType()
    category_href = StringType()
    url = StringType()
    method = StringType()
    description = StringType()
    paramsIdList = ListType(StringType)
    responseIdList = ListType(StringType)
    requestUrlDemo = StringType()
    requestParamsDemo = StringType()
    responseDemo = StringType()

    _id = ObjectIdType(serialize_when_none=False)
    MONGO_COLLECTION = 'api'


# to do
# add delete_flag: true/false 代替删除

# # 在mongodb的shell里面手动修改：
#  db.getCollection('params').update({"api_id": "-1"}, {$set:{"api_id": "596ecb42f0881b24e51c3e1a"}} , {multi: true})


class RecordAPiModel(BaseAPIModel):
    api_id = StringType()
    name = StringType()
    category_href = StringType()
    time = StringType()
    content = StringType()

    _id = ObjectIdType(serialize_when_none=False)
    MONGO_COLLECTION = 'recordapi'


class RecordModel(BaseAPIModel):
    name = StringType()
    version = StringType()
    time = StringType()
    RecordApiIdList = ListType(StringType)

    _id = ObjectIdType(serialize_when_none=False)
    MONGO_COLLECTION = 'record'