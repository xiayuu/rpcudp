#!/usr/bin/env python
# encoding: utf-8

from setuptools import setup, find_packages

setup(
    name="rpcudp",
    version="v0.1",
    description="RPC via UDP",
    author="xiayu",
    license="APACHE",
    url="",
    packages=find_packages(),
    requires=['eventlet'],
    install_requires=['eventlet'])
