#!/anaconda/bin/python

import os
import argparse
import json
import requests
import sys
import random
import urllib
import yaml

'''
a little cli to generate sets of solr documents

yaml query file
---------------
fields:
	- raw_content
	- id
	- date
sample:
	start: 0
	end: 10
	size: 3
query: 
  field:value

'''

class Solr():
	'''
	the solr "connection"
	'''
	def __init__(self, host, collection, port='', auth=()):
		self._host = host
		self._collection = collection
		if port:
			self._port = port
		if auth:
			self._auth = auth

		self.url = self._generate_url()

	def _generate_url(self):
		host = 'http://' + self._host
		if self._port:
			host += ':' + self._port
		return '/'.join([host, 'solr', '#', self._collection, 'query'])

	def execute_request(self, query):
		'''
		make the solr request based on the initial url settings
		and the query block
		'''
		url = '?'.join(self._url, self._generate_qs_from_query(query))

		if self._auth:	
			req = requests.get(url, auth=self._auth)
		else:
			req = requests.get(url)

		assert req.status_code == 200, 'failed request: %s' % url

		return req.content

class Query():
	'''
	read and build a solr query string from the options in the 
	yaml input file.

	special handling for the sample element (return some number of 
		documents between index x and y) -> converted to limit/offset structures
	'''

	_key_mappings = {
		'query': 'q',
		'ext': 'wt', 
		'fields': 'fl'
	}

	def __init__(self):
		pass

	def open_yaml(self, yaml_file):
		assert os.path.exists(yaml_path)

		with open(yaml_file, 'r') as f:
			text = f.read()

		self._yaml = yaml.load(text)

	def build_queries(self):
		'''
		build the query string from the parsed yaml

		?q=raw_content%3A+(soil+OR+pedon+OR+sand+OR+silt+OR+clay)&rows=50&fl=id%2Craw_content&wt=json&indent=true
		?q=raw_content:+(soil+OR+pedon+OR+sand+OR+silt+OR+clay)&rows=50&fl=id,raw_content&wt=json&indent=true

		?q=content%3ARGIS+and+raw_content%3Asoil&start=12&rows=1&wt=json&indent=true
		'''
		kvp = {}
		for k, v in self._key_mappings.iteritems():
			if k in self._yaml:
				if k == 'query':
					#where v is a kvp
					value = self._convert_value_to_solr(self._yaml[k])
					if value:
						kvp[v] = value
				elif k == 'fields':
					kvp[v] = ','.join(self._yaml[k])
				else:
					kvp[v] = self._yaml[k]

		query = self._convert_kvp_to_qs(kvp)

		#if the yaml includes a sample, we need multiple start, rows requests
		queries = []
		if 'sample' in self._yaml:
			#append the additional start, rows to the end of the query string
			range_values = xrange(self._yaml['sample']['start'], self._yaml['sample']['end'])
			indices = random.sample(range_values, self._yaml['sample']['size'])
			queries += [query + self._convert_sample(index) for index in indices]

		return queries if queries else [query]

	def _convert_kvp_to_qs(self, kvp):
		'''
		well. that just got a little silly.
		urllib urlencode doesn't handle the + or paren in a way
		solr finds acceptable.
		'''
		qs = '?' + '&'.join([k + '=' + v for k, v in kvp.iteritems()])
		qs = qs.replace(':', '%3A').replace(',', '%2C')
		return qs
		
	def _convert_sample(self, index):	
		return '&start=%s&rows=1' % index

	def _convert_value_to_solr(self, value):
		if isinstance(value, str):
			return value
		elif isinstance(value, list):
			return '+(%s)' % '+OR+'.join(value)
		elif isinstance(value, dict):
			return ' AND '.join([':'.join([k, self._convert_value_to_solr(v)]) for k, v in value.iteritems()])
		else:
			return None

def main():
	parser = argparse.ArgumentParser(description='CLI to pull records from the nutch solr instance.')

	parser.add_argument('-s', '--solr', help='Host or ip address of the solr instance', required=True)
	parser.add_argument('-p', '--port', help='Port of the solr instance')
	parser.add_argument('-c', '--collection', help='Collection to query of the solr instance', required=True)
	parser.add_argument('-U', '--user', help='User name if solr requires authenticated access')
	parser.add_argument('-P', '--password', help='Password if solr requires authenticated access')
	parser.add_argument('-q', '--query', help='Input file for the query definition (yaml)')
	parser.add_argument('-o', '--output', help='Output file path for solr response', required=True)

	args = parser.parse_args()

	print args

if __name__ == '__main__':
     main()

