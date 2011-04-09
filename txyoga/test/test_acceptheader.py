# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txYoga authors. See the LICENSE file for details.
"""
Tests for the parsing of Accept headers.
"""
from twisted.trial.unittest import TestCase

from txyoga.resource import _parseAccept


fuzzingParameters = {"=": [" =", "= ", " = "],
                     ",": [" ,", ", ", " , ", ",,", ",,,,,", " , ,,,   ,"],
                     ";": [" ;", "; ", " ; "]}


def fuzzHeader(header):
    """
    Fuzzes a reasonably-formed Accept header into a bunch of less reasonably
    formed headers that are still technically valid and should parse equally.

    The original header is also returned.
    """
    fuzzed = [header]

    for sep, fuzzSeps in fuzzingParameters.iteritems():
        fuzzed += [fuzzSep.join(header.split(sep)) for fuzzSep in fuzzSeps]

    fuzzed.append("%s." % (header,)) # dots at the end are allowed

    return fuzzed



class AcceptHeaderParsingTest(TestCase):
    """
    Test the parsing of Accept headers.
    """
    def _test_parse(self, headerValue, expected):
        """
        Tests a particular Accept header value. Also tests fuzzed versions of
        that header.
        """
        for fuzzedHeader in fuzzHeader(headerValue):
            parsed = _parseAccept(fuzzedHeader)
            self.assertEqual(parsed, expected)


    def test_oneElement_noParameters(self):
        """
        Tests an Accept header with one element that has no parameters.
        """
        self._test_parse("text/html", [("text/html", {})])


    def test_oneElement_oneParameter(self):
        """
        Tests an Accept header with one element that has one parameter.
        """
        self._test_parse("text/html;q=0.5",
                         [("text/html", {"q":"0.5"})])


    def test_oneElement_multipleParameters(self):
        """
        Tests an Accept header with one element that has multiple parameters.
        """
        self._test_parse("text/html;q=0.5;r=0.3",
                         [("text/html", {"q": "0.5", "r": "0.3"})])


    def test_multipleElements_noParameters(self):
        """
        Tests an Accept header with multiple elements that don't have any
        parameters.
        """
        self._test_parse("text/html,text/plain",
                         [("text/html", {}), ("text/plain", {})])


    def test_multipleElements_oneParameter(self):
        """
        Tests an Accept header with multiple elements that have one parameter.
        """
        self._test_parse("text/html;q=0.5,text/plain;r=0.3",
                         [("text/html", {"q": "0.5"}),
                          ("text/plain", {"r": "0.3"})])


    def test_multipleElements_multipleParameters(self):
        """
        Tests an Accept header with multiple elements that have multiple
        parameters.
        """
        self._test_parse("text/html;q=0.5;r=0.3,text/plain;q=0.5;r=0.3",
                         [("text/html", {"q": "0.5", "r": "0.3"}),
                          ("text/plain", {"q": "0.5", "r": "0.3"})])


    def test_multipleElements_mixedParameters(self):
        """
        Tests an Accept header with multiple elements that have a mixed number
        of parameters.
        """
        self._test_parse("text/html;q=0.5;r=0.3,text/plain",
                         [("text/html", {"q": "0.5", "r": "0.3"}),
                          ("text/plain", {})])
