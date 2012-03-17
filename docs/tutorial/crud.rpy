# -*- mode: python; coding: utf-8 -*-
from twisted.web.resource import IResource

from txyoga import Collection, Element


class Employee(Element):
    """
    An employee at a company.
    """
    exposedAttributes = "name", "title"
    updatableAttributes = "salary", "title"

    def __init__(self, name, title, salary):
        self.name = name
        self.title = title
        self.salary = salary



class Company(Collection):
    """
    A company.
    """
    defaultElementClass = Employee
    exposedElementAttributes = "name",



startup = Company()

startup.add(Employee(u"lvh", u"CEO", 10000))
startup.add(Employee(u"asook", u"Junior intern", 1))

resource = IResource(startup)
