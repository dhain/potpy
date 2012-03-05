import unittest

from potpy import template


class TestTemplate(unittest.TestCase):
    def test_empty_string(self):
        t = template.Template('')
        self.assertEqual(t.regex.pattern, '')
        self.assertEqual(t.fill_template, '')

    def test_basic_string(self):
        t = template.Template('abc')
        self.assertEqual(t.regex.pattern, 'abc')
        self.assertEqual(t.fill_template, 'abc')

    def test_slash(self):
        t = template.Template('abc/def')
        self.assertEqual(t.regex.pattern, 'abc/def')
        self.assertEqual(t.fill_template, 'abc/def')

    def test_slashes(self):
        t = template.Template('abc/def/ghi')
        self.assertEqual(t.regex.pattern, 'abc/def/ghi')
        self.assertEqual(t.fill_template, 'abc/def/ghi')

    def test_brackets(self):
        t = template.Template('abc/{def}/ghi')
        self.assertEqual(t.regex.pattern, 'abc/(?P<def>.*)/ghi')
        self.assertEqual(t.fill_template, 'abc/%(def)s/ghi')

    def test_brackets_and_regex(self):
        t = template.Template(r'{def:\d+}')
        self.assertEqual(t.regex.pattern, r'(?P<def>\d+)')
        self.assertEqual(t.fill_template, r'%(def)s')

    def test_brackets_in_regex(self):
        t = template.Template(r'{foo:\d{3}}')
        self.assertEqual(t.regex.pattern, r'(?P<foo>\d{3})')
        self.assertEqual(t.fill_template, r'%(foo)s')

    def test_left_heavy_brackets(self):
        with self.assertRaises(ValueError) as assertion:
            template.Template(r'{def:\d{3}'),
        self.assertEqual(
            assertion.exception.message,
            'unbalanced brackets'
        )

    def test_right_heavy_brackets(self):
        t = template.Template(r'{def:\d+}}')
        self.assertEqual(t.regex.pattern, r'(?P<def>\d+)}')
        self.assertEqual(t.fill_template, r'%(def)s}')

    def test_backslash(self):
        t = template.Template(r'a\c')
        self.assertEqual(t.regex.pattern, r'a\\c')
        self.assertEqual(t.fill_template, r'a\\c')

    def test_multiple_brackets(self):
        t = template.Template('{abc}/{def:\d{3}}{ghi}jkl')
        self.assertEqual(
            t.regex.pattern,
            '(?P<abc>.*)/(?P<def>\d{3})(?P<ghi>.*)jkl'
        )
        self.assertEqual(
            t.fill_template,
            '%(abc)s/%(def)s%(ghi)sjkl'
        )

    def test_percent(self):
        t = template.Template('foo%bar')
        self.assertEqual(t.fill_template, 'foo%%bar')

    def test_percent_in_brackets(self):
        t = template.Template('{foo:bar%bar}')
        self.assertEqual(t.fill_template, '%(foo)s')

    def test_fill(self):
        t = template.Template('{foo}, {bar}')
        self.assertEqual(t.fill(foo='baz', bar='qux'), 'baz, qux')


if __name__ == '__main__':
    unittest.main()