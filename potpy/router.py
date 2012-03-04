import re
import sys
from . import urltemplate


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
        self.routes = [
            (name, match, (
                Route(handler) if not isinstance(handler, Route)
                else handler
            )) for name, match, handler in routes
        ]

    def __call__(self, context, obj):
        for name, match, route in self.routes:
            m = self.match(match, obj)
            if m is not None:
                context.update(m)
                return route(context)
        raise self.NoRoute()


class PathRouter(Router):
    def __init__(self, *routes):
        super(PathRouter, self).__init__(*routes)
        self._match_cache = {}
        self._template_cache = {}

    def _match_regex(self, match):
        try:
            rx = self._match_cache[match]
        except KeyError:
            rx = self._match_cache[match] = re.compile(
                urltemplate.make_regex(match))
        return rx

    def _fill_template(self, route_name):
        try:
            template = self._template_cache[route_name]
        except KeyError:
            for name, match, handler in self.routes:
                if name != route_name:
                    continue
                template = self._template_cache[route_name] = \
                    urltemplate.make_fill_template(match)
                break
            else:
                raise
        return template

    def match(self, match, path):
        m = self._match_regex(match).match(path)
        return m and m.groupdict()

    def __call__(self, context, path):
        return super(PathRouter, self).__call__(context, path)

    def reverse(self, route_name, **kwargs):
        return self._fill_template(route_name) % kwargs


class MethodRouter(Router):
    def match(self, match, method):
        if isinstance(match, basestring):
            return {} if method == match else None
        return {} if method in match else None

    def __call__(self, context, method):
        return super(MethodRouter, self).__call__(context, method)
