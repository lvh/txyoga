# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txyoga authors. See the LICENSE file for details.
"""
Mixins that make a test case use some layout when building a collection.
"""
from txyoga import base
from txyoga.test.util import _BaseCollectionTest



class Cookie(base.Element):
    """
    A cookie, typically contained in a jar.
    """
    def __init__(self, name):
        self.name = name



class Jar(base.Collection):
    """
    A cookie jar.
    """



class SimpleCollectionMixin(_BaseCollectionTest):
    collectionClass = Jar
    elementClass = Cookie
    elementArgs = [("chocolateChip",),
                   ("butter",),
                   ("gingerbread",)]



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



class PaginatedCollectionMixin(_BaseCollectionTest):
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



class PartialExposureMixin(_BaseCollectionTest):
    """
    A collection test mixin with a collection that partially exposes its
    elements.
    """
    collectionClass = Zoo
    elementClass = Animal
    elementArgs = [("Pumbaa", "warthog", "bugs"),
                   ("Simba", "lion", "warthogs"),
                   ("Timon", "meerkat", "bugs")]



class World(base.Collection):
    """
    A dystopic world, consisting of a small number of superstates.
    """
    exposedAttributes = "name",



class State(base.Element):
    """
    A state.
    """
    exposedAttributes = "name",
    children = "ministries",

    def __init__(self, name, ministries):
        super(State, self).__init__()
        self.name = name
        self.ministries = ministries



class Ministries(base.Collection):
    """
    A collection of the important organisations within a state.
    """
    exposedElementAttributes = "name",



class Ministry(base.Element):
    """
    A unit of operation of the state machinery.
    """
    exposedAttributes = "name",

    def __init__(self, name):
        super(Ministry, self).__init__()
        self.name = name



ministryNames = ["Miniluv", "Minipax", "Miniplenty", "Minitrue"]



class ElementChildMixin(_BaseCollectionTest):
    """
    A collection test mixin that provides access to elements with children.
    """
    oceaniaMinistries = Ministries()

    for ministryName in ministryNames:
        ministry = Ministry(ministryName)
        oceaniaMinistries.add(ministry)

    collectionClass = World
    elementClass = State
    elementArgs = [("oceania", oceaniaMinistries),
                   ("eurasia", Ministries()),
                   ("eastasia", Ministries())]



class Bikeshed(base.Element):
    """
    A bikeshed.

    The color can be changed liberally, but the functional properties of the
    bikeshed, such as the name and the maximum occupancy, are immutable.
    """
    exposedAttributes = "color", "maximumOccupancy"
    updatableAttributes = "color",

    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.maximumOccupancy = 100



class SoftwareProject(base.Collection):
    """
    A software project that consists of a bunch of bikesheds.
    """
    defaultElementClass = Bikeshed



class UpdatableCollectionMixin(_BaseCollectionTest):
    """
    A mixin for tests that require an updatable collection.
    """
    collectionClass = SoftwareProject
    elementClass = Bikeshed
    elementArgs = [("north", "red"),
                   ("east", "blue"),
                   ("south", "green"),
                   ("west", "yellow")]



class TaggedCookie(Cookie):
    """
    A cookie that exposes its name.
    """
    exposedAttributes = "name",



class Replicator(Jar):
    """
    A futuristic cookie jar that produces new cookies.
    """
    defaultElementClass = TaggedCookie



class ElementCreationMixin(_BaseCollectionTest):
    """
    A mixin for tests that try to create new elements in a collection.
    """
    collectionClass = Replicator
    elementClass = TaggedCookie
    elementArgs = []

    newElementName = "shortbread"
    newElementState = {"name": newElementName}
