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

	_pttn = u'^<!\[CDATA\[(.*?)\]\]>$'

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

		#unicode escape for solr (cdata pattern matching fails without)
		raw_content = raw_content.encode('unicode_escape')

		m = re.search(self._pttn, raw_content)

		assert m

		return m.group(1)

	#TODO: This might turn into a much larger thing (combinations of namespaces, etc)
	def identify_response_type(self, prepared_content):
		'''
		let's try to identify what kind of service response it 
		is based on the namespaces

		PRIORITY:
			opensearch
			opensearch esip
			thredds catalog
			OAI-PMH
			iso
			ogc getcapabilities
			wadl
		'''

		if 'http://www.isotc211.org/2005/gmi' in raw_content:
			return 'ISO'
		elif 'http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0' in raw_content:
			return 'THREDDS'
		elif 'http://a9.com/-/spec/opensearch/1.1/' in raw_content:
			return 'OpenSearch'
		elif 'http://wadl.dev.java.net/2009/02' in raw_content:
			return 'WADL'
		elif 'http://schemas.xmlsoap.org/wsdl/' in raw_content:
			return 'WSDL'
		elif 'http://www.w3.org/2005/Atom' in raw_content:
			'''
			note: this can be some combination of atom, opensearch, and georss content
			'''
			return 'ATOM'
		elif 'http://www.opengis.net/wms' in raw_content:
			return 'WMS'
		elif 'http://www.opengis.net/wfs' in raw_content:
			return 'WFS'
		elif 'http://gcmd.gsfc.nasa.gov/Aboutus/xml/dif/' in raw_content:
			return 'DIF'
		elif 'http://www.openarchives.org/OAI/2.0/oai_d c/' in raw_content:
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
		elif 'http://www.incident.com/cap/1.0' in raw_content:
			'''
			usgs alerts
				view-source:http://www.usgs.gov/alerts/cap/USGS-landslides.20060831T184846
			'''
			return 'CAP-ALERT'


		return ''


