import re
import sys
from . import urltemplate


class Route(list):
    class Stop(Exception):
        NoValue = type('NoValue', (), {})
        def __init__(self, value=NoValue):
            self.value = value

    def add(self, handler, name=None, exception_handlers=()):
        self.append((name, handler, exception_handlers))

    def __call__(self, context):
        result = None
        for name, handler, exception_handlers in self:
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


class Router(list):
    class NoRoute(Exception):
        pass

    def __call__(self, context, obj):
        for name, match, handler in self:
            m = self.match(match, obj)
            if m is not None:
                context.update(m)
                return context.inject(handler)
        raise self.NoRoute()


class UrlRouter(Router):
    def __init__(self, it=()):
        super(UrlRouter, self).__init__(it)
        self._match_cache = {}

    def _match_regex(self, match):
        try:
            rx = self._match_cache[match]
        except KeyError:
            rx = self._match_cache[match] = re.compile(
                urltemplate.make_regex(match))
        return rx

    def match(self, match, path):
        m = self._match_regex(match).match(path)
        return m and m.groupdict()

    def __call__(self, context, path):
        return super(UrlRouter, self).__call__(context, path)


class MethodRouter(Router):
    def match(self, match, method):
        if isinstance(match, basestring):
            return {} if method == match else None
        return {} if method in match else None

    def __call__(self, context, method):
        return super(MethodRouter, self).__call__(context, method)
