# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txyoga authors. See the LICENSE file for details.
"""
Tools for making store testing easy and fun!
"""
import functools

from twisted.internet import defer

from txyoga.test import collections
from txyoga.stores import exceptions


cookie = collections.Cookie(name="sugar")



class StoreTestMixin(object):
    """
    A mixin for store tests.
    """
    storeFactory = None

    @classmethod
    def part(cls, part):
        def getFunction(name):
            try:
                return getattr(part, name).im_func
            except AttributeError:
                return None

        setUp = getFunction("setUp")
        tearDown = getFunction("tearDown")

        testHelperNames = (n for n in vars(part) if n.startswith("_test"))
        for name in testHelperNames:
            setattr(cls, name, getFunction(name))

        testNames = (n for n in vars(part) if n.startswith("test_"))
        tests = (getattr(part, n).im_func for n in testNames)

        for test in tests:
            @functools.wraps(test)
            def decoratedTest(self, _test=test):
                def step(m):
                    if m is None:
                        return lambda result: None
                    else:
                        return lambda result: defer.maybeDeferred(m, self)

                return (step(setUp)(None)
                    .addCallback(step(_test))
                    .addCallback(step(tearDown)))

            setattr(cls, test.__name__, decoratedTest)


    def setUp(self):
        self.collection = collections.Jar()
        self.store = self.storeFactory()


    @defer.inlineCallbacks
    def test_roundtrip(self):
        yield self.store.add(self.collection, cookie)

        identifier = getattr(cookie, cookie.identifyingAttribute)
        gotCookie = yield self.store.get(self.collection, identifier)
        self.assertEqual(gotCookie.name, cookie.name)


    def test_getMissing(self):
        identifier = getattr(cookie, cookie.identifyingAttribute)
        d = self.store.get(self.collection, identifier)
        return self.assertFailure(d, exceptions.MissingElementError)


    def test_add(self):
        return self.store.add(self.collection, cookie)
    

    @defer.inlineCallbacks
    def test_addTwice(self):
        yield self.store.add(self.collection, cookie)
        d = self.store.add(self.collection, cookie)
        yield self.assertFailure(d, exceptions.DuplicateElementError)


    @defer.inlineCallbacks
    def test_remove(self):
        yield self.store.add(self.collection, cookie)
        yield self.store.remove(self.collection, cookie.name)
        d = self.store.get(self.collection, cookie.name)
        yield self.assertFailure(d, exceptions.MissingElementError)

    @defer.inlineCallbacks
    def test_removeTwice(self):
        yield self.store.add(self.collection, cookie)
        yield self.store.remove(self.collection, cookie.name)
        d = self.store.remove(self.collection, cookie.name)
        yield self.assertFailure(d, exceptions.MissingElementError)


    def test_removeFromNonexistentCollection(self):
        newJar = collections.Jar()
        d = self.store.remove(newJar, cookie.name)
        return self.assertFailure(d, exceptions.UnknownCollectionError)


    def test_removeNonexistent(self):
        d = self.store.remove(self.collection, cookie.name)
        return self.assertFailure(d, exceptions.MissingElementError)



@StoreTestMixin.part
class _StoreRangeQueryTestMixin(object):
    def setUp(self):
        self.collection = jar = collections.Jar()
        cookies = (collections.Cookie(str(i)) for i in xrange(50))
        return defer.gatherResults([self.store.add(jar, c) for c in cookies])


    def _testRangeQuery(self, start, stop, expectedIdentifiers):
        query = self.store.query
        def identifier(cookie):
            return getattr(cookie, cookie.identifyingAttribute)
        
        d = query(self.collection, start=start, stop=stop)

        @d.addCallback
        def checkNumberOfCookies(cookies):
            self.assertEqual(len(cookies), len(expectedIdentifiers))
            return cookies
        
        @d.addCallback
        def checkCookieIdentifiers(cookies):
            for cookie, expected in zip(cookies, expectedIdentifiers):
                self.assertEqual(identifier(cookie), expected)


    def test_emptyRange(self):
        return self._testRangeQuery(0, 0, "")

    
    def test_emptyRangeWithOffset(self):
        return self._testRangeQuery(10, 10, "")


    def test_oneElementRange(self):
        return self._testRangeQuery(0, 1, "0")


    def test_twoElementRange(self):
        return self._testRangeQuery(0, 2, "01")



