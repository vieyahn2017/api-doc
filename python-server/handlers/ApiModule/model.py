#!/usr/bin/env python
# -*-coding:utf-8 -*-
# @author:yanghao 
# @created:20170414
# # Description: motor ORM by schematics, this file is the models.


from schematics.types import StringType, IntType, BooleanType
from schematics.types.compound import ListType, DictType
from schematics.contrib.mongo import ObjectIdType
from handlers.mongo_orm import BaseMongoModel

from core import context


# 想写一个公有类，实现这两个属性的自动化，未完成
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
    """ [{"name":"Type1","href":"type1","description":"this is type1"}]  """
    name = StringType()
    href = StringType()
    description = StringType()

    _id = ObjectIdType(serialize_when_none=False)
    MONGO_COLLECTION = 'category'


class ParamModel(BaseAPIModel):
    # id = IntType()
    name = StringType()
    required = BooleanType()
    default = StringType()
    type_ = StringType()
    description = StringType()
    subParamsIdList = ListType(StringType)   # type_=="json"，此项有值。
    parent_id = StringType() # 如果是api_id的直系节点。此字段为None；【与之对应的是type_=="json"类型参数的子节点】
    api_id = StringType()

    _id = ObjectIdType(serialize_when_none=False)
    MONGO_COLLECTION = 'params'


class APiModel(BaseAPIModel):
    name = StringType()
    category_href = StringType()
    url = StringType()
    method = StringType()
    description = StringType()
    paramsIdList = ListType(StringType)
    responseIdList = ListType(StringType)
    paramsDemo = StringType()
    responseDemo = StringType()

    _id = ObjectIdType(serialize_when_none=False)
    MONGO_COLLECTION = 'api'


# to do
# add delete_flag: true/false 代替删除


"""
{
    "Name": "param_1_name", 
    "Required": "false",
    "Default": "", 
    "Type": "string", 
    "Description": "Description of the first parameter."
}, 


{
    "name": "接口名1", 
    "url": "接口url", 
    "method": "GET", 
    "description": "接口描述", 
    "params": [
        {
            "Name": "param_1_name", 
            "Required": "true",
            "Default": "", 
            "Type": "string", 
            "Description": "Description of the first parameter."
        }, 
        {}
    ], 
    "response": [
        {
            "Name": "param_1_name", 
            "Required": "true",
            "Default": "", 
            "Type": "string", 
            "Description": "Description of the first parameter."
        }, 
        {
            "Name": "userId", 
            "Required": "true",
            "Default": "", 
            "Type": "string", 
            "Description": "The userId parameter that is in the URI."
        }
    ], 
    "demo": "<?php  var_dump(123);"
}, 

"""
