# -*- coding:utf-8 -*-
import time
from tornado.ioloop import IOLoop
from tornado.concurrent import Future
from functools import partial


class MessageBackEnd(object):
    '''
    创建到消息后端的连接,发送消息
    '''

    def __init__(self, config):
        self._config = config
        self._connection = None

    def create_connection(self):
        pass

    def subscribe(self, topic, queuename, callback):
        pass

    def publish(self, topic, queuename, body, callback):
        pass


from pika import URLParameters
from pika.adapters.tornado_connection import TornadoConnection


class ChannelProxy(object):
    __WRAPPED_METHOD = ("")

    def __init__(self, channel):
        self._channel = channel

    def queue_declare(self, queue_name, callback=None, **options):
        '''
        如果提供了callback参数,则调用提供的callback
        如果没有提供,使用内置的callback方法,并返回一个future
        '''
        if callback:
            self._channel.queue_declare(callback, queue_name, **options)
        else:
            declare_future = Future()
            future_callback = partial(self.on_queue_declared, declare_future)
            self._channel.queue_declare(future_callback, queue_name)
            return declare_future

    def on_queue_declared(self, future, methodframe):
        future.set_result(methodframe)

    def publish(self, routing_key, body, exchange="", **options):
        self._channel.basic_publish(exchange, routing_key, body, **options)

    def __getattr__(self, attr):
        return getattr(self._channel, attr)


class RabbitBackend(MessageBackEnd):
    def __init__(self, config):
        super(RabbitBackend, self).__init__(config)
        self._channel = None
        self._ioloop = IOLoop.instance()
        self._timeout_callback = None

    def create_connection(self):
        url_params = self._config.MQ_URI
        future = Future()
        TornadoConnection(URLParameters(url_params),
                          partial(self.on_connection_open, future),
                          partial(self.on_open_error, future)
                          )
        return future

    def on_connection_open(self, future, unused_connection):
        self._connection = unused_connection
        future.set_result(self)
        self._connection.add_on_close_callback(self.on_connection_closed)

    def on_open_error(self, future, bad_connection, reason):
        exception = Exception("cannot create mq connection, Reason was %s" % reason)
        future.set_exception(exception)
        if self._timeout_callback:
            self._ioloop.remove_timeout(self._timeout_callback)
        self._ioloop.add_timeout(time.time() + 5, self.reconnect)

    @property
    def channel(self):
        return self.open_channel()

    def open_channel(self, callback=None):
        '''
        :param callback: 如果提供了callback,则在channe 成功打开后调用callback通知
        :type callback: callable
        :returns: None or future 如果没有提供callback, 则返回future
        :rtype: Future
        '''

        if callback:
            self._connection.channel(callback)
        else:
            future = Future()
            self._connection.channel(on_open_callback=partial(self.on_channel_open, future))
            return future

    def on_channel_open(self, future, channel):
        future.set_result(ChannelProxy(channel))

    def queue_declare(self, queue_name, callback=None):

        if callback:
            self.open_channel()
            self._channel.queue_declare(callback, queue_name)
        else:
            future = Future()

            def on_declare_ok(frame):
                future.set_result(None)

            def declare_queue(ch_future):
                self._channel.queue_declare(on_declare_ok, queue_name)

            if not self._channel:
                channel_future = self.open_channel()
                self._ioloop.add_future(channel_future, declare_queue)
            else:
                self._channel.queue_declare(on_declare_ok, queue_name)

            return future

    def exchange_declare(self, name, kind):
        declare_future = Future()
        self._channel.exchange_declare()
        return declare_future

    def publish(self,
                routing_key,
                body,
                exchange="",
                exchange_type="direct",
                **kwargs):

        def publish_callback(future):
            self._channel.basic_publish(exchange, routing_key, body)

        declare_future = self.queue_declare(routing_key)
        self._ioloop.add_future(declare_future, publish_callback)
        return declare_future

    def consume(self,
                queue,
                routing_key=None,
                callback=None,
                no_ack=True,
                exclusive=False,
                exchange="",
                channel=None
                ):
        # 怎么做到一直hold住一个连接并持续写回数据
        # 不调用self.finish方法并把连接标为异步


        def on_queue_bind(unused_frame):
            self._channel.basic_consume(callback, queue, no_ack, exclusive)
            # self._channel.basic_consume(on_message, queue, no_ack, exclusive)

        def start_consume(future):
            if exchange:
                self._channel.queue_bind(on_queue_bind, queue, exchange, routing_key)
            else:
                self._channel.basic_consume(callback, queue, no_ack, exclusive)
                # self._channel.basic_consume(on_message, queue, no_ack, exclusive)

        declare_future = self.queue_declare(queue)
        self._ioloop.add_future(declare_future, start_consume)

    def close(self):
        if self._channel:
            self._channel.close()
        if self._connection:
            self._connection.close()

    def on_connection_closed(self, connection, reply_code, reply_text):
        self._channel = None
        if self._timeout_callback:
            self._ioloop.remove_timeout(self._timeout_callback)
        self._timeout_callback = self._ioloop.add_timeout(time.time() + 5, self.reconnect)

    def reconnect(self):
        self.create_connection()

    def add_on_channel_close_callback(self):
        self._channel.add_on_close_callback(self.on_channel_closed)

    def on_channel_closed(self, channel, reply_code, reply_text):
        self._connection.close()

    def setup_exchange(self, exchange_name):
        self._channel.exchange_declare(self.on_exchange_declareok,
                                       exchange_name,
                                       self.EXCHANGE_TYPE)

    def on_exchange_declareok(self, unused_frame):
        self.setup_queue(self.QUEUE)

    def setup_queue(self, queue_name):
        self._channel.queue_declare(self.on_queue_declareok, queue_name)

    def on_queue_declareok(self, method_frame):
        self._channel.queue_bind(self.on_bindok, self.QUEUE,
                                 self.EXCHANGE, self.ROUTING_KEY)

    def add_on_cancel_callback(self):
        self._channel.add_on_cancel_callback(self.on_consumer_cancelled)

    def on_consumer_cancelled(self, method_frame):
        if self._channel:
            self._channel.close()

    def acknowledge_message(self, delivery_tag):
        self._channel.basic_ack(delivery_tag)

    def on_message(self, unused_channel, basic_deliver, properties, body):
        self.acknowledge_message(basic_deliver.delivery_tag)

    def on_cancelok(self, unused_frame):
        self.close_channel()

    def stop_consuming(self):
        if self._channel:
            self._channel.basic_cancel(self.on_cancelok, self._consumer_tag)

    def start_consuming(self):
        self.add_on_cancel_callback()
        self._consumer_tag = self._channel.basic_consume(self.on_message,
                                                         self.QUEUE)

    def on_bindok(self, unused_frame):
        self.start_consuming()

    def close_channel(self):
        self._channel.close()
