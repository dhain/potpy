from .router import Router
from .template import Template


class PathRouter(Router):
    def __init__(self, *routes):
        self._templates = {}
        super(PathRouter, self).__init__(*routes)

    def add(self, *args):
        if len(args) > 2:
            name, template = args[:2]
            args = args[2:]
        else:
            name = None
            template = args[0]
            args = args[1:]
        if not isinstance(template, Template):
            template = Template(template)
        if name:
            self._templates[name] = template
        super(PathRouter, self).add(template, *args)

    def match(self, template, path):
        m = template.regex.match(path)
        return m and m.groupdict()

    def __call__(self, context, path):
        return super(PathRouter, self).__call__(context, path)

    def reverse(self, *args, **kwargs):
        (name,) = args
        return self._templates[name].fill(**kwargs)


class MethodRouter(Router):
    def match(self, match, method):
        if isinstance(match, basestring):
            return {} if method == match else None
        return {} if method in match else None

    def __call__(self, context, method):
        return super(MethodRouter, self).__call__(context, method)