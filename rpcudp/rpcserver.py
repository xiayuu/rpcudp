#!/usr/bin/env python
# encoding: utf-8

import eventlet
from eventlet.green import socket
import msgpack
from hashlib import sha1
import os

def rpccall(func):
    def _rpccall(self, dest, *args, **kw):
        def _udpcall(data, dest):
            try:
                conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                conn.sendto(data, dest)
                with eventlet.Timeout(3, True):
                    result, source = conn.recvfrom(65500)
                    conn.close()
                    if source != dest:
                        self.debug("WARING:get msg from another host%s" % str(source))
                    return result
            except Exception, e:
                self.debug("RPCEXCEPT:%s" % str(e))
                return ""

        self.debug("%s:c:call:%s:%s:%s" % (func.__name__, dest, str(args), str(kw)))
        msgid = sha1(os.urandom(32)).digest()
        data = msgid + msgpack.packb([func.__name__, args, kw])
        result = eventlet.spawn(_udpcall, data, dest).wait()
        self.debug("%s:c:return:%s:%s" % (func.__name__, str(result), str(dest)))
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
                try:
                    c.sendto(data, dest)
                    res = None
                    with eventlet.Timeout(timeout, False):
                        res, source = c.recvfrom(65500)
                        self.debug("%s:c:return:%s:%s" % (func.__name__, str(res), str(source)))
                        if msgid != res[0:20]:
                            res = None
                        else:
                            res = msgpack.unpackb(res[20:],
                                                encoding='utf-8',
                                                use_list=False)
                    c.close()
                except Exception, e:
                    self.debug("RPCEXCEPT:%s" % str(e))
                    res = None

                return (res, dest)
            pile = eventlet.greenpool.GreenPile()
            for dest in destlist:
                self.debug("%s:c:call:%s:%s:%s" % (func.__name__, dest, str(args), str(kw)))
                pile.spawn(_udpcall, dest)
            return pile
        return _rpccall_n
    return decorator

class RPCServer(object):
    def __init__(self, DEBUG=False):
        self.DEBUG = DEBUG

    def call_dispatch(self, datagram, dest, sock):
        msgid = datagram[0:20]
        data = msgpack.unpackb(datagram[20:], encoding='utf-8', use_list=False)
        funcname, args, kw = data
        f = getattr(self, "rpc_%s" % funcname, None)
        if f is not None and callable(f):
            self.debug("%s:s:call:%s:%s" % (funcname, str(args), str(kw)))
            result = f(*args, **kw)
            self.debug("%s:s:return:%s" % (funcname, str(result)))
            txdata = msgid + msgpack.packb(result)
            sock.sendto(txdata, dest)
            self.debug("%s:s:rpcres:%s" % (funcname, str(dest)))
        else:
            self.debug("%s:s:notexist" % funcname)

    def debug(self, msg):
        if self.DEBUG:
            print(msg)

    def run(self, bindaddr):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(bindaddr)
        while True:
            recvData, source = sock.recvfrom(65500)
            eventlet.spawn_n(self.call_dispatch, recvData, source, sock)
