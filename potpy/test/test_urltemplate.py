import unittest

from potpy.urltemplate import make_regex


class TestMakeRegex(unittest.TestCase):
    def test_empty_string(self):
        self.assertEqual(make_regex(''), '')

    def test_basic_string(self):
        self.assertEqual(make_regex('abc'), 'abc')

    def test_string_with_slash(self):
        self.assertEqual(make_regex('abc/def'), 'abc/def')

    def test_string_with_slashes(self):
        self.assertEqual(make_regex('abc/def/ghi'), 'abc/def/ghi')

    def test_string_with_brackets(self):
        self.assertEqual(
            make_regex('abc/{def}/ghi'),
            'abc/(?P<def>.*)/ghi'
        )

    def test_string_with_brackets_and_regex(self):
        self.assertEqual(
            make_regex(r'{def:\d+}'),
            r'(?P<def>\d+)'
        )

    def test_string_with_brackets_in_regex(self):
        self.assertEqual(
            make_regex(r'{foo:\d{3}}'),
            r'(?P<foo>\d{3})'
        )

    def test_string_with_left_heavy_brackets(self):
        with self.assertRaises(ValueError):
            make_regex(r'{def:\d{3}'),

    def test_string_with_right_heavy_brackets(self):
        self.assertEqual(
            make_regex(r'{def:\d+}}'),
            r'(?P<def>\d+)}'
        )

    def test_string_with_backslash(self):
        self.assertEqual(make_regex(r'a\c'), r'a\\c')

    def test_string_with_multiple_brackets(self):
        self.assertEqual(
            make_regex('{abc}/{def:\d{3}}{ghi}jkl'),
            '(?P<abc>.*)/(?P<def>\d{3})(?P<ghi>.*)jkl'
        )


if __name__ == '__main__':
    unittest.main()
