# -*- coding: utf-8 -*-
"""
Utilties for making HTTP requests to txYoga tutorial examples.
"""
import functools
import httplib
import urllib


def buildPath(*parts):
    return "/" + "/".join(urllib.quote(part) for part in parts)


class Example(object):
    """
    A txYoga tutorial example.
    """
    def __init__(self, exampleName, host="localhost:8080"):
        self._connection =  httplib.HTTPConnection(host)
        self._buildPath = functools.partial(buildPath, exampleName + ".rpy")


    def get(self, *parts):
        path = self._buildPath(*parts)
        self._connection.request("GET", path)
        return self._connection.getresponse()
