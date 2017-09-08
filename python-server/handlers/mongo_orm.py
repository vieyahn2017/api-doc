#!/usr/bin/env python
#-*-coding:utf-8 -*-
# @author:yanghao 
# @created:20170414
## mongodb_models.py
## Description: motor ORM by schematics, change from acl_webapp.


from datetime import timedelta

from tornado import gen, ioloop
from schematics.models import Model
from schematics.types import NumberType, StringType
from pymongo.errors import ConnectionFailure
import motor
from bson.objectid import ObjectId

from core import context


# 这个log还需要根据项目改下
import logging
# l = logging.getLogger(__name__)

from tornado.log import app_log
l = app_log


MAX_FIND_LIST_LEN = 100
MONGO_RECONNECT_TRIES =  5
MONGO_RECONNECT_TIMEOUT = 2  # in seconds

class BaseMongoModel(Model):
    """
    Provides generic methods to work with model.
    Why use `MyModel.find_one` instead of `db.collection.find_one` ?
    1. Collection name is declared inside the model, so it is not needed
        to provide it all the time
    2. This `MyModel.find_one` will return MyModel instance, whereas
        `db.collection.find_one` will return dictionary

    Example with directly access:
        db_result = yield db.collection_name.find_one({"i": 3})
        obj = MyModel(db_result)

    Same example, but using MyModel.find_one:
        obj = yield MyModel.find_one(db, {"i": 3})

    #########################################

    Using motor with schematics simulate ORM.
    Like this:
        from schematics.types import StringType
        class NewsModel(BaseModel):
            title = StringType()
            content = StringType()
            author = StringType() 
            MONGO_COLLECTION = 'news'


    the api motor.Op is deprecated.
    # Old style:
    document = yield motor.Op(collection.find_one, {'_id': my_id})
    # New style:
    document = yield collection.find_one({'_id': my_id})
    """

    _id = NumberType(number_class=ObjectId, number_type="ObjectId")

    def __init__(self, *args, **kwargs):
        """ db settings
        虽然这边有db的属性，但是在handler里面写逻辑，有时候引用这个db不太方便，
        所以在handler里面加了db属性，直接在那边调用.
        注意各个方法，有的db是默认参数，有的db需要手动带入，使用时要注意别弄错了。
        """
        default_db = context['dbconn'].test
        self.set_db(kwargs.pop('db', default_db))
        super(BaseMongoModel, self).__init__(*args, **kwargs)

    @property
    def db(self):
        return getattr(self, '_db', None)

    def set_db(self, db):
        self._db = db

    @classmethod
    def process_query(cls, query):
        """
        query can be modified here before actual providing to database.
        """
        return dict(query)

    @property
    def pk(self):
        return self._id

    @classmethod
    def get_model_name(cls):
        return cls.MONGO_COLLECTION

    @classmethod
    def get_collection(cls):
        return getattr(cls, 'MONGO_COLLECTION', None)

    @classmethod
    def check_collection(cls, collection):
        return collection or cls.get_collection()

    @classmethod
    def find_list_len(cls):
        return getattr(cls, 'FIND_LIST_LEN', MAX_FIND_LIST_LEN)

    @classmethod
    @gen.coroutine
    def find_one(cls, db, query, collection=None, model=True):
        result = None
        c = cls.check_collection(collection)
        query = cls.process_query(query)
        for i in cls.reconnect_amount():
            try:
                result = yield db[c].find_one(query)
            except ConnectionFailure as e:
                exceed = yield cls.check_reconnect_tries_and_wait(i, 'find_one')
                if exceed:
                    raise e
            else:
                if model and result:
                    result = cls.make_model(result, "find_one", db=db)
                raise gen.Return(result)

    @classmethod
    @gen.coroutine
    def remove_entries(cls, db, query, collection=None):
        """
        Removes documents by given query.
        Example:
            obj = yield ExampleModel.remove_entries(
                self.db, {"first_name": "Hello"})
        """
        c = cls.check_collection(collection)
        query = cls.process_query(query)
        for i in cls.reconnect_amount():
            try:
                yield db[c].remove(query)
            except ConnectionFailure as e:
                exceed = yield cls.check_reconnect_tries_and_wait(i, 'remove_entries')
                if exceed:
                    raise e
            else:
                return

    @gen.coroutine
    def remove(self, db, collection=None):
        """
        Removes current instance from database.
        Example:
            obj = yield ExampleModel.find_one(self.db, {"last_name": "Sara"})
            yield obj.remove(self.db)
        """
        _id = self.to_primitive()['_id']
        yield self.remove_entries(db, {"_id": _id}, collection)

    @gen.coroutine
    def save(self, db=None, collection=None, ser=None):
        """
        If object has _id, then object will be created or fully rewritten.
        If not, object will be inserted and _id will be assigned.
        Example:
            obj = ExampleModel({"first_name": "Vasya"})
            yield obj.save(self.db)
        """
        db = db or self.db
        c = self.check_collection(collection)
        data = self.get_data_for_save(ser)
        result = None
        for i in self.reconnect_amount():
            try:
                result = yield db[c].save(data)
            except ConnectionFailure as e:
                exceed = yield self.check_reconnect_tries_and_wait(i, 'save')
                if exceed:
                    raise e
            else:
                if result:
                    self._id = result
                return

    @gen.coroutine
    def insert(self, db=None, collection=None, ser=None, **kwargs):
        """
        If object has _id, then object will be inserted with given _id.
        If object with such _id is already in database, then
        pymongo.errors.DuplicateKeyError will be raised.
        If object has no _id, then object will be inserted and _id will be
        assigned.

        Example:
            obj = ExampleModel({"first_name": "Vasya"})
            yield obj.insert()
        """
        db = db or self.db
        c = self.check_collection(collection)
        data = self.get_data_for_save(ser)
        for i in self.reconnect_amount():
            try:
                result = yield db[c].insert(data, **kwargs)
            except ConnectionFailure as e:
                exceed = yield self.check_reconnect_tries_and_wait(i, 'insert')
                if exceed:
                    raise e
            else:
                if result:
                    self._id = result
                return

    @gen.coroutine
    def update(self, db=None, query=None, collection=None, update=None, ser=None,
            upsert=False, multi=False):
        """
        Updates the object. If object has _id, then try to update the object.
        If object with given _id is not found in database, or object doesn't
        have _id field, then save it and assign generated _id.
        Difference from save:
            Suppose such object in database:
                {"_id": 1, "foo": "egg1", "bar": "egg2"}
            We want to save following data:
                {"_id": 1, "foo": "egg3"}
            If we'll run save, then in database will be following data:
                {"_id": 1, "foo": "egg3"} # "bar": "egg2" is removed
            But if we'll run update, then existing fields will be kept:
                {"_id": 1, "foo": "egg3", "bar": "egg2"}
        Example:
            obj = yield ExampleModel.find_one(self.db, {"first_name": "Foo"})
            obj.last_name = "Bar"
            yield obj.update(self.db)
        """
        db = db or self.db
        # TODO: refactor, update and ser arguments are very similar, left only one
        c = self.check_collection(collection)
        if update is None:
            data = self.get_data_for_save(ser)
        else:
            data = update
        if not query:
            _id = self.pk or data.pop("_id")
            query = {"_id": _id}
        if update is None:
            data = {"$set": data}
        for i in self.reconnect_amount():
            try:
                result = yield db[c].update(query, data, upsert=upsert, multi=multi)
            except ConnectionFailure as e:
                exceed = yield self.check_reconnect_tries_and_wait(i, 'update')
                if exceed:
                    raise e
            else:
                l.debug("Update result: {0}".format(result))
                raise gen.Return(result)

    @classmethod
    def get_cursor(cls, db, query, collection=None, fields={}):
        c = cls.check_collection(collection)
        query = cls.process_query(query)
        return db[c].find(query, fields) if fields else db[c].find(query)


    @classmethod
    @gen.coroutine
    def find(cls, cursor, model=True, list_len=None):
        """
        Returns a list of found documents.

        :arg cursor: motor cursor for find
        :arg model: if True, then construct model instance for each document.
            Otherwise, just leave them as list of dicts.
        :arg list_len: list of documents to be returned.

        Example:
            cursor = ExampleModel.get_cursor(self.db, {"first_name": "Hello"})
            objects = yield ExampleModel.find(cursor)
        """
        result = None
        list_len = list_len or cls.find_list_len() or MAX_FIND_LIST_LEN
        for i in cls.reconnect_amount():
            try:
                result = yield cursor.to_list(list_len)
            except ConnectionFailure as e:
                exceed = yield cls.check_reconnect_tries_and_wait(i, 'find')
                if exceed:
                    raise e
            else:
                if model:
                    field_names_set = set(cls._fields.keys())
                    for i in xrange(len(result)):
                        result[i] = cls.make_model(
                            result[i], "find", field_names_set)
                raise gen.Return(result)

    @classmethod
    @gen.coroutine
    def aggregate(cls, db, pipe_list, collection=None):
        c = cls.check_collection(collection)
        for i in cls.reconnect_amount():
            try:
                result = yield db[c].aggregate(pipe_list)
            except ConnectionFailure as e:
                exceed = yield cls.check_reconnect_tries_and_wait(i, 'aggregate')
                if exceed:
                    raise e
            else:
                raise gen.Return(result)


    @staticmethod
    def reconnect_amount():
        return xrange(MONGO_RECONNECT_TRIES + 1)

    @classmethod
    @gen.coroutine
    def check_reconnect_tries_and_wait(cls, reconnect_number, func_name):
        if reconnect_number >= MONGO_RECONNECT_TRIES:
            raise gen.Return(True)
        else:
            timeout = MONGO_RECONNECT_TIMEOUT
            l.warning("ConnectionFailure #{0} in {1}.{2}. Waiting {3} seconds"
                .format(
                    reconnect_number + 1, cls.__name__, func_name, timeout))
            io_loop = ioloop.IOLoop.instance()
            yield gen.Task(io_loop.add_timeout, timedelta(seconds=timeout))

    def get_data_for_save(self, ser):
        data = ser or self.to_primitive()
        if '_id' in data and data['_id'] is None:
            del data['_id']
        return data

    @classmethod
    def make_model(cls, data, method_name, field_names_set=None, db=None):
        """
        Create model instance from data (dict).
        """
        if field_names_set is None:
            field_names_set = set(cls._fields.keys())
        else:
            if not isinstance(field_names_set, set):
                field_names_set = set(field_names_set)
        new_keys = set(data.keys()) - field_names_set
        if new_keys:
            l.warning(
                "'{0}' has unhandled fields in DB: "
                "'{1}'. {2} returned data: '{3}'"
                .format(cls.__name__, new_keys, data, method_name))
            for new_key in new_keys:
                del data[new_key]
        return cls(raw_data=data, db=db)

