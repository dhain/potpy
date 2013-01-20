import sys
import unittest
from potpy.test.loader import Loader


if __name__ == '__main__':
    suite = Loader().loadTestsFromNames(['potpy.test'])
    result = unittest.TextTestRunner().run(suite)
    sys.exit(not result.wasSuccessful())
