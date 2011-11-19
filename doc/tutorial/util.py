# -*- coding: utf-8 -*-
"""
Utilties for making HTTP requests to txyoga tutorial examples.
"""
import functools
import httplib
import urllib


def buildPath(*parts):
    return "/" + "/".join(urllib.quote(part) for part in parts)


class Example(object):
    """
    A txyoga tutorial example.
    """
    def __init__(self, exampleName, host="localhost:8080"):
        self._makeConnection = functools.partial(httplib.HTTPConnection, host)
        self._buildPath = functools.partial(buildPath, exampleName + ".rpy")


    def _makeRequest(self, method, body, headers, *parts):
        """
        Makes an HTTP request to the tutorial example.
        """
        path = self._buildPath(*parts)
        connection = self._makeConnection()
        connection.request(method, path, body, headers)
        return connection.getresponse()


    def get(self, *parts):
        """
        Gets a particular collection or element.
        """
        return self._makeRequest("GET", "", {}, *parts)


    def delete(self, *parts):
        """
        Deletes a particular element.
        """
        return self._makeRequest("DELETE", "", {}, *parts)


    def put(self, body, headers, *parts):
        """
        Puts a particular element in a collection.
        """
        return self._makeRequest("PUT", body, headers, *parts)
