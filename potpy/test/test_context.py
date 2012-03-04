import unittest
from mock import sentinel, Mock

from potpy import context


class TestContext(unittest.TestCase):
    def setUp(self):
        self.context = context.Context(
            foo=sentinel.foo,
            bar=sentinel.bar,
            baz=sentinel.baz,
        )

    def test_can_inject_to_functions(self):
        def func(foo):
            return foo
        self.assertIs(self.context.inject(func), sentinel.foo)

    def test_injects_self_as_context(self):
        def func(context):
            return context
        self.assertIs(self.context.inject(func), self.context)

    def test_can_override_context(self):
        self.context['context'] = sentinel.context
        def func(context):
            return context
        self.assertIs(self.context.inject(func), sentinel.context)

    def test_context_can_be_a_default_argument(self):
        def func(context=None):
            return context
        self.assertIs(self.context.inject(func), self.context)

    def test_can_inject_to_classes(self):
        class Cls(object):
            def __init__(self, bar):
                self.bar = bar
        self.assertIs(self.context.inject(Cls).bar, sentinel.bar)

    def test_can_inject_to_classes_without_init(self):
        class Cls(object):
            pass
        self.assertTrue(isinstance(self.context.inject(Cls), Cls))

    def test_can_inject_to_instances(self):
        class Cls(object):
            def __call__(self, baz):
                return baz
        self.assertIs(self.context.inject(Cls()), sentinel.baz)

    def test_can_inject_to_instance_methods(self):
        class Cls(object):
            def frob(self, baz):
                return baz
        self.assertIs(self.context.inject(Cls().frob), sentinel.baz)

    def test_can_inject_to_class_methods(self):
        class Cls(object):
            @classmethod
            def frob(cls, baz):
                return baz
        self.assertIs(self.context.inject(Cls().frob), sentinel.baz)

    def test_can_inject_to_static_methods(self):
        class Cls(object):
            @staticmethod
            def frob(baz):
                return baz
        self.assertIs(self.context.inject(Cls().frob), sentinel.baz)

    def test_raises_TypeError_for_non_callable_objects(self):
        with self.assertRaises(TypeError) as assertion:
            self.context.inject(object())

    def test_raises_TypeError_for_integers(self):
        with self.assertRaises(TypeError) as assertion:
            self.context.inject(1)

    def test_callable_injectables(self):
        self.context['foo'] = lambda: sentinel.result
        self.assertIs(
            self.context.inject(lambda foo: foo),
            sentinel.result
        )

    def test_callable_injectables_get_injected(self):
        self.context['foo'] = lambda bar: bar
        self.assertIs(
            self.context.inject(lambda foo: foo),
            sentinel.bar
        )

    def test_can_override_with_kwargs(self):
        func = Mock()
        self.context.inject(
            lambda foo, bar: func(foo, bar),
            bar=sentinel.overridden
        )
        func.assert_called_once_with(sentinel.foo, sentinel.overridden)

    def test_can_specify_extra_kwargs(self):
        func = Mock()
        self.context.inject(
            lambda foo, deadbeef: func(foo, deadbeef),
            deadbeef=sentinel.deadbeef
        )
        func.assert_called_once_with(sentinel.foo, sentinel.deadbeef)

    def test_get_with_default_returns_default_when_key_not_present(self):
        self.assertIs(
            self.context.get('frob', sentinel.default),
            sentinel.default
        )


if __name__ == '__main__':
    unittest.main()
