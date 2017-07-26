#!/usr/bin/env python
# encoding: utf-8
from rpcudp.rpcserver import RPCServer
from rpcudp.rpcserver import rpccall

class Testserver(RPCServer):
    @rpccall
    def ping(self, dest, i, j=0):
        pass

    @rpccall
    def pong(self, dest):
        pass

    def rpc_pong(self):
        print("call pong")
        return True

    def rpc_ping(self, i, j=0):
        self.pong(('localhost', 1001))
        return "Pong"+str(i+j)


server = Testserver()
server.run(('localhost', 1001))
