"""
This module provides classes for creating WSGI (:pep:`333`) applications.

For a simple example, see ``examples/wsgi.py``. For a more complete example,
see ``examples/todo``.
"""
from .router import Router
from .template import Template
from .context import Context
from .util import rename_args


class PathRouter(Router):
    """
    Route by URL/path.

    Utilizes the :class:`~potpy.template.Template` class to capture path
    parameters, adding them to the :class:`~potpy.context.Context`. For
    example, you might define a route with a path
    template: ``/posts/{slug}`` -- which would match the path
    ``/posts/my-post``, adding ``{'slug': 'my-post'}`` to the context:

        >>> from potpy.context import Context
        >>> from pprint import pprint
        >>> handler = lambda: None  # just a bogus handler
        >>> router = PathRouter(('/posts/{slug}', handler))
        >>> ctx = Context(path_info='/posts/my-post')
        >>> ctx.inject(router)
        >>> pprint(dict(ctx))
        {'path_info': '/posts/my-post', 'slug': 'my-post'}

    Routes can also be named, allowing reverse path lookup and filling of path
    parameters. See :meth:`reverse` for details.
    """
    def __init__(self, *routes):
        self._templates = {}
        super(PathRouter, self).__init__(*routes)

    def add(self, *args):
        """Add a path template and handler.

        :param name: Optional. If specified, allows reverse path lookup with
            :meth:`reverse`.
        :param template: A string or :class:`~potpy.template.Template`
            instance used to match paths against. Strings will be wrapped in a
            Template instance.
        :param handler: A callable or :class:`~potpy.router.Route` instance
            which will handle calls for the given path. See
            :meth:`potpy.router.Router.add` for details.
        """
        if len(args) > 2:
            name, template = args[:2]
            args = args[2:]
        else:
            name = None
            template = args[0]
            args = args[1:]
        if isinstance(template, tuple):
            template, type_converters = template
            template = Template(template, **type_converters)
        elif not isinstance(template, Template):
            template = Template(template)
        if name:
            self._templates[name] = template
        super(PathRouter, self).add(template, *args)

    def match(self, template, path_info):
        """Check for a path match.

        :param template: A :class:`~potpy.template.Template` object to match
            against.
        :param path_info: The path to check for a match.
        :returns: The template parameters extracted from the path, or ``None``
            if the path does not match the template.

        Example:

            >>> from potpy.template import Template
            >>> template = Template('/posts/{slug}')
            >>> PathRouter().match(template, '/posts/my-post')
            {'slug': 'my-post'}
        """
        return template.match(path_info)

    __call__ = rename_args(Router.__call__, (
        'self', 'context', 'path_info'))

    def reverse(self, *args, **kwargs):
        """Look up a path by name and fill in the provided parameters.

        Example:

            >>> handler = lambda: None  # just a bogus handler
            >>> router = PathRouter(('post', '/posts/{slug}', handler))
            >>> router.reverse('post', slug='my-post')
            '/posts/my-post'
        """
        (name,) = args
        return self._templates[name].fill(**kwargs)


class MethodRouter(Router):
    """
    Route by request method.

        >>> from potpy.context import Context
        >>> handler1 = lambda request_method: (1, request_method.lower())
        >>> handler2 = lambda request_method: (2, request_method.lower())
        >>> router = MethodRouter(
        ...     ('POST', handler1),          # can specify a single method
        ...     (('GET', 'HEAD'), handler2)  # or a tuple of methods
        ... )
        >>> Context(request_method='GET').inject(router)
        (2, 'get')
        >>> Context(request_method='POST').inject(router)
        (1, 'post')
    """
    class MethodNotAllowed(Router.NoRoute):
        """
        Raised instead of :exc:`potpy.router.Router.NoRoute` when no handler
        matches the given method.

        Has an ``allowed_methods`` attribute which is a list of the methods
        handled by this router.
        """
        def __init__(self, allowed_methods, request_method):
            self.allowed_methods = allowed_methods
            self.request_method = request_method

    def NoRoute(self, request_method):
        allowed_methods = []
        for methods, route in self.routes:
            allowed_methods.extend(methods)
        return self.MethodNotAllowed(allowed_methods, request_method)

    def match(self, methods, request_method):
        """Check for a method match.

        :param methods: A method or tuple of methods to match against.
        :param request_method: The method to check for a match.
        :returns: An empty :class:`dict` in the case of a match, or ``None``
            if there is no matching handler for the given method.

        Example:

            >>> MethodRouter().match(('GET', 'HEAD'), 'HEAD')
            {}
            >>> MethodRouter().match('POST', 'DELETE')
        """
        if isinstance(methods, basestring):
            return {} if request_method == methods else None
        return {} if request_method in methods else None

    __call__ = rename_args(Router.__call__, (
        'self', 'context', 'request_method'))


class App(object):
    """Wrap a potpy router in a WSGI application.

    Use this with :class:`PathRouter` and :class:`MethodRouter` to implement a
    full-featured HTTP request routing system. Return a WSGI app from the last
    handler in the route, and it will be called with ``environ`` and
    ``start_response``.

    If no route matches, a `404 Not Found` response will be generated. If
    using a MethodRouter, and the request method doesn't match, a `405 Method
    Not Allowed` response will be generated. Also responds to HTTP ``OPTIONS``
    requests.

    Calls the provided router with a context containing ``environ``,
    ``path_info``, and ``request_method`` fields, and any fields from the
    optional ``default_context`` argument.

    :param router: The router to call in response to WSGI requests.
    :param default_context: Optional. A :class:`dict`-like mapping of extra
        fields to add to the context for each request.

    Example:

        >>> def my_app(environ, start_response):
        ...     start_response('200 OK', [('Content-type', 'text/plain')])
        ...     return ['Hello, world!']
        ...
        >>> def handler(request):
        ...     # do something with the request
        ...     return my_app
        ...
        >>> class Request(object):
        ...     def __init__(self, environ):
        ...         pass    # wrap environ in a custom request object
        ...
        >>> app = App(
        ...     PathRouter(('/hello', lambda: my_app)),
        ...     {'request': Request}    # add a Request object to context
        ... )
        >>> app({
        ...     'PATH_INFO': '/hello',
        ...     'REQUEST_METHOD': 'GET',
        ... }, lambda status, headers: None)    # bogus start_response
        ['Hello, world!']
    """
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
        """Call the router as a WSGI app.

        Constructs a :class:`~potpy.context.Context` object with ``environ``,
        ``path_info``, and ``request_method`` (extracted from the environ),
        and any fields supplied in ``self.default_context``.

        Calls the result of the router call as a WSGI app.
        """
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
