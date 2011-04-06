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

    The original header is also returned in that list.
    """
    fuzzed = [header]

    for sep, fuzzSeps in fuzzingParameters.iteritems():
        fuzzed += [fuzzSep.join(header.split(sep)) for fuzzSep in fuzzSeps]

    fuzzed.append("%s." % (header,))

    return fuzzed



class AcceptHeaderParsingTest(TestCase):
    def _test_parse(self, headerValue, expected):
        for fuzzedHeader in fuzzHeader(headerValue):
            parsed = _parseAccept(fuzzedHeader)
            self.assertEqual(parsed, expected)


    def test_singleElement_noParameters(self):
        self._test_parse("text/html", [("text/html", {})])


    def test_singleElement_oneParameter(self):
        self._test_parse("text/html;q=0.5",
                         [("text/html", {"q":"0.5"})])


    def test_singleElement_manyParameters(self):
        self._test_parse("text/html;q=0.5;r=0.3",
                         [("text/html", {"q": "0.5", "r": "0.3"})])


    def test_manyElements_noParameters(self):
        self._test_parse("text/html,text/plain",
                         [("text/html", {}), ("text/plain", {})])


    def test_manyElements_oneParameter(self):
        self._test_parse("text/html;q=0.5,text/plain;r=0.3",
                         [("text/html", {"q": "0.5"}),
                          ("text/plain", {"r": "0.3"})])


    def test_manyElements_manyParameters(self):
        self._test_parse("text/html;q=0.5;r=0.3,text/plain;q=0.5;r=0.3",
                         [("text/html", {"q": "0.5", "r": "0.3"}),
                          ("text/plain", {"q": "0.5", "r": "0.3"})])


    def test_manyElements_mixedParameters(self):
        self._test_parse("text/html;q=0.5;r=0.3,text/plain",
                         [("text/html", {"q": "0.5", "r": "0.3"}),
                          ("text/plain", {})])
