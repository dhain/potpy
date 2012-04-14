from __future__ import with_statement
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from types import ModuleType
from mock import sentinel, Mock

from potpy.context import Context
from potpy import configparser


class TestParsePathSpec(unittest.TestCase):
    def test_just_a_path(self):
        name, path, types = configparser.parse_path_spec('/foobar:')
        self.assertIs(name, None)
        self.assertEqual(path, '/foobar')
        self.assertEqual(types, {})

    def test_name_and_path(self):
        name, path, types = configparser.parse_path_spec('name /foobar:')
        self.assertEqual(name, 'name')
        self.assertEqual(path, '/foobar')
        self.assertEqual(types, {})

    def test_path_and_type(self):
        name, path, types = configparser.parse_path_spec(
            '/foobar (foo: bar):')
        self.assertIs(name, None)
        self.assertEqual(path, '/foobar')
        self.assertEqual(types, {'foo': 'bar'})

    def test_name_path_and_types(self):
        name, path, types = configparser.parse_path_spec(
            'name /foobar (foo: bar, baz:quux):')
        self.assertEqual(name, 'name')
        self.assertEqual(path, '/foobar')
        self.assertEqual(types, {'foo': 'bar', 'baz': 'quux'})

    def test_raises_SyntaxError_if_no_match(self):
        with self.assertRaises(SyntaxError) as assertion:
            configparser.parse_path_spec(':')
        self.assertEqual(
            assertion.exception.message, 'expecting path spec')


class TestParseMethodSpec(unittest.TestCase):
    def test_single_method(self):
        self.assertEqual(
            configparser.parse_method_spec('* GET:'),
            ['GET']
        )

    def test_many_methods(self):
        self.assertEqual(
            configparser.parse_method_spec('* GET, HEAD:'),
            ['GET', 'HEAD']
        )

    def test_raises_SyntaxError_if_no_match(self):
        with self.assertRaises(SyntaxError) as assertion:
            configparser.parse_method_spec('foo;bar:')
        self.assertEqual(
            assertion.exception.message, 'expecting method spec')


class TestParseHandlerSpec(unittest.TestCase):
    def test_just_a_handler(self):
        handler, name = configparser.parse_handler_spec('foo.bar')
        self.assertEqual(handler, 'foo.bar')
        self.assertIs(name, None)

    def test_handler_with_name(self):
        handler, name = configparser.parse_handler_spec('foo.bar (baz)')
        self.assertEqual(handler, 'foo.bar')
        self.assertEqual(name, 'baz')

    def test_with_trailing_colon(self):
        handler, name = configparser.parse_handler_spec('foo.bar:')
        self.assertEqual(handler, 'foo.bar')
        self.assertIs(name, None)

    def test_raises_SyntaxError_if_no_match(self):
        with self.assertRaises(SyntaxError) as assertion:
            configparser.parse_handler_spec('42')
        self.assertEqual(
            assertion.exception.message, 'expecting handler spec')


class TestParseExceptionHandlerSpec(unittest.TestCase):
    def test_single_type(self):
        types, handler = configparser.parse_exception_handler_spec(
            'exc: handler')
        self.assertEqual(types, ('exc',))
        self.assertEqual(handler, 'handler')

    def test_many_types(self):
        types, handler = configparser.parse_exception_handler_spec(
            'exc1, exc2: handler')
        self.assertEqual(types, ('exc1', 'exc2'))
        self.assertEqual(handler, 'handler')

    def test_raises_SyntaxError_if_no_match(self):
        with self.assertRaises(SyntaxError) as assertion:
            configparser.parse_exception_handler_spec(': handler')
        self.assertEqual(
            assertion.exception.message,
            'expecting exception handler spec'
        )


class TestSplitIndent(unittest.TestCase):
    def test_empty_string(self):
        self.assertEqual(configparser.split_indent(''), (0, ''))

    def test_no_leading_spaces(self):
        self.assertEqual(configparser.split_indent('foo'), (0, 'foo'))

    def test_leading_spaces(self):
        self.assertEqual(configparser.split_indent('  foo'), (2, 'foo'))

    def test_translates_tabs_to_8_spaces(self):
        self.assertEqual(configparser.split_indent('\t foo'), (9, 'foo'))

    def test_strips_trailing_spaces(self):
        self.assertEqual(configparser.split_indent('  foo '), (2, 'foo'))

    def test_strips_comments(self):
        self.assertEqual(
            configparser.split_indent('foo#bar'), (0, 'foo'))


class TestParseConfig(unittest.TestCase):
    def test_simple_config(self):
        module = ModuleType('module')
        module.handler1 = lambda: sentinel.a2
        module.handler2 = lambda a1, a2: (a1, a2, sentinel.result)
        config = '''
        index /{a1:\d+} (a1: int):
            handler1 (a2)
            handler2
        '''
        router = configparser.parse_config(config.splitlines(), module)
        self.assertEqual(router.reverse('index', a1=37), '/37')
        ctx = Context(path_info='/42')
        self.assertEqual(
            ctx.inject(router),
            (42, sentinel.a2, sentinel.result)
        )

    def test_medium_config(self):
        module = ModuleType('module')
        module.handler1 = lambda: sentinel.a2
        module.handler2 = lambda a1, a2: (a1, a2, sentinel.result)
        config = '''
        index /{a1:\d+} (a1: int):
            * GET, HEAD:
                handler1 (a2)
                handler2
            * POST:
                handler1
        '''
        router = configparser.parse_config(config.splitlines(), module)
        self.assertEqual(router.reverse('index', a1=37), '/37')
        ctx = Context(path_info='/42', request_method='GET')
        self.assertEqual(
            ctx.inject(router),
            (42, sentinel.a2, sentinel.result)
        )
        ctx = Context(path_info='/42', request_method='POST')
        self.assertIs(ctx.inject(router), sentinel.a2)

    def test_complex_config(self):
        module = ModuleType('module')
        module.exc1 = type('exc1', (Exception,), {})
        module.exc2 = type('exc2', (Exception,), {})
        module.exc3 = type('exc3', (Exception,), {})
        module.handler1 = lambda: sentinel.a2
        module.handler2 = lambda a1, a2: (a1, a2, sentinel.result)
        module.handler3 = lambda: Mock(side_effect=module.exc2)()
        module.handler4 = lambda: sentinel.a4
        module.handler5 = lambda: sentinel.a5
        module.handler6 = lambda r1: (r1, sentinel.a6)
        module.handler7 = lambda: sentinel.a7
        module.handler8 = lambda: sentinel.a8
        module.handler9 = lambda r1, r2: (r1, r2, sentinel.a9)
        config = """
        index /:
            * GET, HEAD:
                handler1 (a2)
                handler2
            * POST:
                handler1
        todo /{todo_id:\d+} (todo_id: int):
            * GET, HEAD:
                handler3 (r1):
                    exc1, exc2: handler4
                    exc3: handler5
                handler6
        other /foo:
            handler7 (r1)
            * DELETE:
                handler8 (r2)
            handler9
        """
        router = configparser.parse_config(config.splitlines(), module)
        ctx = Context(path_info='/42', request_method='GET')
        self.assertEqual(ctx.inject(router), (sentinel.a4, sentinel.a6))
        ctx = Context(path_info='/foo', request_method='DELETE')
        self.assertEqual(
            ctx.inject(router),
            (sentinel.a7, sentinel.a8, sentinel.a9)
        )

    def test_omitting_module_uses_calling_module(self):
        config = """
        /:
            TestParseConfig
        """
        router = configparser.parse_config(config.splitlines())
        self.assertIs(
            router.routes[0][1].route[0][1], TestParseConfig)


if __name__ == '__main__':
    unittest.main()
