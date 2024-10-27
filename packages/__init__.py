import unittest

def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    suite.addTests(loader.discover('tests'))
    return suite