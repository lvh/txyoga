# -*- mode: Python; coding: utf-8 -*-

from twisted.web.resource import IResource

from txyoga import Collection, Element

# First, you define a collection. Collecations are containers for elements.
class Jar(Collection):
    """
    A jar, filled with many delicious cookies.
    """

# Secondly, you define an element. Elements go in containers.
class Cookie(Element):
    """
    A delicious cookie, with a name and some very basic nutritional facts.
    """
    def __init__(self, name, calories):
        self.name = name
        self.calories = calories

# We'll create a jar with some cookies in it to demonstrate it works.
jar = Jar()

jar.add(Cookie("chocolate chip", 80))
jar.add(Cookie("oreo", 160))
jar.add(Cookie("animal cracker", 250))
jar.add(Cookie("shortbread", 40))
jar.add(Cookie("sugar cookie", 65))
jar.add(Cookie("brownie", 112))

# Elements have an identifying attribute, similar to a primary keys
# from relational databases. You wouldn't be able to add another
# cookie with the same name. By default, this attribute is called
# ``name``. You can change it by setting the `identifyingAttribute`
# class attribute.

# Collections and elements can be adapted to resources, allowing them
# to be served by ``twisted.web``. Naming it ``resource`` in an
# ``rpy`` file is how you tell Twisted it's what you want to serve. If
# you don't really understand adaptation, the short explanation is
# that collections (in this case, the jar) aren't resources, but they
# can be turned into them. This means the two concerns (being a
# collection, and serving one over HTTP) are clearly separated in
# code.
resource = IResource(jar)
