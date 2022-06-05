#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import  # needed for zmq import
import six
import zmq
import time
from Common.tinyrpc import HEARTBEAT_INTERVAL, FCT_HEARTBEAT
from Common.tinyrpc.transports import ServerTransport,ClientTransport
import json
import Configure.events as events
DEFAULT_RPC_TIMEOUT = 5000
LOGGER_PORT = 19000
LOGGER_PUB = 19100


class LoggerReport(object):

    event = None
    data = None
    site = None

    def _to_dict(self):
        jdata = dict(event=self.event, data=self.data,site=self.site)
        return jdata

    def serialize(self):
        return json.dumps(self._to_dict())

    def __repr__(self):
        r_str = 'event=' + events.get_name(self.event) + '; data=' + str(self.data) + '; site=' + str(self.site)
        return r_str


class ReporterProtocol(object):

    @staticmethod
    def parse_report(msg):
        if 'data' in msg and 'event' in msg:
            report_dict = json.loads(msg)
            # print report_dict,type(report_dict)
            report = LoggerReport()
            report.event = report_dict.get("event")
            report.site = report_dict.get("site")
            report.data = report_dict.get("data")
            return report
        else:
            return None


class LoggerServerTransport(ServerTransport):
    """Server transport based on a :py:const:`zmq.ROUTER` socket.

    :param socket: A :py:const:`zmq.ROUTER` socket instance, bound to an
                   endpoint.
    """

    def __init__(self, socket, polling_milliseconds=0):
        self.publisher = None
        self.socket = socket
        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)
        self.polling_milliseconds = polling_milliseconds
        self.heartbeat_at = time.time()

    def broadcast(self, msg):
        if self.publisher:
            self.publisher.publish(msg)
        # TODO: HB shall be out per 5sec or only needed as NOP when PUB idle?

    def check_heartbeat(self):
        t_now = time.time()
        if t_now >= self.heartbeat_at:

            self.broadcast(FCT_HEARTBEAT)
            self.heartbeat_at = time.time() + HEARTBEAT_INTERVAL

    def receive_message(self):
        """Asynchronous poll socket"""
        socks = dict(self.poller.poll(HEARTBEAT_INTERVAL * 1000))
        if socks.get(self.socket) == zmq.POLLIN:
            msg = self.socket.recv_multipart()
            context, message = msg[:-1], msg[-1]
            self.broadcast('received: ' + message)
        else:
            context, message = None, None
        return context, message

    def send_reply(self, context, reply):
        self.socket.send_multipart(context + [reply])
        self.broadcast('response: ' + reply)

    @classmethod
    def create(cls, zmq_context, endpoint, polling_milliseconds=0):
        """Create new server transport.

        Instead of creating the socket yourself, you can call this function and
        merely pass the :py:class:`zmq.core.context.Context` instance.

        By passing a context imported from :py:mod:`zmq.green`, you can use
        green (gevent) 0mq sockets as well.

        :param zmq_context: A 0mq context.
        :param endpoint: The endpoint clients will connect to.
        """
        socket = zmq_context.socket(zmq.ROUTER)
        socket.bind(endpoint)
        return cls(socket, polling_milliseconds)

    def shutdown(self):
        if not self.socket.closed:
            self.socket.setsockopt(zmq.LINGER, 0)
            self.socket.close()


class LoggerClientTransport(ClientTransport):
    """Client transport based on a :py:const:`zmq.REQ` socket.

    :param socket: A :py:const:`zmq.REQ` socket instance, connected to the
                   server socket.
        :param zmq_context: A 0mq context.
        :param endpoint: The endpoint the server is bound to.
    """

    def __init__(self, socket, context, endpoint, timeout=DEFAULT_RPC_TIMEOUT):
        self.publisher = None
        self.socket = socket
        self.context = context
        self.endpoint = endpoint
        self.timeout = timeout

    def reconnect(self):
        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.close()
        time.sleep(0.1)
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.connect(self.endpoint)


    def send_only(self, message):
        poll = zmq.Poller()
        poll.register(self.socket, zmq.POLLIN)

        if six.PY3 and isinstance(message, six.string_types):
            # pyzmq won't accept unicode strings
            message = message.encode()
        self.socket.send(message)

    def shutdown(self):
        if not self.socket.closed:
            self.socket.setsockopt(zmq.LINGER, 0)
            self.socket.close()

    @classmethod
    def create(cls, zmq_context, endpoint):
        """Create new client transport.

        Instead of creating the socket yourself, you can call this function and
        merely pass the :py:class:`zmq.core.context.Context` instance.

        By passing a context imported from :py:mod:`zmq.green`, you can use
        green (gevent) 0mq sockets as well.

        :param zmq_context: A 0mq context.
        :param endpoint: The endpoint the server is bound to.
        """
        socket = zmq_context.socket(zmq.DEALER)
        socket.connect(endpoint)
        return cls(socket, zmq_context, endpoint)
