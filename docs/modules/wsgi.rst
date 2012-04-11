:mod:`potpy.wsgi` -- WSGI module
================================

.. automodule:: potpy.wsgi

Module Contents
---------------

.. autoclass:: PathRouter
    :show-inheritance:
    :members:
    :exclude-members: add, reverse

    .. automethod:: add([name,] template, handler)
    .. automethod:: reverse(name, \*\*kwargs)

.. autoclass:: MethodRouter
    :show-inheritance:
    :members:

.. autoclass:: App
    :members: __call__
