import re

from lib.preprocessors import BaseReader
from lib.utils import parse_url


class OpenSearchReader(BaseReader):
	_service_descriptors = {
		"title": "/{http://a9.com/-/spec/opensearch/1.1/}OpenSearchDescription/{http://a9.com/-/spec/opensearch/1.1/}ShortName",
		"abstract": "/{http://a9.com/-/spec/opensearch/1.1/}OpenSearchDescription/{http://a9.com/-/spec/opensearch/1.1/}LongName", 
		"description": "/{http://a9.com/-/spec/opensearch/1.1/}OpenSearchDescription/{http://a9.com/-/spec/opensearch/1.1/}Description",
		"source": "/{http://a9.com/-/spec/opensearch/1.1/}OpenSearchDescription/{http://a9.com/-/spec/opensearch/1.1/}Attribution",
		"contact": "/{http://a9.com/-/spec/opensearch/1.1/}OpenSearchDescription/{http://a9.com/-/spec/opensearch/1.1/}Developer",
		"rights": "/{http://a9.com/-/spec/opensearch/1.1/}OpenSearchDescription/{http://a9.com/-/spec/opensearch/1.1/}SyndicationRight",
		"language": "/{http://a9.com/-/spec/opensearch/1.1/}OpenSearchDescription/{http://a9.com/-/spec/opensearch/1.1/}Language",
		"subject": "/{http://a9.com/-/spec/opensearch/1.1/}OpenSearchDescription/{http://a9.com/-/spec/opensearch/1.1/}Tags"
	}
	_to_exclude = [
		'/{http://a9.com/-/spec/opensearch/1.1/}OpenSearchDescription/{http://a9.com/-/spec/opensearch/1.1/}Url'
	]

	_parameter_formats = {
        "geo:box": "west, south, east, north",
        "time:start": "YYYY-MM-DDTHH:mm:ssZ",
        "time:stop": "YYYY-MM-DDTHH:mm:ssZ"
    }

	def return_exclude_descriptors(self):
		excluded = self._service_descriptors.values()
		return [e[1:] for e in excluded] + self._to_exclude

	def parse_endpoints(self):
		'''

		'''
		urls = self.parser.find('/{http://a9.com/-/spec/opensearch/1.1/}OpenSearchDescription/{http://a9.com/-/spec/opensearch/1.1/}Url')

		endpoints = [
			(
				url.get('type', ''),
				url.get('template', ''),
				self._extract_url_parameters(url.get('template', ''))
			) for url in urls 
		]

		return endpoints

	def _extract_parameter_type(self, param):
		'''
		return prefix, type from a string as prefix:type or {prefix:type}
		as tuple (prefix, type)
		'''
		pattern = '\{{0,1}(\S*):([\S][^}]*)'

		#TODO: this is probably a bad assumption (that there's just the 
		#	one item in the list, not that urlparse returns the terms as a list)
		if isinstance(param, list):
			param = param[0]

		if ':' not in param:
			return ('', param)

		m = re.search(pattern, param)
		return m.groups()
 
	def _extract_url_parameters(self, url):
		'''
		strip out the osdd url parameters

		note: not always emitted correctly as param={thing?}. could also be param=thing

		tuple: (parameter name, namespace(s), param namespace prefix, param type, format)
		'''
		assert url, 'No URL'

		query_params = parse_url(url)
		#deal with the namespaced parameters as [query param key, prefix, type]
		query_params = [[k] + list(self._extract_parameter_type(v)) for k, v in query_params.iteritems()]

		return [
			(
				qp[0], 
				self.parser._namespaces,
				qp[1],
				qp[2],
				self._parameter_formats.get(':'.join(qp[1:]))
			)
			for qp in query_params
		]


