#!/usr/bin/env python
#-*-coding:utf-8 -*-
#
#Author: tony - birdaccp at gmail.com
#Create by:2015-08-11 15:50:42
#Last modified:2017-05-27 16:26:57
#Filename:config.py
#Description:

base_host = "10.0.0.161"

settings = {
    "gzip": False,
    "salt":"dL4+QD38pvumyQ+4KH1txZkNt3cez3+NtL2Sz70XNCo=",
    "token_duration": 3600,
    "token_name":"X-Xsrf-Token",
    "logfile": "/tmp/microcloud_server.log",
    "executor_number": 10  #真正运行时估计不够
}

mongodbConf = {
    "host": "{0}:27017".format(base_host), 
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

#MESSAGE_BACKEND = "message.RabbitBackend"
#MQ_URI = "amqp://guest:guest@localhost:5672/%2F"


UPLOAD_PATH = "/tmp/upload/%s"
#UPLOAD_PATH = "/tmp/%s"
UPLOAD_URL  = "/upload/%s"
VALID_FILE_EXT = (".png", ".jpg", ".gif")

API_VERSION = 'v1'


DEFAULT_PORT = 30001
LOCALHOST_PREFIX = "http://localhost:%s" % DEFAULT_PORT
