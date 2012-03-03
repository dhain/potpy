import re
import sys
from . import urltemplate


class Route(list):
    class Stop(Exception):
        pass

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
            except self.Stop:
                break
            if name:
                context[name] = result
        return result


class Router(list):
    def __init__(self, it=()):
        super(Router, self).__init__(it)
        self._match_cache = {}

    def _match_regex(self, match):
        try:
            rx = self._match_cache[match]
        except KeyError:
            rx = self._match_cache[match] = re.compile(
                urltemplate.make_regex(match))
        return rx

    def urlmatch(self, match, url):
        regex = self._match_regex(match)
        return regex.match(url)

    def __call__(self, context, path):
        for name, match, obj in self:
            m = self.urlmatch(match, path)
            if m:
                context.update(m.groupdict())
                return context.inject(obj)
