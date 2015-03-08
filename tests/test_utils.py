import unittest
from lib.nlp_utils import normalize_keyword_text, collapse_to_bag
from lib.yaml_configs import import_yaml_configs
from lib.utils import flatten


class TestUtils(unittest.TestCase):
    def setUp(self):
        pass

    def test_flatten(self):
        '''
        test flatten outside of bag of words
        '''
        # let's not do anything (but don't screw it up)
        basic_list = ['a', 'b', 'c']
        flattened = flatten(basic_list)
        self.assertTrue(flattened)
        self.assertTrue(basic_list == flattened)

        complex_list = ['a', 'b', 'c', ['d', 'e'], 'f', [['g', 'h'], 'i']]
        flattened = flatten(complex_list)
        self.assertTrue(flattened)
        self.assertFalse(complex_list == flattened)
        self.assertTrue('g' in flattened)


class TestYamlImport(unittest.TestCase):
    def setUp(self):
        '''
        nothing to set up
        '''
        pass

    def test_import(self):
        paths = [
            'lib/configs/fgdc_identifier.yaml',
            'lib/configs/thredds_identifier.yaml'
        ]

        config = import_yaml_configs(paths)

        self.assertTrue(len(config) == 2)
        self.assertTrue(config[1]['name'] == 'UNIDATA')


class TestNlpUtils(unittest.TestCase):
    def setUp(self):
        pass

    def test_keywords(self):
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

    def test_collapse_to_bag(self):
        '''
        for some irregular lists, and a dict of stuff
        and a single string
        '''

        simple_bag = collapse_to_bag("This is just a sentence.")

        self.assertTrue(simple_bag)
        self.assertTrue(simple_bag == "This is just a sentence.")

        complex_bag = {
            "first": ""
        }
