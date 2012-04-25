# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txyoga authors. See the LICENSE file for details.
"""
Test collection pagination.
"""
import urlparse

from twisted.trial.unittest import TestCase

from txyoga.test import collections


class PaginationTest(collections.PaginatedCollectionMixin, TestCase):
    """
    Test collection pagination.
    """
    def test_firstPage(self):
        """
        Test the first page of a collection.

        It should be of the correct size, not have a link to a previous page
        (since there is none), and have a link to the next page (since there
        is one).
        """
        self.addElements()
        return self.getElements().addCallback(self._checkFirstPage)


    def _checkFirstPage(self, _):
        numResults = len(self.responseContent["results"])
        self.assertEqual(numResults, self.collectionClass.pageSize)

        self.assertEqual(self.responseContent["prev"], None)
        self.assertNotEqual(self.responseContent["next"], None)


    def test_followPages(self):
        """
        Tests that the entire collection can be accessed by walking down all
        the pages sequentially.
        """
        self.addElements()
        elementsPerPage = []

        pageSize = self.collectionClass.pageSize
        completePages, remaining = divmod(len(self.elementArgs), pageSize)
        pages = completePages + (1 if remaining else 0)

        def hashable(d):
            """
            A hashable version of an element.

            Used to check if an element has been seen before or not.
            """
            return tuple(sorted(d.itervalues()))

        def isLast(index):
            """
            Checks if this is the index of the last page.
            """
            return index == pages - 1

        def nextPageArgs():
            """
            Gets the args for getting the next page.
            """
            nextURL = self.responseContent["next"]
            rawQuery = urlparse.urlsplit(nextURL).query
            nextQuery = urlparse.parse_qsl(rawQuery)

            nextQueryKeys = [key for key, _ in nextQuery]
            for key in ("start", "stop"):
                self.assertEqual(nextQueryKeys.count(key), 1)

            return dict((k, [v]) for k, v in nextQuery)

        args = {}

        for index in xrange(pages):
            seenElements = set()
            elementsPerPage.append(seenElements)

            self.getElements(args)
            newElements = map(hashable, self.responseContent["results"])

            for element in newElements:
                # Test that the element is not duplicated in this page
                self.assertNotIn(element, seenElements)
                seenElements.add(element)

                # Test that the element is not duplicated in a previous page
                for previousPageElements in elementsPerPage[:-1]:
                    self.assertNotIn(element, previousPageElements)

            if not isLast(index):
                args = nextPageArgs()

        self.assertIdentical(self.responseContent["next"], None)
