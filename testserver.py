#!/usr/bin/env python
# encoding: utf-8

from rpcudp.rpcserver import RPCServer
from rpcudp.rpcserver import rpccall

class Testserver(RPCServer):
    @rpccall
    def ping(self, dest):
        pass

    def rpc_ping(self, i, j=0):
        return "Pong" + str(i + j)


server = Testserver()
server.run()
