#!/usr/bin/env python
# -*-coding:utf-8 -*-
#
# Author: tony - birdaccp at gmail.com
# Create by:2014-08-16 22:39:36
# Last modified:2017-05-24 17:15:24
# Filename:utils.py
# Description:

import imghdr
import tempfile
from uuid import uuid1
from hashlib import sha256
from base64 import encodestring
from tornado.log import app_log
import yaml

# from PIL import Image
from datetime import datetime
import config

RANDOM_SEED = "1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def save_avatar(photodata):
    ext = is_image(stream=photodata)
    if ext:
        filename = "%s.%s" % (get_tempname(), ext)
        fullpath = config.UPLOAD_PATH % filename
        with open(fullpath, "wb") as avatar:
            avatar.write(photodata)
        return unicode(config.UPLOAD_URL % filename)
    else:
        raise Exception("file format error")


def get_mqclient():
    from core import context
    return context.get("message_backend")


def load_rbacfile():
    from config import RBAC_FILE
    try:
        rbac_dict = yaml.load(file(RBAC_FILE))
        return rbac_dict["rights"]
    except IOError as ioex:
        app_log.exception(ioex.message)


def async_client():
    from tornado.httpclient import AsyncHTTPClient
    return AsyncHTTPClient(max_body_size=1024 * 100)


def is_image(filename=None, stream=None):
    return imghdr.what(filename, stream)


def valid_filename(self, ext):
    ext = ext.lower()
    if ext not in config.VALID_FILE_EXT:
        raise Exception(500, "invalid fiename")


def get_tempname():
    return next(tempfile._get_candidate_names())


def module_resolver(namespace):
    namespace_parts = namespace.split(".")
    module_name = ".".join(namespace_parts[0:-1])
    cls_name = namespace_parts[-1]
    try:
        module = __import__(module_name, fromlist=["*"])
        if hasattr(module, cls_name):
            return getattr(module, cls_name)
    except Exception as ex:
        app_log.error("resolve %s failed with exception %s" % (namespace, ex))


def is_dirty(model_obj):
    obj_info = model_obj.__storm_object_info__
    return obj_info.get("sequence")


def table_name(tables):
    names = []
    if not tables:
        return
    if hasattr(tables, "__storm_table__"):
        tables = [tables]

    for table in tables:
        if hasattr(table, "__storm_table__"):
            names.append(table.__storm_table__)
        else:
            names.append(table.table.__storm_table__)
    return names


def tables_key(table_names):
    return ["%s.keys" % table for table in table_names]


def copy_model(src):
    model = src.__class__
    model_obj = model()
    for column_name in model._storm_columns.itervalues():
        column_name = column_name.name
        try:
            setattr(model_obj, column_name, getattr(src, column_name))
        except:
            pass
    return model_obj


def build_all_hash(model, func_name, args, kwargs):
    remain_args = args[1:]
    if remain_args:
        condition_hash = "".join(str(hash(obj)) for obj in remain_args)

    if kwargs:
        condition_hash = hash(tuple(zip(kwargs.iterkeys(), kwargs.itervalues())))

    return "%s.%s.%s" % (model.__storm_table__, func_name, str(condition_hash))


def build_paging_hash(model, func_name, args, kwargs):
    key = "%s.%s.%d"
    table = model.__storm_table__
    form = args[1]
    rs = args[2]
    startindex, endindex = parsepage(form)
    rs = rs[startindex:endindex]
    rs_hash = hash(rs.get_select_sql())
    return key % (table, func_name, rs_hash)


def build_filter_by_hash(model, func_name, args, kwargs):
    key = "%s.%s.%d"
    table = model.__storm_table__
    form = args[1]
    return key % (table, func_name, hash(form))


def rowlist(rows):
    resultset = []
    for row in rows:
        resultset.append(dict(row))
    return resultset


def get_columns(modelcls, extra_field=None):
    sort_columns = [column.name for column in modelcls._storm_columns.itervalues()]
    sort_columns.sort()
    if extra_field:
        sort_columns.extend(extra_field)
    return sort_columns


def iter_row(model):
    columns = (col.name for col in model._storm_columns.itervalues())
    for col in columns:
        if col == "createtime":
            yield col, str(getattr(model, col))
        else:
            yield col, getattr(model, col)


def zip_row(*iterables):
    sentinel = object()
    iterators = [iter(it) for it in iterables]
    while iterators:
        result = []
        for it in iterators:
            elem = next(it, sentinel)
            if elem is sentinel:
                return
            if isinstance(elem, datetime):
                elem = str(elem)
            result.append(elem)
        yield tuple(result)


def get_row(cls, row):
    return zip_row(get_columns(cls), row)


def get_rows(modelcls, db, rs, extra_field=None):
    columns = get_columns(modelcls, extra_field)
    sql, params = rs.get_select_sql()
    raw_cursor = db.raw_execute(sql, params)
    while True:
        row = raw_cursor.fetchmany()
        if row:
            yield dict(zip_row(columns, row[0]))
        else:
            break


def fetch_lazy_rows(rs):
    return [dict(row) for row in rs]


def fetch_rows(clazz, rs):
    rows = []
    columns = get_columns(clazz)
    for rec_ins in rs:
        record = {}
        for name in columns:
            value = getattr(rec_ins, name)
            if isinstance(value, datetime):
                value = str(value)
            record[name] = value
        rows.append(record)
    return rows


def build_password(pwd):
    from config import settings
    salt = settings["salt"]
    key = "%s%s" % (salt, pwd.strip())
    return unicode(sha256(key).hexdigest())


def build_random_passwd():
    import random
    plain_pwd = "".join((random.choice(RANDOM_SEED) for _ in xrange(8)))
    hash_pwd = unicode(sha256(plain_pwd).hexdigest())
    return plain_pwd, hash_pwd


def build_token(factor=""):
    key = "%s_%s" % (str(uuid1()), factor)
    return encodestring(sha256(key).digest()).strip()


class Singleton(type):
    def __call__(clazz, *args, **kwargs):
        if hasattr(clazz, "_instance"):
            return clazz._instance
        else:
            clazz._instance = super(Singleton, clazz).__call__(*args, **kwargs)
            return clazz._instance


def parsepage(form):
    pageindex, pagesize = form.curpage.data, form.perpage.data
    startindex = (pageindex - 1) * pagesize
    endindex = startindex + pagesize
    return startindex, endindex


def getstore():
    from config import dbConf, dbPool
    from tornado_mysql import pools
    # pools.DEBUG = True #调试模式
    return pools.Pool(dbConf, **dbPool)


def getmc():
    try:
        from pylibmc import Client
        from config import cacheServers
        adv_setting = {"cas": True, "tcp_nodelay": True, "ketama": True}
        return Client(cacheServers, binary=True, behaviors=adv_setting)
    except Exception as e:
        print e
        print "import pylibmc failed, perhaps your os is not supported"
