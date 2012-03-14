from .router import Router
from .template import Template
from .context import Context
from .util import rename_args


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

    def match(self, template, path_info):
        m = template.regex.match(path_info)
        return m and m.groupdict()

    __call__ = rename_args(Router.__call__, (
        'self', 'context', 'path_info'))

    def reverse(self, *args, **kwargs):
        (name,) = args
        return self._templates[name].fill(**kwargs)


class MethodRouter(Router):
    class MethodNotAllowed(Router.NoRoute):
        def __init__(self, allowed_methods, request_method):
            self.allowed_methods = allowed_methods
            self.request_method = request_method

    def NoRoute(self, request_method):
        allowed_methods = []
        for methods, route in self.routes:
            allowed_methods.extend(methods)
        return self.MethodNotAllowed(allowed_methods, request_method)

    def match(self, match, request_method):
        if isinstance(match, basestring):
            return {} if request_method == match else None
        return {} if request_method in match else None

    __call__ = rename_args(Router.__call__, (
        'self', 'context', 'request_method'))


class App(object):
    def __init__(self, router, default_context=None):
        self.router = router
        if default_context is None:
            default_context = {}
        self.default_context = default_context

    def not_found(self, environ, start_response):
        message = 'The requested resource could not be found.\r\n'
        start_response('404 Not Found', [
            ('Content-type', 'text/plain'),
            ('Content-length', str(len(message)))
        ])
        return [message]

    def method_not_allowed(self, request_method, allowed_methods):
        joined_methods = ', '.join(allowed_methods)
        def method_not_allowed(environ, start_response):
            if request_method == 'OPTIONS':
                status = '200 OK'
                message = (
                    'The requested resource supports the '
                    'following methods: %s.\r\n'
                ) % (joined_methods,)
            else:
                status = '405 Method Not Allowed'
                message = (
                    'The requested resource does not support '
                    'the %s method. It does support: %s.\r\n'
                ) % (request_method, joined_methods)
            start_response(status, [
                ('Content-type', 'text/plain'),
                ('Content-length', str(len(message))),
                ('Allow', joined_methods)
            ])
            return [message]
        return method_not_allowed

    def __call__(self, environ, start_response):
        context = Context(
            self.default_context,
            environ=environ,
            path_info=environ['PATH_INFO'],
            request_method=environ['REQUEST_METHOD']
        )
        try:
            response = context.inject(self.router)
        except MethodRouter.MethodNotAllowed as exc:
            return self.method_not_allowed(
                exc.request_method, exc.allowed_methods
            )(environ, start_response)
        except PathRouter.NoRoute:
            return self.not_found(environ, start_response)
        return response(environ, start_response)
