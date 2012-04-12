import os
from pkgutil import walk_packages
from doctest import DocTestSuite, DocFileSuite
from setuptools.command.test import ScanningLoader

import potpy

PKG_PATH = potpy.__file__
DOC_PATH = os.path.abspath(os.path.join(
    os.path.dirname(PKG_PATH), '..', 'docs'))


def reverse_iter(it):
    i = len(it)
    while i:
        i -= 1
        yield i, it[i]


class Loader(object):
    def loadTestsFromNames(self, names, module=None):
        suite = ScanningLoader().loadTestsFromNames(names, module)
        for loader, name, ispkg in walk_packages(PKG_PATH):
            if ispkg:
                continue
            try:
                docsuite = DocTestSuite(name)
            except ValueError, err:
                if err.args[1] != 'has no tests':
                    raise
                continue
            suite.addTests(docsuite)
        for dirpath, dirnames, filenames in os.walk(DOC_PATH):
            for i, d in reverse_iter(dirnames):
                if d.startswith('_'):
                    del dirnames[i]
            for f in filenames:
                if not f.endswith('.rst'):
                    continue
                docsuite = DocFileSuite(
                    os.path.join(dirpath, f), module_relative=False)
                suite.addTests(docsuite)
        return suite
