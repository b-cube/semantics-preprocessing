import unittest
from lib.parser import Parser
import os
import json


class TestParser(unittest.TestCase):
    def setUp(self):
    	'''
    	we are assuming input from the solr sample parser 
    	so this is the encoded, cdata-removed input

    	except i have blended the two a bit (handling that \\n issue
    		in the parser vs the cdata issue in the solr response)

		so init the parser with a file that reflects that
    	'''
    	with open('tests/test_data/basic_osdd_c1576284036448b5ef3d16b2cd37acbc.txt', 'r') as f:
    		data = f.read()

        self.parser = Parser(data)

    def test_parse_xml(self):
    	'''
		the _parse is called from init
    	'''

    	self.assertTrue(self.parser.xml is not None)
    	self.assertTrue(len(self.parser._namespaces) > 0)

    def test_remap_namespaced_paths(self):
    	in_xpath = '{http://a9.com/-/spec/opensearch/1.1/}OpenSearchDescription/{http://a9.com/-/spec/opensearch/1.1/}Image'
    	out_xpath = 'default:OpenSearchDescription/default:Image'

    	test_xpath = self.parser._remap_namespaced_xpaths(in_xpath)

    	self.assertTrue(test_xpath == out_xpath)


    def test_find_nodes(self):
    	nodes = self.parser.find_nodes()

    	self.assertTrue(len(nodes) == 5)
    	self.assertTrue(len(nodes[2][2]) == 3)
    	self.assertTrue(nodes[1][0] == 'UTF-8')

    	#run with excludes
    	excludes = [
    		'{http://a9.com/-/spec/opensearch/1.1/}OpenSearchDescription/{http://a9.com/-/spec/opensearch/1.1/}InputEncoding',
    		'{http://a9.com/-/spec/opensearch/1.1/}OpenSearchDescription/{http://a9.com/-/spec/opensearch/1.1/}Image/@width'
    	]
    	nodes = self.parser.find_nodes(excludes)
    	self.assertTrue(len(nodes) == 4)
    	self.assertTrue(len(nodes[1][2]) == 2)
    	self.assertTrue(nodes[0][0] == 'CEOS')
    	self.assertTrue(nodes[1][2][1][0] == '16')
    	self.assertTrue(nodes[1][2][0][1] == '{http://a9.com/-/spec/opensearch/1.1/}OpenSearchDescription/{http://a9.com/-/spec/opensearch/1.1/}Image/@type')