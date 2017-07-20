#!/usr/bin/env python
# encoding: utf-8

import eventlet
from eventlet.green import socket
import msgpack
from hashlib import sha1
import os

def udpcall(conn, data, dest):
    conn.sendto(data, dest)
    return conn.recvfrom(1024)

def rpccall(func):
    def _rpccall(self, dest, *args, **kw):
        msgid = sha1(os.urandom(32)).digest()
        c = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        data = msgid + msgpack.packb([func.__name__, args, kw])
        self.pile.spawn(udpcall, c, data, dest)
        result, _ = self.pile.next()
        c.close()
        if msgid == result[0:20]:
            return msgpack.unpackb(result[20:], encoding='utf-8')
    return _rpccall


class RPCServer(object):
    def __init__(self):
        pool = eventlet.GreenPool()
        self.pile = eventlet.GreenPile(pool)

    def call_dispatch(self, datagram, dest, sock):
        msgid = datagram[0:20]
        data = msgpack.unpackb(datagram[20:], encoding='utf-8')
        funcname, args, kw = data
        f = getattr(self, "rpc_%s" % funcname, None)
        if f is not None and callable(f):
            result = f(*args, **kw)
            txdata = msgid + msgpack.packb(result)
            sock.sendto(txdata, dest)

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('0.0.0.0', 8080))
        while True:
            recvData, source = sock.recvfrom(1024)
            eventlet.spawn_n(self.call_dispatch, recvData, source, sock)
