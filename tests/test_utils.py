# -*- coding: utf-8 -*-

import unittest
from lib.nlp_utils import normalize_keyword_text, normalize_subjects
from lib.nlp_utils import collapse_to_bag
from lib.nlp_utils import is_english
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
            # 'soil-clay-pedon-loam-sandy loam', # removed from regex
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

        # a better test
        new_strings = normalize_subjects(strings, False, True)
        self.assertTrue(len(new_strings) == 1)

        new_strings = normalize_subjects(strings, False, False)
        self.assertTrue(len(new_strings) == 4)

    def test_collapse_to_bag(self):
        '''
        for some irregular lists, and a dict of stuff
        and a single string
        '''

        simple_bag = collapse_to_bag("This is just a sentence.")

        self.assertTrue(simple_bag)
        self.assertTrue(simple_bag == "This is just a sentence.")

        complex_source = {
            "first": "This is just a sentence.",
            "second": ["Likely an abstract", "or possibly a description"],
            "third": {
                "type": "irony?",
                "url": "http://www.irony.com"
            }
        }
        complex_bag = collapse_to_bag(complex_source, False)
        expected_bag = '''Likely an abstract or possibly a description http://www.irony.com irony? This is just a sentence.'''
        self.assertTrue(complex_bag == expected_bag)

        # without the url
        complex_bag = collapse_to_bag(complex_source)
        expected_bag = '''Likely an abstract or possibly a description irony? This is just a sentence.'''
        self.assertTrue(complex_bag == expected_bag)

    def test_language_detection(self):
        expected_english = '''we know that keywords are handled in
            a variety of ways even in standards'''
        expected_german = u'''Landesamt für innere Verwaltung Mecklenburg-Vorpommern;
            Amt für Geoinformation, Vermessung und Katasterwesen'''
        expected_romance = 'Vada dritto! e poi giri a destra'

        self.assertTrue(is_english(expected_english))
        self.assertFalse(is_english(expected_german))
        self.assertFalse(is_english(expected_romance))
