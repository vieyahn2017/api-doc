# -*- coding:utf-8 -*-
# Author alex8224 at gmail.com

from __future__ import absolute_import, with_statement
import time
import traceback
from threading import Thread, RLock, Event

try:
    from pylibmc import (WriteError, ServerDown, ConnectionError)
except:
    WriteError = ServerDown = ConnectionError = Exception

import constant
from tornado.log import app_log
from core import EVENTBUS
from utils import Singleton

from tornado_mysql.cursors import Cursor, DictCursor

__all__ = ("StoreContext")


class ConnectionPoolException(Exception): pass


class DbPoolNotStartedException(ConnectionPoolException): pass


class NoMoreConnectionException(ConnectionPoolException): pass


class BaseConnectionPool(Thread):
    def __init__(self, max_conn_number,
                 min_conn_number,
                 idle_timeout,
                 check_interval):

        super(BaseConnectionPool, self).__init__()
        self.setDaemon(True)
        self._min_conn_number = min_conn_number
        self._max_conn_number = max_conn_number
        self._busy = []
        self._idle = []
        self._bad = []
        self._idle_timeout = idle_timeout
        self._check_interval = check_interval
        self._last = time.time()
        self._lock = RLock()
        self._event = Event()
        self._errstack = ""
        self._run = False
        self._status = constant.STATE_PENGDING
        self._name = "Database Connection Pool"

    def _create_raw_connection(self):
        pass

    def initpool(self):
        for index in range(self._min_conn_number):
            raw_conn = self._create_raw_connection()
            if raw_conn:
                self._idle.append(raw_conn)

    def _access(self):
        self._last = time.time()

    def get_connection(self):
        with self._lock:
            self._access()
            if not self._run:
                raise ConnectionPoolException("ConnectionPool already exited!")
            if len(self._idle) > 0:
                conn = self._idle.pop(0)
                self._busy.append(conn)
                return conn
            elif len(self._idle) == 0 and len(self._busy) < self._max_conn_number:
                raw_conn = self._create_raw_connection()
                self._busy.append(raw_conn)
                return raw_conn
            else:
                raise NoMoreConnectionException("no more availe connection")

    def push_back(self, raw_conn):
        with self._lock:
            self._access()
            self._idle.append(raw_conn)
            if raw_conn in self._busy:
                self._busy.remove(raw_conn)

    def _call_whatever(self, callback, *args, **kwargs):
        try:
            callback(*args, **kwargs)
        except Exception:
            app_log.exception("_call_whatever error")

    def _close_conn(self, conn):
        pass

    def exit(self):
        with self._lock:
            for conn in self._idle:
                self._call_whatever(self._close_conn, conn)
            for conn in self._busy:
                self._call_whatever(self._close_conn, conn)
            self._run = False

    def _ping(self, conn):
        pass

    def clear_bad_conn(self, conn):
        with self._lock:
            self._bad.append(conn)
            if conn in self._busy:
                self._busy.remove(conn)

    def _keep_alived(self):
        for raw_conn in self._idle:
            self._call_whatever(self._ping, raw_conn)
        for raw_conn in self._busy:
            self._call_whatever(self._ping, raw_conn)

    def _clean_bad_conn(self):

        bad_number = len(self._bad)
        while len(self._bad) > 0:
            conn = self._bad.pop(0)
            if conn in self._busy:
                self._busy.remove(conn)
            if conn in self._idle:
                self._idle.remove(conn)

            self._call_whatever(self._close_conn, conn)

        if bad_number > 0:
            app_log.warn("cleaned %d closed connections" % bad_number)

    def server_down(self):
        with self._lock:
            self._state = constant.STATE_SERVER_DOWN

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, to_state):
        self._state = to_state
        if to_state == constant.STATE_RUNNING:
            EVENTBUS.emit_system_notify("cacheserver.up", "")

    def check_server(self):
        pass

    def _recycle(self):
        now = time.time()
        if now - self._last > self._idle_timeout:
            self._keep_alived()
            self._idle.extend(self._busy)
            self._busy = []
            decrease_number = len(self._idle) - self._min_conn_number
            if decrease_number <= 0:
                return
            for n in range(decrease_number):
                raw_conn = self._idle.pop(0)
                self._call_whatever(self._close_conn, raw_conn)

    def run(self):
        try:
            self.initpool()
        except:
            self._errstack = traceback.format_exc()
            self._event.set()
            return

        self._run = True
        self._state = constant.STATE_RUNNING
        app_log.info("%s started, I have %d connections " % (self._name, len(self._idle)))
        while self._run:
            self._event.set()
            with self._lock:
                self._clean_bad_conn()
                self._recycle()
                if self._state == constant.STATE_SERVER_DOWN:
                    self.check_server()
                else:
                    self._recycle()
                # app_log.debug("%s have %d idle, %d busy" % (self._name, len(self._idle), len(self._busy)))
            time.sleep(self._check_interval)

    @property
    def errors(self):
        return self._errstack

    def wait_start(self):
        self._event.wait()
        return self._run, self.errors


class CacheConnectionPool(BaseConnectionPool):
    __metaclass__ = Singleton

    def __init__(self, max_conn_number,
                 min_conn_number,
                 idle_timeout,
                 check_interval
                 ):
        super(CacheConnectionPool, self).__init__(
            max_conn_number,
            min_conn_number,
            idle_timeout, check_interval)
        self._name = "CacheConnection Pool"

    def _create_raw_connection(self):
        from utils import getmc
        return getmc()

    def check_server(self):
        mc = self._create_raw_connection()
        try:
            mc.get_stats()
            self.state = constant.STATE_RUNNING
        except:
            pass
            # app_log.error("Cache Server still Down!!!")

    def _ping(self, mc):
        pass

    def _close_conn(self, conn):
        conn.disconnect_all()

    @staticmethod
    def shutdown():
        CacheConnectionPool.instance().exit()

    @staticmethod
    def notify_server_down():
        CacheConnectionPool.instance().server_down()

    @staticmethod
    def instance():
        return CacheConnectionPool._instance


class CacheConnectionProxy(object):
    def __init__(self, mc):
        self._raw_mc_conn = mc

    def quit(self):
        pass

    def _call_whatever(self, callback, *args, **kwargs):
        try:
            return callback(*args, **kwargs)
        except (ServerDown, WriteError, ConnectionError):
            EVENTBUS.emit_system_notify("cacheserver.down", "")
            app_log.exception("call %s, args %s" % (callback.__name__, str(args)))

    def get(self, key):
        return self._call_whatever(self._raw_mc_conn.get, key.encode("utf-8"))

    def gets(self, key):
        return self._call_whatever(self._raw_mc_conn.gets, key.encode("utf-8"))

    def cas(self, *args, **kwargs):
        return self._call_whatever(self._raw_mc_conn.cas, *args, **kwargs)

    def set(self, key, *args):
        return self._call_whatever(self._raw_mc_conn.set, key.encode("utf-8"), *args)

    def get_multi(self, pairs):
        return self._call_whatever(self._raw_mc_conn.get_multi, pairs)

    def set_multi(self, *args, **kwargs):
        return self._call_whatever(self._raw_mc_conn.set_multi, *args, **kwargs)

    def delete_multi(self, pairs):
        return self._call_whatever(self._raw_mc_conn.delete_multi, pairs)

    def delete(self, key):
        return self._call_whatever(self._raw_mc_conn.delete, key)


def install_cache_pool():
    cache_pool = CacheConnectionPool(10, 5, 60, 5)
    cache_pool.start()
    started, errstack = cache_pool.wait_start()
    if not started:
        raise DbPoolNotStartedException("Cache Pool bootstrap failed!")


def get_proxy_mc():
    # cache_pool = CacheConnectionPool.instance()
    # raw_mc = cache_pool.get_connection()
    from utils import getmc
    return CacheConnectionProxy(getmc())


class StoreContext(object):
    def __init__(self, dictCursor=True, autocommit=False):
        self._store = None
        # self._autocommit = autocommit
        self._dictCursor = dictCursor

    def __enter__(self):
        from utils import getstore
        # from utils import get_true_store as getstore
        try:
            self._store = getstore()
            cursor = DictCursor if self._dictCursor else Cursor
            self._store.connect_kwargs['cursorclass'] = cursor

            # self._store.autocommit(self._autocommit)
        except:
            # if self._store:
            #     self._store.close()
            raise
        return self._store

    def __exit__(self, exc_type, exc_value, traceback):
        pass
        # if self._store:
        #    if exc_type is None:
        #        if not self._autocommit:
        #            try:
        #                self._store.commit()
        #            except:
        #                self._store.rollback()
        #    else:
        #        self._store.rollback()
        #    # self._store.close()
