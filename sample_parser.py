#!/anaconda/bin/python

import os
import argparse
import json
import codecs
import re
import sys


import yaml

'''
base nutch/solr response parser
'''

class FileParser():
	'''
	from a file, return a tuple of id, date, raw_content
	objects from sample data file (basically a json solr response
		untouched from the solr cli)
	'''

	_pttn = u'^<!\[CDATA\[(.*?)\]\]>'

	def __init__(self):
		pass

	def parse_file(self, file_path):

		assert os.path.exists(file_path)

		with open(file_path, 'r') as f:
			text = f.read()

		response = json.loads(text)
		return [(j['id'], j['date'], j['raw_content']) for j in response['responses']['docs']]

	
	def prepare_raw_content(self, raw_content):
		'''
		string from the solr raw_content element, unmodified
		'''	

		#unicode escape (solr?)
		raw_content = raw_content.encode('unicode_escape')

		#regex for the CDATA
		#TODO: there are internal CDATAs so neat, i guess
		m = re.search(self._pttn, raw_content)
		assert m

		raw_content = m.group(1)

		#there is a certain amount of cargocult encoding right here.
		return raw_content.decode('string_escape').strip().decode('unicode_escape').encode('utf-8')

	def identify_response_type(self, prepared_content):
		'''
		let's try to identify what kind of service response it 
		is based on the namespaces

		no namespaces:
			FGDC
			zenodo
		'''

		if 'http://www.isotc211.org/2005/gmi' in raw_content:
			return 'ISO'
		elif 'http://www.w3.org/2005/Atom' in raw_content:
			return 'ATOM'
		elif 'http://www.opengis.net/wms' in raw_content:
			return 'WMS'
		elif 'http://gcmd.gsfc.nasa.gov/Aboutus/xml/dif/' in raw_content:
			return 'DIF'
		elif 'http://www.openarchives.org/OAI/2.0/oai_dc/' in raw_content:
			#OAI-PMH as Dublin Core
			return 'OAI-PMH'
		elif 'http://pds.nasa.gov/pds4/pds/v1' in raw_content:
			return 'PDS'
		elif 'http://www.loc.gov/MARC21/slim' in raw_content:
			return 'MARC21'
		elif '<metstdv>FGDC-STD-001-1998' in raw_content:
			return 'FGDC-1998'
		elif '<metstdv>FGDC-STD-012-2002' in raw_content:
			return 'FGDC-2002'

		return ''


