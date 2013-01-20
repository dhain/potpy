from __future__ import with_statement
import unittest
if not hasattr(unittest.TestCase, 'assertIs'):
    import unittest2 as unittest

import re
from mock import sentinel, Mock, patch

from potpy.context import Context
from potpy.template import Template
from potpy import wsgi


class TestPathRouter(unittest.TestCase):
    def setUp(self):
        self.context = Context()

    def test_routes_empty_path(self):
        app = Mock(name='app')
        r = wsgi.PathRouter(
            ('', lambda: app())
        )
        self.assertIs(r(self.context, ''), app.return_value)

    def test_matches_path(self):
        app = Mock(name='app')
        r = wsgi.PathRouter(
            ('foo', lambda: Mock(name='foo')()),
            ('bar', lambda: app())
        )
        self.assertIs(r(self.context, 'bar'), app.return_value)

    def test_injects_match_groups_to_app(self):
        app = Mock(name='app')
        r = wsgi.PathRouter(
            ('{foo}/{bar}', lambda foo, bar: app(foo, bar)),
        )
        self.assertIs(r(self.context, 'oof/rab'), app.return_value)
        app.assert_called_once_with('oof', 'rab')

    def test_match_can_be_template(self):
        template = Template('')
        r = wsgi.PathRouter((template, lambda: Mock()()))
        r.match = Mock(return_value={})
        r(self.context, sentinel.path)
        r.match.assert_called_once_with(template, sentinel.path)

    def test_match_can_be_template_arg_tuple(self):
        template = ('{foo:\d+}', {'foo': int})
        r = wsgi.PathRouter((template, lambda: Mock()()))
        r(self.context, '42')
        self.assertEqual(self.context['foo'], 42)

    def test_gets_path_from_context(self):
        template = Template('')
        r = wsgi.PathRouter((template, lambda: Mock()()))
        r.match = Mock(return_value={})
        self.context['path_info'] = sentinel.path
        self.context.inject(r)
        r.match.assert_called_once_with(template, sentinel.path)

    def test_reverse(self):
        r = wsgi.PathRouter(
            ('hello', 'hello/{name}', lambda: Mock()()),
        )
        self.assertEqual(r.reverse('hello', name='guido'), 'hello/guido')


class MethodRouter(unittest.TestCase):
    def setUp(self):
        self.context = Context()

    def test_routes_by_method(self):
        app = Mock(name='app')
        r = wsgi.MethodRouter(
            ('GET', lambda: app())
        )
        self.assertIs(r(self.context, 'GET'), app.return_value)

    def test_tuple_specifies_multiple_methods(self):
        app = Mock(name='app')
        r = wsgi.MethodRouter(
            (('GET', 'HEAD'), lambda: app())
        )
        self.assertIs(r(self.context, 'GET'), app.return_value)
        self.assertIs(r(self.context, 'HEAD'), app.return_value)

    def test_gets_method_from_context(self):
        r = wsgi.MethodRouter(
            (sentinel.match, lambda: Mock()()),
        )
        r.match = Mock(return_value={})
        self.context['request_method'] = sentinel.method
        self.context.inject(r)
        r.match.assert_called_once_with(sentinel.match, sentinel.method)

    def test_NoRoute_is_subclass(self):
        self.assertTrue(issubclass(
            wsgi.MethodRouter.MethodNotAllowed, wsgi.Router.NoRoute))
        app = Mock(name='app')
        r = wsgi.MethodRouter(
            (('GET', 'HEAD'), lambda: app()),
            (('POST',), lambda: app())
        )
        with self.assertRaises(r.MethodNotAllowed) as assertion:
            r(self.context, 'DELETE')
        self.assertEqual(assertion.exception.request_method, 'DELETE')
        self.assertEqual(
            assertion.exception.allowed_methods,
            ['GET', 'HEAD', 'POST']
        )


class TestApp(unittest.TestCase):
    def setUp(self):
        self.environ = {
            'PATH_INFO': sentinel.path_info,
            'REQUEST_METHOD': sentinel.request_method,
        }

    def test_not_found(self):
        app = wsgi.App(sentinel.router)
        start_response = Mock()
        message = 'The requested resource could not be found.\r\n'
        expected_headers = [
            ('Content-type', 'text/plain'),
            ('Content-length', str(len(message)))
        ]
        self.assertEqual(
            app.not_found(sentinel.environ, start_response),
            [message]
        )
        start_response.assert_called_once_with(
            '404 Not Found', expected_headers)

    def test_method_not_allowed(self):
        app = wsgi.App(sentinel.router)
        start_response = Mock()
        request_method = 'DELETE'
        allowed_methods = ['GET', 'HEAD']
        joined_methods = ', '.join(allowed_methods)
        message = (
            'The requested resource does not support '
            'the %s method. It does support: %s.\r\n'
        ) % (request_method, joined_methods)
        expected_headers = [
            ('Content-type', 'text/plain'),
            ('Content-length', str(len(message))),
            ('Allow', joined_methods)
        ]
        self.assertEqual(
            app.method_not_allowed(
                request_method, allowed_methods
            )(sentinel.environ, start_response),
            [message]
        )
        start_response.assert_called_once_with(
            '405 Method Not Allowed', expected_headers)

    def test_method_not_allowed_options(self):
        app = wsgi.App(sentinel.router)
        start_response = Mock()
        request_method = 'OPTIONS'
        allowed_methods = ['GET', 'HEAD']
        joined_methods = ', '.join(allowed_methods)
        message = (
            'The requested resource supports the '
            'following methods: %s.\r\n'
        ) % (joined_methods,)
        expected_headers = [
            ('Content-type', 'text/plain'),
            ('Content-length', str(len(message))),
            ('Allow', joined_methods)
        ]
        self.assertEqual(
            app.method_not_allowed(
                request_method, allowed_methods
            )(sentinel.environ, start_response),
            [message]
        )
        start_response.assert_called_once_with(
            '200 OK', expected_headers)

    def test_sets_up_and_injects_context(self):
        router = Mock()
        app = wsgi.App(
            lambda environ, path_info, request_method: router(
                environ, path_info, request_method))
        self.assertIs(
            app(self.environ, sentinel.start_response),
            router.return_value.return_value
        )
        router.assert_called_once_with(
            self.environ, sentinel.path_info, sentinel.request_method)
        router.return_value.assert_called_once_with(
            self.environ, sentinel.start_response)

    def test_handles_NoRoute(self):
        router = Mock(side_effect=wsgi.PathRouter.NoRoute)
        app = wsgi.App(lambda: router())
        with patch.object(app, 'not_found') as not_found:
            self.assertIs(
                app(self.environ, sentinel.start_response),
                not_found.return_value
            )
        not_found.assert_called_once_with(
            self.environ, sentinel.start_response)

    def test_handles_MethodNotFound(self):
        router = Mock(
            side_effect=wsgi.MethodRouter.MethodNotAllowed(
                sentinel.allowed_methods, sentinel.request_method))
        app = wsgi.App(lambda: router())
        with patch.object(app, 'method_not_allowed') as not_allowed:
            self.assertIs(
                app(self.environ, sentinel.start_response),
                not_allowed.return_value.return_value
            )
        not_allowed.assert_called_once_with(
            sentinel.request_method, sentinel.allowed_methods)
        not_allowed.return_value.assert_called_once_with(
            self.environ, sentinel.start_response)

    def test_can_specify_default_context(self):
        router = Mock()
        app = wsgi.App(
            lambda extra1, extra2: router(extra1, extra2),
            {
                'extra1': sentinel.extra1,
                'extra2': sentinel.extra2,
            }
        )
        app(self.environ, sentinel.start_response),
        router.assert_called_once_with(sentinel.extra1, sentinel.extra2)


if __name__ == '__main__':
    unittest.main()
