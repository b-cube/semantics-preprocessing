import unittest
from lib.nlp_utils import normalize_keyword_text


class TestKeywords(unittest.TestCase):
    def setUp(self):
        '''
        nothing to set up
        '''
        pass

    def test_strings(self):
        '''
        the most basic examples
        '''
        strings = [
            'soil+clay+pedon+loam+sandy loam',
            'soil-clay-pedon-loam-sandy loam',
            'soil;clay;pedon;loam;sandy loam',
            'soil|clay|pedon|loam|sandy loam',
            'soil>clay>pedon>loam>sandy loam'
        ]

        tests = []
        for s in strings:
            tests.append(normalize_keyword_text(s))

        self.assertTrue(tests is not None)
        self.assertTrue(len(set(tests)) == 1)
        self.assertTrue('+' not in next(iter(set(tests))))
