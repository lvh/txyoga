==========
 Tutorial
==========

The tutorial consists of a bunch of progressively more complex
examples, showcasing more and more features as you go along. You
should have a decent working knowledge of Python and some idea of how
REST works. Some understanding of Twisted, particularly
``twisted.web`` and the way it does object publishing probably,
wouldn't hurt either; but that's mostly important for more advanced
use cases.

The tutorial examples themselves are ``rpy`` files. These are
basically Python files that expose a resource. This way, we can run
the tutorials with minimal boilerplate. You might want to do something
more sophisticated in a real application, but that's outside the scope
of this tutorial.

Each example starts with a short summary, followed by walking you
through the documented example code. Finally, you can try the example
out interactively.

Serving the tutorial examples
=============================

In order for the interactive examples to work, Twisted needs to be
serving the tutorial. There are two ways of doing that: using the
helper script, or invoking ``twistd`` manually. The former neatly
daemonizes ``twistd`` and cleans up the log file, but the latter makes
it a bit easier to see what's going on under the hood in terms of HTTP
requests.

The helper script will only work on \*nix-like environments. Windows
users should run ``twistd`` manually.

Using the helper script
-----------------------

From the ``doc`` directory::

     ./serveTutorial start

When you're done::

     ./serveTutorial stop

Running ``twistd`` manually
---------------------------

Run following command from the txyoga base directory::

    twistd -n web --path doc/tutorial

The ``-n`` flag makes ``twistd`` stay in the foreground instead of
daemonizing. The other arguments should be fairly
self-explanatory. You should see something similar to this::

    2011-04-17 21:29:28+0200 [-] Log opened.
    2011-04-17 21:29:28+0200 [-] twistd 11.0.0+r31557 (/usr/bin/python 2.7.1) starting up.
    2011-04-17 21:29:28+0200 [-] reactor class: twisted.internet.selectreactor.SelectReactor.
    2011-04-17 21:29:28+0200 [-] twisted.web.server.Site starting on 8080
    2011-04-17 21:29:28+0200 [-] Starting factory <twisted.web.server.Site instance at 0x2e7f3b0>

As you can see, Twisted is listening for connections on port 8080.

List of examples
================

.. toctree::

   accessing
   createdelete
