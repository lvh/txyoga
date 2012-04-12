# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txyoga authors. See the LICENSE file for details.
"""
Tests for the in-memory store.
"""
from twisted.trial import unittest

from txyoga.stores import memory
from txyoga.stores.test import tools


class MemoryStoreTest(tools.StoreTestMixin, unittest.TestCase):
	"""
	A test for the in-memory store.
	"""
	storeFactory = memory.MemoryStore
