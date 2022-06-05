#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import  # needed for zmq import
import six
import zmq
import time
from Common.tinyrpc import FCT_HEARTBEAT
from Common.tinyrpc.transports import ServerTransport
HEARTBEAT_INTERVAL = 0.5

DEFAULT_RPC_TIMEOUT = 500


class ZmqFixtureTransport(ServerTransport):
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



