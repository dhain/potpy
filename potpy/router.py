import sys


class Route(object):
    class Stop(Exception):
        NoValue = type('NoValue', (), {})
        def __init__(self, value=NoValue):
            self.value = value

    class previous(object):
        def __init__(self, name):
            self.name = name

        class __metaclass__(type):
            def __getattr__(cls, name):
                return cls(name)

        def __getattr__(self, name):
            return type(self)('.'.join((self.name, name)))

        def __call__(self, obj):
            for name in self.name.split('.'):
                obj = getattr(obj, name)
            return obj

    def __init__(self, *route):
        self.route = []
        if len(route) == 1 and not isinstance(route[0], tuple):
            try:
                route = iter(route[0])
            except TypeError:
                pass
        for handler in route:
            if isinstance(handler, tuple):
                self.add(*handler)
            else:
                self.add(handler)

    def add(self, handler, name=None, exception_handlers=()):
        self.route.append((name, handler, exception_handlers))

    def __call__(self, context):
        result = None
        for name, handler, exception_handlers in self.route:
            if handler is self.previous:
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
    class NoRoute(Exception):
        pass

    def __init__(self, *routes):
        self.routes = []
        for route in routes:
            self.add(*route)

    def add(self, match, handler):
        self.routes.append((match, (
            Route(handler) if not isinstance(handler, Route)
            else handler
        )))

    def __call__(self, context, obj):
        for match, route in self.routes:
            m = self.match(match, obj)
            if m is not None:
                context.update(m)
                return route(context)
        raise self.NoRoute(obj)
