# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txYoga authors. See the LICENSE file for details.
"""
Mixins that make a test case use some layout when building a collection.
"""
from txyoga import base
from txyoga.test.util import _BaseCollectionTest


class Zoo(base.Collection):
    """
    A zoo, which contains a bunch of animals.

    Exposes the name and species of an animal, but not its diet.
    """
    exposedElementAttributes = "name", "species"

    pageSize = 3
    maxPageSize = 5



class Animal(base.Element):
    """
    An animal in captivity.
    """
    exposedAttributes = "name", "species", "diet"

    def __init__(self, name, species, diet):
        self.name = name
        self.species = species
        self.diet = diet



class _PaginatedCollectionMixin(_BaseCollectionTest):
    """
    A collection test mixin that produces a paginated collection.
    """
    collectionClass = Zoo
    elementClass = Animal
    elementArgs = [("Pumbaa", "warthog", "bugs"),
                   ("Simba", "lion", "warthogs"),
                   ("Timon", "meerkat", "bugs"),
                   ("Rafiki", "mandrill", "strange yellow fruit"),
                   ("Zazu", "hornbill", "nondescript berries"),
                   ("Shenzi", "hyena", "lion cubs"),
                   ("Banzai", "hyena", "lion cubs"),
                   ("Ed", "hyena", "whatever he can get, really")]



class _PartlyExposingCollectionMixin(_BaseCollectionTest):
    collectionClass = Zoo
    elementClass = Animal
    elementArgs = [("Pumbaa", "warthog", "bugs"),
                   ("Simba", "lion", "warthogs"),
                   ("Timon", "meerkat", "bugs")]



class SoftwareProject(base.Collection):
    """
    A software project that consists of a bunch of bikesheds.
    """



class Bikeshed(base.Element):
    """
    A bikeshed.

    The color can be changed liberally, but the functional properties of the
    bikeshed, such as the name and the maximum occupancy, are immutable.
    """
    exposedAttributes = "name", "color", "maximumOccupancy"
    updatableAttributes = "color",

    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.maximumOccupancy = 100



class _UpdatableCollectionMixin(_BaseCollectionTest):
    """
    A mixin for tests that require an updatable collection.
    """
    collectionClass = SoftwareProject
    elementClass = Bikeshed
    elementArgs = [("north", "red"),
                   ("east", "blue"),
                   ("south", "green"),
                   ("west", "yellow")]



