import re
import unittest
from types import TracebackType
from mock import sentinel, Mock

from potpy.context import Context
from potpy import router


class SOME_TRACEBACK(object):
    def __eq__(self, other):
        return isinstance(other, TracebackType)
SOME_TRACEBACK = SOME_TRACEBACK()


class TestRoute(unittest.TestCase):
    def setUp(self):
        self.calls = []

    def handler(self, value):
        def handler():
            self.calls.append(value)
            return value
        return handler

    def test_calls_handlers_in_order(self):
        route = router.Route(
            self.handler(sentinel.first),
            self.handler(sentinel.second),
            self.handler(sentinel.third),
        )
        self.assertIs(route(Context()), sentinel.third)
        self.assertEqual(
            self.calls,
            [sentinel.first, sentinel.second, sentinel.third]
        )

    def test_adds_named_handler_results_to_context(self):
        route = router.Route(
            (self.handler(sentinel.result), 'result'),
            lambda result: result,
        )
        context = Context()
        self.assertIs(route(context), sentinel.result)
        self.assertEqual(context['result'], sentinel.result)

    def test_can_add_more_handlers(self):
        route = router.Route(
            self.handler(sentinel.first),
            self.handler(sentinel.second),
        )
        route.add(self.handler(sentinel.third))
        self.assertIs(route(Context()), sentinel.third)
        self.assertEqual(
            self.calls,
            [sentinel.first, sentinel.second, sentinel.third]
        )

    def test_subroutes(self):
        route = router.Route((lambda: sentinel.foo, 'foo'))
        subroute = router.Route(
            (lambda foo: (foo, sentinel.result), 'sub'),
        )
        route.add(subroute)
        context = Context()
        self.assertEqual(
            route(context),
            (sentinel.foo, sentinel.result)
        )
        self.assertEqual(
            context['sub'],
            (sentinel.foo, sentinel.result)
        )

    def test_stop(self):
        def stopper():
            raise router.Route.Stop()
        route = router.Route(
            self.handler(sentinel.result),
            stopper,
            self.handler(sentinel.not_result)
        )
        self.assertIs(route(Context()), sentinel.result)
        self.assertEqual(self.calls, [sentinel.result])

    def test_stop_with_value(self):
        def stopper():
            raise router.Route.Stop(sentinel.result)
        route = router.Route(
            self.handler(sentinel.not_result),
            stopper,
            self.handler(sentinel.also_not_result)
        )
        self.assertIs(route(Context()), sentinel.result)
        self.assertEqual(self.calls, [sentinel.not_result])

    def test_exceptions_are_raised(self):
        MyException = type('MyException', (Exception,), {})
        route = router.Route(lambda: Mock(side_effect=MyException)())
        with self.assertRaises(MyException):
            route(Context())

    def test_exception_handlers(self):
        MyException = type('MyException', (Exception,), {})
        exc = MyException()
        def raiser():
            raise exc
        exc_handler = Mock(name='exc_handler')
        route = router.Route()
        route.add(raiser, exception_handlers=[
            (MyException, lambda exc_info: exc_handler(exc_info))
        ])
        self.assertIs(route(Context()), exc_handler.return_value)
        exc_handler.assert_called_once_with((
            MyException, exc, SOME_TRACEBACK))

    def test_exception_handlers_unhandled(self):
        MyException = type('MyException', (Exception,), {})
        OtherException = type('OtherException', (Exception,), {})
        exc_handler = Mock(name='exc_handler')
        route = router.Route()
        route.add(
            lambda: Mock(side_effect=MyException)(),
            exception_handlers=[
                (OtherException, lambda exc_info: exc_handler(exc_info))
            ]
        )
        with self.assertRaises(MyException):
            route(Context())
        self.assertFalse(exc_handler.called)

    def test_result_of_exception_handler_is_added_to_context(self):
        MyException = type('MyException', (Exception,), {})
        exc = MyException()
        def raiser():
            raise exc
        exc_handler = Mock(
            name='exc_handler',
            return_value=sentinel.exc_handler_result
        )
        route = router.Route(
            (raiser, 'handler_result', [
                (MyException, lambda exc_info: exc_handler(exc_info))
            ]),
            lambda handler_result: (handler_result, sentinel.next_result)
        )
        self.assertEqual(
            route(Context()),
            (sentinel.exc_handler_result, sentinel.next_result)
        )

    def test_can_refer_to_previous(self):
        ctx = Context(foo=sentinel.foo)
        class MyClass(object):
            def __call__(self, foo):
                return foo
        route = router.Route()
        route.add(MyClass)
        route.add(route.previous)
        self.assertIs(route(ctx), sentinel.foo)

    def test_can_refer_to_attribute_of_previous(self):
        ctx = Context(foo=sentinel.foo)
        class MyClass(object):
            def my_method(self, foo):
                return foo
        route = router.Route()
        route.add(MyClass)
        route.add(router.Route.previous.my_method)
        self.assertIs(route(ctx), sentinel.foo)

    def test_can_refer_to_subattribute_of_previous(self):
        ctx = Context(foo=sentinel.foo)
        class MyClass(object):
            class ChildClass(object):
                @staticmethod
                def my_method(foo):
                    return foo
        route = router.Route()
        route.add(MyClass)
        route.add(router.Route.previous.ChildClass.my_method)
        self.assertIs(route(ctx), sentinel.foo)


class TestRouter(unittest.TestCase):
    def setUp(self):
        self.context = Context()

    def test_injects_match_result_to_handler(self):
        handler = Mock()
        r = router.Router(
            (sentinel.no_match, lambda: handler(sentinel.not_result)),
            (sentinel.match, lambda foo, bar: handler(foo, bar)),
        )
        r.match = Mock(side_effect=lambda match, obj: {
            'foo': sentinel.foo,
            'bar': sentinel.bar
        } if match is sentinel.match else None)
        self.assertIs(
            r(self.context, sentinel.obj),
            handler.return_value
        )
        self.assertEqual(
            r.match.call_args_list,
            [
                ((sentinel.no_match, sentinel.obj),),
                ((sentinel.match, sentinel.obj),),
            ]
        )
        handler.assert_called_once_with(sentinel.foo, sentinel.bar)

    def test_raises_NoRoute_when_no_routes_at_all(self):
        r = router.Router()
        with self.assertRaises(r.NoRoute):
            r(self.context, '')

    def test_raises_NoRoute_when_no_routes_match(self):
        handler = Mock()
        r = router.Router((sentinel.match, handler))
        r.match = Mock(return_value=None)
        with self.assertRaises(r.NoRoute):
            r(self.context, sentinel.obj)
        self.assertFalse(handler.called)

    def test_wraps_handlers_in_route(self):
        handler = Mock()
        r = router.Router(
            (sentinel.match, [
                lambda: handler(sentinel.result1),
                lambda: handler(sentinel.result2),
            ]),
        )
        r.match = Mock(return_value={})
        self.assertTrue(isinstance(r.routes[0][-1], router.Route))
        self.assertIs(
            r(self.context, sentinel.obj),
            handler.return_value
        )
        self.assertEqual(
            handler.call_args_list,
            [
                ((sentinel.result1,),),
                ((sentinel.result2,),),
            ]
        )

    def test_doesnt_rewrap_handlers_that_are_already_routes(self):
        route = router.Route()
        r = router.Router((sentinel.match, route))
        self.assertIs(r.routes[0][-1], route)


class TestPathRouter(unittest.TestCase):
    def setUp(self):
        self.context = Context()

    def test_routes_empty_path(self):
        app = Mock(name='app')
        r = router.PathRouter(
            ('', lambda: app())
        )
        self.assertIs(r(self.context, ''), app.return_value)

    def test_matches_path(self):
        app = Mock(name='app')
        r = router.PathRouter(
            ('foo', lambda: Mock(name='foo')()),
            ('bar', lambda: app())
        )
        self.assertIs(r(self.context, 'bar'), app.return_value)

    def test_injects_match_groups_to_app(self):
        app = Mock(name='app')
        r = router.PathRouter(
            ('{foo}/{bar}', lambda foo, bar: app(foo, bar)),
        )
        self.assertIs(r(self.context, 'oof/rab'), app.return_value)
        app.assert_called_once_with('oof', 'rab')

    def test_match_can_be_compiled_regex(self):
        rx = re.compile('')
        r = router.PathRouter(
            (rx, lambda: Mock()()),
        )
        r.match = Mock(return_value={})
        r(self.context, sentinel.path)
        r.match.assert_called_once_with(rx, sentinel.path)

    def test_named_routes_may_not_be_compiled_regex(self):
        with self.assertRaises(TypeError) as assertion:
            router.PathRouter(('name', re.compile(''), lambda: None))
        self.assertEqual(
            assertion.exception.message,
            'match argument for named routes must be strings'
        )

    def test_gets_path_from_context(self):
        rx = re.compile('')
        r = router.PathRouter(
            (rx, lambda: Mock()()),
        )
        r.match = Mock(return_value={})
        self.context['path'] = sentinel.path
        self.context.inject(r)
        r.match.assert_called_once_with(rx, sentinel.path)

    def test_reverse(self):
        r = router.PathRouter(
            ('hello', 'hello/{name}', lambda: Mock()()),
        )
        self.assertEqual(r.reverse('hello', name='guido'), 'hello/guido')


class MethodRouter(unittest.TestCase):
    def setUp(self):
        self.context = Context()

    def test_routes_by_method(self):
        app = Mock(name='app')
        r = router.MethodRouter(
            ('GET', lambda: app())
        )
        self.assertIs(r(self.context, 'GET'), app.return_value)

    def test_tuple_specifies_multiple_methods(self):
        app = Mock(name='app')
        r = router.MethodRouter(
            (('GET', 'HEAD'), lambda: app())
        )
        self.assertIs(r(self.context, 'GET'), app.return_value)
        self.assertIs(r(self.context, 'HEAD'), app.return_value)

    def test_gets_method_from_context(self):
        r = router.MethodRouter(
            (sentinel.match, lambda: Mock()()),
        )
        r.match = Mock(return_value={})
        self.context['method'] = sentinel.method
        self.context.inject(r)
        r.match.assert_called_once_with(sentinel.match, sentinel.method)


if __name__ == '__main__':
    unittest.main()
