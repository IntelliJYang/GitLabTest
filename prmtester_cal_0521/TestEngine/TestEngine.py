#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import zmq

if not __package__:
    path = os.path.join(os.path.dirname(__file__), os.pardir)
    sys.path.insert(0, path)

import time
import datetime
import argparse
import traceback
from threading import Thread
from Configure import zmqports
from drivermanager import DriverManager
from Common.publisher import ZmqPublisher
from Common.rpc_server import RPCServerWrapper
from Common.tinyrpc.dispatch import RPCDispatcher
from Common.tinyrpc.server.HeartBeat import HB
from Common.tinyrpc.protocols.jsonrpc import *
from Configure import constant

VERSION = "%s %s" % ("0.0.2", "updated on 2018-10-22")


class TestEngine(RPCDispatcher):
    def __init__(self, publisher, site):
        super(TestEngine, self).__init__()
        self.site = site
        self.dispatcher = RPCDispatcher()
        self.publisher = publisher

    def register_modules_public_methods(self):
        """
        register all functions in func_table
        :return:
        """
        drviers = DriverManager(self.site, self.publisher)

        functions = drviers.functions
        if functions:
            for name, obj in functions.items():
                self.add_method(obj, name)
        drviers.init_all_drivers()

        # Gordon mark
        if not constant.SIMULATOR_FIXTURE:
            mix = drviers.get_module("mix")
            mix.reset_mix()



    def _dispatch(self, request):
        try:
            method = None
            result = None
            ret = None
            try:
                method = self.get_method(request.method)
            except JSONRPCMethodNotFoundError as e:
                return request.error_respond(e)

            if method:
                try:
                    result = method(*request.args, **request.kwargs)
                except Exception as e:
                    # an error occur within the method, return it
                    ret = request.error_respond(e)
                # respond with result
                ret = request.respond(result)
        except Exception as e:
            ret = request.error_respond(JSONRPCServerError(e.message + os.linesep + traceback.format_exc()))
        return ret


class TestEngineServer(Thread):
    def __init__(self, args):

        # get current site
        self.site = args.uut
        self.log_name = "testEngine_uut{0}.log".format(args.uut)
        super(TestEngineServer, self).__init__()

        ctx = zmq.Context()
        pub_endpoint = "tcp://*:" + str(zmqports.TEST_ENGINE_PUB + self.site)
        self.publisher = ZmqPublisher(ctx, pub_endpoint, "TestEngine_{}".format(self.site))

        # self.publish("TestEngine_{} pub at: {}".format(self.site, pub_endpoint))

        self.test_engine = TestEngine(self.publisher, self.site)
        time.sleep(0.2)
        self.server_wrapper = RPCServerWrapper(
            zmqports.TEST_ENGINE_PORT + self.site,
            self.publisher,
            ctx=ctx,
            dispatcher=self.test_engine
        )

        self.test_engine.register_modules_public_methods()

        self.hb = HB(5, self.publisher)
        self.hb.setDaemon(True)
        self.hb.start()
        self.rpc_server = self.server_wrapper.rpc_server

    def publish(self, msg):
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f") + "   " + str(msg) + "\n")
        self.publisher.publish(msg)

    def stop_engine(self):
        self.rpc_server.stopsever()

    def run(self):
        # print ('TestEngine starting now')
        # self.publish('TestEngine_{} Starting...'.format(self.site))
        try:
            self.rpc_server.serve_forever()
        except Exception as e:
            print e, traceback.format_exc()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='TestEngine')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s' + "'s version is " + VERSION)
    parser.add_argument('-u', '--uut', help='UUT slot number', type=int, default=0)
    parser.add_argument('-s', '--slots', help='Slots of the fixture', type=int, default=1)
    args = parser.parse_args()
    server = TestEngineServer(args)
    server.start()
