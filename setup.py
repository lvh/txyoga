#!/usr/bin/env python
from distutils.core import setup

setup(name='txyoga',
      version='0',
      description='REST toolkit for Twisted',
      url='https://github.com/lvh/txyoga',

      author='Laurens Van Houtven',
      author_email='_@lvh.cc',

      packages=['txyoga'],

      requires=['twisted'],

      license='ISC',
      classifiers=[
        "Development Status :: 3 - Alpha",
        "Framework :: Twisted",
        "License :: OSI Approved :: ISC License (ISCL)",
        "Topic :: Internet :: WWW/HTTP",
        ])
