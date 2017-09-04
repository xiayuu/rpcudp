#!/usr/bin/env python
# encoding: utf-8
from rpcudp.rpcserver import RPCServer
from rpcudp.rpcserver import rpccall, rpccall_n

class Testserver(RPCServer):
    @rpccall_n(timeout=2)
    def ping(self, dest, i, j=0):
        pass

    @rpccall
    def pong(self, dest):
        pass

    def rpc_pong(self):
        print("call pong")
        return True

    def rpc_ping(self, i, j=0):
        self.pong()
        return "Pong"+str(i+j)


server = Testserver()
i = 0
while True:
    i=i+1
    result = server.ping([('192.168.1.4', 1002),('192.168.1.4', 1001), ('192.168.1.4', 1003)], i, j=20)
    print("wait for result")
    for res in result:
        print(res)
    break
