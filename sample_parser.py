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

	def identify_response_type(self, prepared_content, url):
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

		if 'http://www.isotc211.org/2005/gmi' in prepared_content \
			or 'http://www.isotc211.org/2005/gmd' in prepared_content:

			return 'ISO'
		elif 'http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0' in prepared_content:
			return 'THREDDS'
		elif 'http://a9.com/-/spec/opensearch/1.1/' in prepared_content:
			return 'OpenSearch'
		elif 'http://wadl.dev.java.net' in prepared_content:
			return 'WADL'
		elif 'http://www.opengis.net/wms' in prepared_content \
			or 'SERVICE=WMS' in url.upper() \
			or ('http://mapserver.gis.umn.edu/mapserver' in prepared_content \
				and 'SERVICE=WMS' in url.upper()):

			return 'WMS'
		elif 'http://www.opengis.net/wfs' in prepared_content \
			or 'SERVICE=WFS' in url.upper() \
			or ('http://mapserver.gis.umn.edu/mapserver' in prepared_content \
				and 'SERVICE=WFS' in url.upper()):

			return 'WFS'
		elif 'http://www.opengis.net/wcs' in prepared_content \
			or 'SERVICE=WCS' in url.upper() \
			or ('http://mapserver.gis.umn.edu/mapserver' in prepared_content \
				and 'SERVICE=WCS' in url.upper()):

			return 'WCS'			
		elif 'http://www.openarchives.org/OAI/' in prepared_content:
			#OAI-PMH as Dublin Core
			return 'OAI-PMH'

		return ''


