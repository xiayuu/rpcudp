#!/usr/bin/env python
# encoding: utf-8
from rpcudp.rpcserver import RPCServer
from rpcudp.rpcserver import rpccall

class Testserver(RPCServer):
    @rpccall
    def ping(self, dest, i, j=0):
        pass

    def rpc_ping(self, i, j=0):
        return "Pong"+str(i+j)


server = Testserver()
i = 0
while True:
    i=i+1
    result = server.ping(('127.0.0.1', 8080), i, j=20)
    print(result)
