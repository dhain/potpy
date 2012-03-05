import re
import unittest
from mock import sentinel, Mock

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

    def test_gets_path_from_context(self):
        template = Template('')
        r = wsgi.PathRouter((template, lambda: Mock()()))
        r.match = Mock(return_value={})
        self.context['path'] = sentinel.path
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
        self.context['method'] = sentinel.method
        self.context.inject(r)
        r.match.assert_called_once_with(sentinel.match, sentinel.method)


if __name__ == '__main__':
    unittest.main()
