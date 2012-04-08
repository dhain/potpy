from pkgutil import walk_packages
from doctest import DocTestSuite
from setuptools.command.test import ScanningLoader

import potpy


class Loader(object):
    def loadTestsFromNames(self, names, module=None):
        suite = ScanningLoader().loadTestsFromNames(names, module)
        for loader, name, ispkg in walk_packages(potpy.__file__):
            if ispkg:
                continue
            try:
                docsuite = DocTestSuite(name)
            except ValueError, err:
                if err.args[1] != 'has no tests':
                    raise
                continue
            suite.addTests(docsuite)
        return suite
