import importlib

from x527.tinyrpc.protocols.jsonrpc import *


class PluginServer(object):
    def __init__(self):
        self.sequence = None
        try:
            self.plugin = importlib.import_module('fctplugin')
        except ImportError:
            self.plugin = None

    @staticmethod
    def respond(result):
        req = JSONRPCRequest()
        req.unique_id = 1
        return req.respond(result)

    @staticmethod
    def error_respond(error_msg):
        error = JSONRPCPluginError(error_msg)
        req = JSONRPCRequest()
        req.unique_id = 1
        return req.error_respond(error)

    def call(self, test):
        if self.plugin is None:
            return self.error_respond('No plugin was imported')
        try:
            func = getattr(self.plugin, test.function)
            test_dict = test._to_dict()
            result = func(test_dict['params'], test.unit, test.timeout, self.sequence)
            return self.respond(result)
        except Exception as e:
            return self.error_respond(e.message)
