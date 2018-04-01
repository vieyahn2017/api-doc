#!/usr/bin/env python
# -*-coding:utf-8 -*-
# Author: tony - birdaccp at gmail.com
from __future__ import absolute_import, with_statement
from functools import wraps

import traceback

from tornado.gen import coroutine, Return
from tornado.log import app_log

from core import SystemStatus, EventHub
from connproxy import StoreContext

EVTHUB = EventHub()


class ModelOperException(Exception): pass


def cache(func):
    @wraps(func)
    def _cache(*args, **kwargs):
        if SystemStatus.cache_server_down():
            app_log.error("cache server down, using database query directly")
            return func(*args, **kwargs)

        model = args[0]
        get_cache_func = model.get_all_from_cache
        cache_func = model.cache_all
        if func.__name__ == "paging":
            get_cache_func = model.get_paging_from_cache
            cache_func = model.cache_paging
        elif func.__name__ == "filter_by":
            get_cache_func = model.get_filter_by_from_cache
            cache_func = model.cache_filter_by

        cached_result = get_cache_func(func.__name__, args, kwargs)
        if cached_result:
            return cached_result
        else:
            db_result = func(*args, **kwargs)
            if db_result:
                cache_func(func.__name__, args, kwargs, db_result)
            return db_result

    return _cache


class BaseModel(object):
    exclude_field = ()

    @coroutine
    # @cache
    def query(self, sql, params=None):
        with StoreContext() as store:
            cur = yield store.execute(sql, params)
            res = cur.fetchall()
        raise Return(res)

    @coroutine
    def get(self, sql, params=None):
        with StoreContext() as store:
            cur = yield store.execute(sql, params)
            res = cur.fetchone()
        raise Return(res)

    @coroutine
    def execute_0(self, sql, param):
        with StoreContext() as store:
            ctx = yield store.begin()
            try:
                yield ctx.execute(sql, param)
                yield ctx.commit()
                flag = True
            except:
                app_log.error("execute sql failed, raw_sql[{0}], details: {1}".format(sql, traceback.format_exc()))
                yield ctx.rollback()
                flag = False
        raise Return(flag)

    @coroutine
    def execute(self, sql, param=None):
        with StoreContext() as store:
            try:
                yield store.execute(sql, param)
                flag = True
            except:
                app_log.error("execute sql failed, raw_sql[{0}], details: {1}".format(sql, traceback.format_exc()))
                flag = False
        raise Return(flag)

    @coroutine
    def batch(self, sql, datas):
        with StoreContext() as store:
            ctx = yield store.begin()
            try:
                for param in datas:
                    yield ctx.execute(sql, param)
                yield ctx.commit()
                flag = True
            except:
                app_log.error(
                    "batch execute sql failed, raw_sql[{0}], details: {1}".format(sql, traceback.format_exc()))
                yield ctx.rollback()
                flag = False
        raise Return(flag)


class BaseGxmModel(BaseModel):
    """
    # gxm1015
    Base Class for admin modules.
    It contains some reusable method.
    Other model in Admin can inherit from this class.
    """

    def __init__(self):
        super(BaseGxmModel, self).__init__()

    @coroutine
    def execute_lastrowid(self, query, params=None):
        """
        Executes the given query, returning the lastrowid from the query.
        """
        with StoreContext() as store:
            cur = yield store.execute(query, params)
            res = cur.lastrowid
        raise Return(res)

    @coroutine
    def execute_rowcount(self, query, params=None):
        """Executes the given query, returning the rowcount from the query."""
        with StoreContext() as store:
            cur = yield store.execute(query, params)
            res = cur.rowcount
        raise Return(res)

    @coroutine
    def begin(self):
        """
        Start transaction
        Wait to get connection and returns `Transaction` object.
        :return: Future[Transaction]
        :rtype: Future
        """
        with StoreContext() as store:
            ctx = yield store.begin()
        raise Return(ctx)

    insert = execute_lastrowid
    update = execute_rowcount
    delete = execute_rowcount

    @property
    def cache_server(self):
        # with StoreCache() as mc:
        #     return mc
        return 1  # to do
