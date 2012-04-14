PotPy Documentation
===================

PotPy lets you build applications in a very flexible way. You design objects
based on your domain requirements, then compose them together using PotPy's
flexible routing system. PotPy enables you to:

* **Write simple, decoupled objects** that work together in various ways.
* **Easily test your objects**, by not imposing a rigid object construction
  paradigm.
* **Write WSGI components using TDD**, without having to deal with WSGI
  conventions except at the edges of the system.

PotPy was inspired by the `Raptor project
<https://github.com/garybernhardt/raptor>`_ from the Ruby world.

Installation
------------

::

    $ pip install potpy

For details, see the README file.

* `GitHub project page <https://github.com/dhain/potpy>`_
* `PotPy on PyPI <http://pypi.python.org/pypi/potpy>`_

Hello World Example
-------------------

.. literalinclude:: /../examples/wsgi.py
   :linenos:

More Examples
-------------

* `Todo List example <https://github.com/dhain/potpy/tree/master/examples/todo>`_

Overview
--------

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
value may be added to the context by the Route object. This allows later
callables in a route to access information produced by earlier ones, which
facilitates a very expressive style of application design.

A :class:`~potpy.router.Router` is an object that (typically) selects between
various Routes given some condition. The Router class itself is an abstract
base class, although the :mod:`potpy.wsgi` module provides two concrete
subclasses that route based on specific WSGI `environ` variables (:pep:`333`).
By subclassing the Router class and providing a
:meth:`~potpy.router.Router.match` method that selects based on something
specific to your problem domain, you can build powerful control flows between
the objects in your system with minimal effort.

The :mod:`potpy.template`, :mod:`potpy.wsgi`, and :mod:`potpy.configparser`
modules turn PotPy into a flexible HTTP request routing system.
:class:`~potpy.template.Template` objects allow string matching with parameter
extraction, and the reverse -- filling parameters into a string from a mapping.
The :class:`potpy.wsgi.PathRouter` class utilizes these templates to make
URL-based routing convenient and easy. The :mod:`~potpy.configparser` module
enables you to specify a web application's URL layout in a simple declarative
syntax, while being flexible enough to let you specify which HTTP methods (eg.
`GET`, `POST`, etc.) your domain objects should handle, and exception handlers.


Module Listing
==============

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
