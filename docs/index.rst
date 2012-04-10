PotPy Documentation
===================

At the heart of potpy are the concepts of routes and routers.

A :class:`~potpy.router.Route` is a list of "handlers" which get called in
order. Routes are called with a :class:`~potpy.context.Context` -- handlers are
called by injecting values from the context as arguments.

Each handler may have a name, in which case the result of that handler is
added to the context under that name.

Composing handlers with routes and contexts is very powerful, allowing you to
structure your program as one or more "pipelines" for data to flow along.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


Module Listing
--------------

.. toctree::
   :maxdepth: 1

   modules/context
   modules/router
   modules/template
   modules/wsgi
   modules/configparser
