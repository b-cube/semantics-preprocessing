from lib.preprocessors import *

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

	def return_exclude_descriptors(self):
		excluded = self._service_descriptors.values()
		return [e[1:] for e in excluded]

	def parse_endpoints(self):
		pass


