PotPy Documentation
===================

PotPy is a generic routing apparatus. It allows you to develop applications by
composing your domain objects together into one or more "pipelines" for data to
flow along. Composition is accomplished with the idea of a
:class:`~potpy.context.Context` -- return values from handler functions along
these routes can be added to the context, enabling later handler functions to
access them.

The magic happens when a context is *injected* into a callable. PotPy inspects
the callable's signature, and pulls values out of the context by argument name.
For example:

    >>> from potpy.context import Context
    >>> def my_callable(foo, bar, baz='default'):
    ...     # do something cool
    ...     return 42
    ...
    >>> ctx = Context(foo='some value', bar='another value')
    >>> ctx.inject(my_callable)
    42

Building on the context, PotPy provides routes and routers. A
:class:`~potpy.router.Route` is a list of callables that you define which get
called in order. These callables are actually called by injecting a context, as
above. The same context is used to call subsequent callables in the route, and
these callables can either interact with the context directly, or their return
value may be added to the context by the Route object. This facilitates a very
expressive style of application design.

A :class:`~potpy.router.Router` is an object that (typically) selects between
various Routes given some condition. The Router class itself is an abstract
base class, although the :mod:`potpy.wsgi` module provides two concrete
subclasses that route based on specific WSGI `environ` variables (:pep:`333`).
By subclassing the Router class and providing a
:meth:`~potpy.router.Router.match` method that selects based on something
specific to your problem domain, you can build powerful control flows between
the objects in your system with minimal effort.


Module Listing
--------------

.. toctree::
   :maxdepth: 1

   modules/context
   modules/router
   modules/template
   modules/wsgi
   modules/configparser


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
