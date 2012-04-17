import setuptools

setuptools.setup(name='txyoga',
      version='0',
      description='REST toolkit for Twisted',
      url='https://github.com/lvh/txyoga',

      author='Laurens Van Houtven',
      author_email='_@lvh.cc',

      packages = setuptools.find_packages(),

      requires=['twisted'],

      license='ISC',
      classifiers=[
        "Development Status :: 3 - Alpha",
        "Framework :: Twisted",
        "License :: OSI Approved :: ISC License (ISCL)",
        "Topic :: Internet :: WWW/HTTP",
        ])
