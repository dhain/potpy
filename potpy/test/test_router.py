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
        route = router.Route([
            (None, self.handler(sentinel.first), ()),
            (None, self.handler(sentinel.second), ()),
            (None, self.handler(sentinel.third), ()),
        ])
        self.assertIs(route(Context()), sentinel.third)
        self.assertEqual(
            self.calls,
            [sentinel.first, sentinel.second, sentinel.third]
        )

    def test_adds_named_handler_results_to_context(self):
        route = router.Route()
        route.add(self.handler(sentinel.result), 'result')
        route.add(lambda result: result)
        context = Context()
        self.assertIs(route(context), sentinel.result)
        self.assertEqual(context['result'], sentinel.result)

    def test_subroutes(self):
        route = router.Route()
        subroute = router.Route()
        subroute.add(lambda foo: (foo, sentinel.result), 'sub')
        route.add(lambda: sentinel.foo, 'foo')
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
        route = router.Route()
        route.add(self.handler(sentinel.result))
        route.add(stopper)
        route.add(self.handler(sentinel.not_result))
        self.assertIs(route(Context()), sentinel.result)
        self.assertEqual(self.calls, [sentinel.result])

    def test_exceptions_are_raised(self):
        MyException = type('MyException', (Exception,), {})
        route = router.Route()
        route.add(lambda: Mock(side_effect=MyException)())
        with self.assertRaises(MyException):
            route(Context())

    def test_exception_handlers(self):
        MyException = type('MyException', (Exception,), {})
        exc = MyException()
        def raiser():
            raise exc
        exc_handler = Mock(name='handler')
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
        exc_handler = Mock(name='handler')
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


class TestRouter(unittest.TestCase):
    def setUp(self):
        self.context = Context()

    def test_routes_empty_url(self):
        app = Mock(name='app')
        r = router.Router([
            (None, '', lambda: app())
        ])
        self.assertIs(r(self.context, ''), app.return_value)

    def test_matches_url(self):
        app = Mock(name='app')
        r = router.Router([
            (None, 'foo', lambda: Mock(name='foo')()),
            (None, 'bar', lambda: app())
        ])
        self.assertIs(r(self.context, 'bar'), app.return_value)

    def test_injects_match_groups_to_app(self):
        results = []
        def app(foo, bar):
            results.append((foo, bar))
            return sentinel.result
        r = router.Router([
            (None, '{foo}/{bar}', app)
        ])
        self.assertIs(r(self.context, 'oof/rab'), sentinel.result)
        self.assertEqual(results, [('oof', 'rab')])


if __name__ == '__main__':
    unittest.main()
