#!/usr/bin/env python
# -*-coding:utf-8 -*-

base_host = "127.0.0.1"

settings = {
    "gzip": False,
    "salt":"dL4+QD38pvumyQ+4KH1txZkNt3cez3+NtL2Sz70XNCo=",
    "token_duration": 3600,
    "token_name": "X-Xsrf-Token",
    "logfile": "log/api_doc.log",
    "executor_number": 10  #真正运行时估计不够
}

dbConf = {
    "host": base_host,
    "port": 3306,
    "db":  "test",
    "user": "test",
    "password": "test",
    "charset": "utf8",
}

dbPool = {
    "max_idle_connections": 20, #最大保持连接数
    "max_recycle_sec": 3, #回收时间
}

cacheServers = ["{0}:11211".format(base_host)]

EVENT_HOOKS = (
            "events.UserLoginWatcher",
            "events.CacheFlushWatcher",
            "events.UserWatcher",
            "events.SyncSystemMessage",
            "events.SystemAlertWatcher",
            "events.NoticeWatcher",
        )

MIDDLEWARE_CLASSES = (
            "auth.CheckLogin",
            "auth.CheckRights",
            #"cache.CacheMyWorkResponse",
            "auth.SetDefaultHeader",
        )

RBAC_FILE = "./rights.yml"

API_VERSION = 'v1'

DEFAULT_PORT = 3000
DEFAULT_MODULE = "ApiModule"
# DEFAULT_MODULE = "ApiShow"


# python server.py --module=ApiModule --port=3001

# handlers里面按照模块组织代码，里面有个ApiModule文件夹，这边加个api模块
# urls.py里面按照模块导入

BASE_URL = "http://%s:%s" % (base_host, DEFAULT_PORT)

import motor
mongodb_host = "{0}:27017".format(base_host)
mongodb_client = motor.motor_tornado.MotorClient('mongodb://%s' % mongodb_host)
MONGODB_CONN = mongodb_client.apis

# 统一确定了：API用到的mongodb数据库集合名字为：apidocs