#!/usr/bin/env python
# encoding: utf-8

import eventlet
from eventlet.green import socket
import msgpack
from hashlib import sha1
import os

def rpccall(func):
    def _rpccall(self, dest, *args, **kw):
        def _udpcall(conn, data, dest):
            conn.sendto(data, dest)
            self.debug("data send to dest")
            with eventlet.Timeout(3, True):
                return conn.recvfrom(65500)

        self.debug("rpccall function %s" % func.__name__)
        self.debug("rpccall dest: %s:%d" % dest)
        msgid = sha1(os.urandom(32)).digest()
        c = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        data = msgid + msgpack.packb([func.__name__, args, kw])
        self.pile.spawn(_udpcall, c, data, dest)
        result, _ = self.pile.next()
        self.debug("rcpcall returned")
        c.close()
        if msgid == result[0:20]:
            return msgpack.unpackb(result[20:], encoding='utf-8', use_list=False)
    return _rpccall

def rpccall_n(timeout=3):
    def decorator(func):
        def _rpccall_n(self, destlist, *args, **kw):
            def _udpcall(dest):
                msgid = sha1(os.urandom(32)).digest()
                c = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                data = msgid + msgpack.packb([func.__name__, args, kw])
                c.sendto(data, dest)
                res = None
                with eventlet.Timeout(timeout, False):
                    res, _ = c.recvfrom(65500)
                    if msgid != res[0:20]:
                        res = None
                    else:
                        res = msgpack.unpackb(res[20:],
                                              encoding='utf-8',
                                              use_list=False)
                c.close()
                return (res, dest)
            for dest in destlist:
                self.pile.spawn(_udpcall, dest)
            return self.pile
        return _rpccall_n
    return decorator

class RPCServer(object):
    def __init__(self, DEBUG=False):
        pool = eventlet.GreenPool()
        self.pile = eventlet.GreenPile(pool)
        self.DEBUG = DEBUG

    def call_dispatch(self, datagram, dest, sock):
        self.debug("call dispatch")
        msgid = datagram[0:20]
        data = msgpack.unpackb(datagram[20:], encoding='utf-8', use_list=False)
        funcname, args, kw = data
        f = getattr(self, "rpc_%s" % funcname, None)
        if f is not None and callable(f):
            self.debug("call function %s" % funcname)
            result = f(*args, **kw)
            self.debug("finished call function %s" % funcname)
            txdata = msgid + msgpack.packb(result)
            self.debug("send data to %s:%d" % dest)
            sock.sendto(txdata, dest)
        else:
            self.debug("function %s is not callable " % funcname)

    def debug(self, msg):
        if self.DEBUG:
            print(msg)

    def run(self, bindaddr):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(bindaddr)
        self.debug("bind to addr %s:%d" % bindaddr)
        while True:
            recvData, source = sock.recvfrom(1024)
            self.debug("receive msg from %s:%d" % source)
            eventlet.spawn_n(self.call_dispatch, recvData, source, sock)
