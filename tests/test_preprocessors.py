import unittest
import os
import json

from lib.parser import Parser
from lib.preprocessors import *
from lib.wxs_preprocessors import *
from lib.thredds_preprocessors import *
from lib.oaipmh_preprocessors import *

class TestBaseReader(unittest.TestCase):
	def setUp(self):    	
		pass

	def test_load_xml(self):
		#honestly, this is just a parser test

		pass

	def test_return_descriptors(self):
		pass

	def return_everything_else(self):
		pass

class TestWmsReader(unittest.TestCase):
	def setUp(self):   
		with open('tests/test_data/esri_wms_35bd4e2ce8cd13e8697b03976ffe1ee6.txt', 'r') as f:
			text = f.read() 	
		self.reader = WmsReader(text)
		self.reader._load_xml()

	def test_load_xml(self):
		#honestly, this is just a parser test

		self.assertTrue(self.reader.parser is not None)
		self.assertTrue(self.reader.parser.xml is not None)

	def test_return_descriptors(self):
		descriptors = self.reader.return_service_descriptors()

		self.assertTrue(descriptors is not None)

	def return_everything_else(self):
		nodes = self.reader.return_everything_else({})

		self.assertTrue(nodes is not None)

class TestThreddsReader(unittest.TestCase):
	def setUp(self):  
		#this response doesn't come from nay harvest 
		with open('tests/test_data/thredds_catalog_eol.xml', 'r') as f:
			text = f.read() 	
		self.reader = ThreddsReader(text)
		self.reader._load_xml()

	def test_return_descriptors(self):
		descriptors = self.reader.return_service_descriptors()
		
		self.assertTrue('Actinic Flux' in descriptors['title'])
		self.assertTrue(descriptors['version'] == "1.0.2")

	def test_return_everything_else(self):
		excluded = self.reader.return_exclude_descriptors()
		remainder = self.reader.return_everything_else(excluded)

		self.assertTrue(len(remainder) > 0)
		self.assertTrue(remainder[1][2][0][0] == 'codiac_order')
		self.assertTrue(remainder[2][1] == '{http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0}catalog/{http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0}dataset')


class TestOaiPmhReader(unittest.TestCase):
	def setUp(self):  
		#this response doesn't come from nay harvest 
		with open('tests/test_data/oaipmh_identify.xml', 'r') as f:
			text = f.read() 	
		self.reader = OaiPmhReader(text)
		self.reader._load_xml()

	def test_return_descriptors(self):
		descriptors = self.reader.return_service_descriptors()
		
		self.assertTrue('Aberdeen' in descriptors['title'])
		self.assertTrue(descriptors['version'] == "2.0")
		self.assertTrue(descriptors['source'] == 'http://aura.abdn.ac.uk/dspace-oai/request')









