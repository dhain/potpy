import sys


class Route(object):
    """
    A list of handlers which can be called with a
    :class:`~potpy.context.Context`.

    Initializer can also be called with a single (non-tuple) iterable of
    handlers. Each handler item is either a callable or a tuple: ``(handler,
    name, exception_handlers)`` -- see :meth:`add` for details of this tuple.
    """

    class Stop(Exception):
        """
        Raise this exception to jump out of a route early.

        If an argument is provided, it will be used as the route return value,
        otherwise the return value of the previous handler will be returned.

        Example::
            >>> from potpy.context import Context

            >>> def stopper():
            ...     raise Route.Stop('stops here')
            ...
            >>> def foobar():
            ...     return 'never gets run'
            ...
            >>> route = Route(stopper, foobar)
            >>> route(Context())
            'stops here'
        """
        NoValue = type('NoValue', (), {})
        def __init__(self, value=NoValue):
            self.value = value

    class previous(object):
        """
        Refer to result of previous handler in route.

        Example::

            >>> from potpy.context import Context

            >>> class MyClass:
            ...    def foo(self):
            ...        return 42
            ...
            >>> route = Route(
            ...     MyClass,            # instantiate MyClass
            ...     Route.previous.foo  # refer to foo attribute of instance
            ... )
            >>> route(Context())
            42
        """
        class __metaclass__(type):
            def __getattr__(cls, name):
                return cls(name)

        def __init__(self, name):
            self.name = name

        def __getattr__(self, name):
            return type(self)('.'.join((self.name, name)))

        def __call__(self, obj):
            for name in self.name.split('.'):
                obj = getattr(obj, name)
            return obj

    class context(object):
        """
        Refer to a context item in route.

        Example::

            >>> from potpy.context import Context

            >>> class MyClass:
            ...     def foo(self):
            ...         return 42
            ...
            >>> route = Route(
            ...     Route.context.inst.foo  # refer to ctx['inst'].foo
            ... )
            >>> route(Context(inst=MyClass()))
            42
        """
        class __metaclass__(type):
            def __getitem__(cls, key):
                return cls(key)
            __getattr__ = __getitem__

        def __init__(self, key, name=None):
            self.key = key
            self.name = name

        def __getattr__(self, name):
            if self.name:
                name = '.'.join((self.name, name))
            return type(self)(self.key, name)

        def __call__(self, context):
            obj = context[self.key]
            if self.name:
                for name in self.name.split('.'):
                    obj = getattr(obj, name)
            return obj

    def __init__(self, *handlers):
        self.route = []
        if len(handlers) == 1 and not isinstance(handlers[0], tuple):
            try:
                handlers = iter(handlers[0])
            except TypeError:
                pass
        for handler in handlers:
            if isinstance(handler, tuple):
                self.add(*handler)
            else:
                self.add(handler)

    def add(self, handler, name=None, exception_handlers=()):
        """Add a handler to the route.

        :param handler: The "handler" callable to add.
        :param name: Optional. When specified, the return value of this
            handler will be added to the context under ``name``.
        :param exception_handlers: Optional. A list of ``(types, handler)``
            tuples, where ``types`` is an exception type (or tuple of types)
            to handle, and ``handler`` is a callable. See below for example.

        **Exception Handlers**

        When an exception occurs in a handler, ``exc_info`` will be
        temporarily added to the context and the list of exception handlers
        will be checked for an appropriate handler. If no handler can be
        found, the exception will be re-raised to the caller of the route.

        If an appropriate exception handler is found, it will be called (the
        context will be injected, so handlers may take an ``exc_info``
        argument), and its return value will be used in place of the original
        handler's return value.

        Examples:

            >>> from potpy.context import Context

            >>> route = Route()
            >>> route.add(lambda: {}['foo'], exception_handlers=[
            ...     (KeyError, lambda: 'bar')
            ... ])
            >>> route(Context())
            'bar'

            >>> def read_line_from_file():
            ...     raise IOError()     # simulate a failed read
            ...
            >>> def retry_read():
            ...     return 'success!'   # simulate retrying the read
            ...
            >>> def process_line(line):
            ...     return line.upper()
            ...
            >>> route = Route()
            >>> route.add(read_line_from_file, 'line', [
            ...     # return value will be added to context as 'line'
            ...     ((OSError, IOError), retry_read)
            ... ])
            >>> route.add(process_line)
            >>> route(Context())
            'SUCCESS!'

            >>> route = Route()
            >>> route.add(lambda: {}['foo'], exception_handlers=[
            ...     (IndexError, lambda: 'bar') # does not handle KeyError
            ... ])
            >>> route(Context())    # so exception will be re-raised here
            Traceback (most recent call last):
                ...
            KeyError: 'foo'
        """
        self.route.append((name, handler, exception_handlers))

    def __call__(self, context):
        """Call the handlers in the route, in order,  with the given context."""
        result = None
        for name, handler, exception_handlers in self.route:
            if handler is self.context:
                raise TypeError("can't refer to context directly")
            elif isinstance(handler, self.context):
                handler = handler(context)
            elif handler is self.previous:
                handler = result
            elif isinstance(handler, self.previous):
                handler = handler(result)
            try:
                try:
                    result = context.inject(handler)
                except Exception:
                    context['exc_info'] = sys.exc_info()
                    exc_type = sys.exc_info()[0]
                    try:
                        for types, exc_handler in exception_handlers:
                            if issubclass(exc_type, types):
                                result = context.inject(exc_handler)
                                break
                        else:
                            raise
                    finally:
                        del context['exc_info']
            except self.Stop, stop:
                if stop.value is not stop.NoValue:
                    result = stop.value
                break
            if name:
                context[name] = result
        return result


class Router(object):
    """
    Routes objects to handlers via a :meth:`match` method.

    When called with a :class:`~potpy.context.Context` and an object, that
    object will be checked against each registered handler for a match. When a
    matching handler is found, the context is updated with the result of the
    :meth:`match` method, and the handler is called with the context.

    Handlers are wrapped in :class:`Route` objects, causing the context to be
    injected into the call. You may also add Route objects directly.

    The :meth:`match` method of this class is unimplemented. You must subclass
    it and provide an appropriate match method to define a Router. See
    :class:`potpy.wsgi.PathRouter` and :class:`potpy.wsgi.MethodRouter` for
    example subclasses.
    """
    class NoRoute(Exception):
        """
        Raised when no route matches the given object.
        """
        pass

    def __init__(self, *routes):
        self.routes = []
        for route in routes:
            self.add(*route)

    def add(self, match, handler):
        """Register a handler with the Router.

        :param match: The first argument passed to the :meth:`match` method
            when checking against this handler.
        :param handler: A callable or :class:`Route` instance that will handle
            matching calls. If not a Route instance, will be wrapped in one.
        """
        self.routes.append((match, (
            Route(handler) if not isinstance(handler, Route)
            else handler
        )))

    def __call__(self, context, obj):
        """Route the given object to a matching handler.

        :param context: The :class:`~potpy.context.Context` object used when
            calling the matching handler.
        :param obj: The object to match against.
        """
        for match, route in self.routes:
            m = self.match(match, obj)
            if m is not None:
                context.update(m)
                return route(context)
        raise self.NoRoute(obj)

    def match(self, match, obj):
        """Check for a match.

        This method implements the routing logic of the Router. Handlers are
        registered with a ``match`` argument, which will be passed to this
        method when checking against that handler. When the Router is called
        with a context and an object, it will iterate over its list of
        registered handlers, passing the corresponding ``match`` argument and
        the object to this method once for each, until a match
        is found. If this method returns a :class:`dict`, it signifies that
        the object matched against the current handler, and the context is
        updated with the returned dict. To signify a non-match, this method
        returns ``None``, and iteration continues.

        .. note::

            This method is unimplemented in the base class. See
            :meth:`potpy.wsgi.MethodRouter.match` for a concrete example.

        :param match: The ``match`` argument corresponding to a handler
            registered with :meth:`add`.
        :param obj: The object to match against.
        :returns: A :class:`dict` or ``None``.
        """
        raise NotImplementedError()
