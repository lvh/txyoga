"""
Twisted REST object publishing.
"""
from twisted.python.components import registerAdapter
from twisted.web.resource import IResource

from txyoga.interface import ICollection, IElement
from txyoga.resource import CollectionResource, ElementResource


registerAdapter(CollectionResource, ICollection, IResource)
registerAdapter(ElementResource, IElement, IResource)

