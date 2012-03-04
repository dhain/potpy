import re
from .router import Router
from . import urltemplate


class PathRouter(Router):
    def __init__(self, *routes):
        self._templates = {}
        self._match_cache = {}
        super(PathRouter, self).__init__(*routes)

    def add(self, *args):
        if len(args) > 2:
            name, match = args[:2]
            if not isinstance(match, basestring):
                raise TypeError(
                    'match argument for named routes must be strings')
            args = args[2:]
            self._templates[name] = urltemplate.make_fill_template(match)
        else:
            match = args[0]
            args = args[1:]
        if not isinstance(match, re._pattern_type):
            match = re.compile(urltemplate.make_regex(match))
        super(PathRouter, self).add(match, *args)

    def match(self, match, path):
        m = match.match(path)
        return m and m.groupdict()

    def __call__(self, context, path):
        return super(PathRouter, self).__call__(context, path)

    def reverse(self, *args, **kwargs):
        (name,) = args
        return self._templates[name] % kwargs


class MethodRouter(Router):
    def match(self, match, method):
        if isinstance(match, basestring):
            return {} if method == match else None
        return {} if method in match else None

    def __call__(self, context, method):
        return super(MethodRouter, self).__call__(context, method)
