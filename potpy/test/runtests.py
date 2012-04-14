import unittest
from loader import Loader


if __name__ == '__main__':
    suite = Loader().loadTestsFromNames(['potpy.test'])
    unittest.TextTestRunner().run(suite)
