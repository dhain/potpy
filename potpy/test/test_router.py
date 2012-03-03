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

    def test_injects_match_result_to_handler(self):
        handler = Mock()
        r = router.Router([
            ('name1', sentinel.no_match,
             lambda: handler(sentinel.shouldntgetthis)),
            ('name2', sentinel.match,
             lambda foo, bar: handler(foo, bar)),
        ])
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
        r = router.Router([('name', sentinel.match, handler)])
        r.match = Mock(return_value=None)
        with self.assertRaises(r.NoRoute):
            r(self.context, sentinel.obj)
        self.assertFalse(handler.called)


class TestUrlRouter(unittest.TestCase):
    def setUp(self):
        self.context = Context()

    def test_routes_empty_url(self):
        app = Mock(name='app')
        r = router.UrlRouter([
            (None, '', lambda: app())
        ])
        self.assertIs(r(self.context, ''), app.return_value)

    def test_matches_url(self):
        app = Mock(name='app')
        r = router.UrlRouter([
            (None, 'foo', lambda: Mock(name='foo')()),
            (None, 'bar', lambda: app())
        ])
        self.assertIs(r(self.context, 'bar'), app.return_value)

    def test_injects_match_groups_to_app(self):
        app = Mock(name='app')
        r = router.UrlRouter([
            (None, '{foo}/{bar}', lambda foo, bar: app(foo, bar)),
        ])
        self.assertIs(r(self.context, 'oof/rab'), app.return_value)
        app.assert_called_once_with('oof', 'rab')


if __name__ == '__main__':
    unittest.main()
