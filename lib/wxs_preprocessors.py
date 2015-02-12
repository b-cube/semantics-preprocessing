from lib.preprocessors import *
from lib.utils import parse_gml_envelope

class WmsReader(BaseReader):
	_versions = {
		"1.3.0": {
			"service": {
				"title": "/{http://www.opengis.net/wms}WMS_Capabilities/{http://www.opengis.net/wms}Service/{http://www.opengis.net/wms}Title",
				"name": "/{http://www.opengis.net/wms}WMS_Capabilities/{http://www.opengis.net/wms}Service/{http://www.opengis.net/wms}Name",
				"abstract": "/{http://www.opengis.net/wms}WMS_Capabilities/{http://www.opengis.net/wms}Service/{http://www.opengis.net/wms}Abstract",
				"tags": "/{http://www.opengis.net/wms}WMS_Capabilities/{http://www.opengis.net/wms}Service/{http://www.opengis.net/wms}KeywordList/{http://www.opengis.net/wms}Keyword",
				"contact": "/{http://www.opengis.net/wms}WMS_Capabilities/{http://www.opengis.net/wms}Service/{http://www.opengis.net/wms}ContactInformation/{http://www.opengis.net/wms}ContactPersonPrimary"
			},
			"endpoint": {
				"GetCapabilities": {
					"formats": "/{http://www.opengis.net/wms}WMS_Capabilities/{http://www.opengis.net/wms}Capability/{http://www.opengis.net/wms}Request/{http://www.opengis.net/wms}GetCapabilities/{http://www.opengis.net/wms}Format",
					"url": "/{http://www.opengis.net/wms}WMS_Capabilities/{http://www.opengis.net/wms}Capability/{http://www.opengis.net/wms}Request/{http://www.opengis.net/wms}GetCapabilities/{http://www.opengis.net/wms}DCPType/{http://www.opengis.net/wms}HTTP/{http://www.opengis.net/wms}Get/{http://www.opengis.net/wms}OnlineResource/@{http://www.w3.org/1999/xlink}href"

				},
				"GetMap": {
					"formats": "/{http://www.opengis.net/wms}WMS_Capabilities/{http://www.opengis.net/wms}Capability/{http://www.opengis.net/wms}Request/{http://www.opengis.net/wms}GetMap/{http://www.opengis.net/wms}Format",
					"url": "/{http://www.opengis.net/wms}WMS_Capabilities/{http://www.opengis.net/wms}Capability/{http://www.opengis.net/wms}Request/{http://www.opengis.net/wms}GetMap/{http://www.opengis.net/wms}DCPType/{http://www.opengis.net/wms}HTTP/{http://www.opengis.net/wms}Get/{http://www.opengis.net/wms}OnlineResource/@{http://www.w3.org/1999/xlink}href"

				},
				"GetFeatureInfo": {
					"formats": "/{http://www.opengis.net/wms}WMS_Capabilities/{http://www.opengis.net/wms}Capability/{http://www.opengis.net/wms}Request/{http://www.opengis.net/wms}GetFeatureInfo/{http://www.opengis.net/wms}Format",
					"url": "/{http://www.opengis.net/wms}WMS_Capabilities/{http://www.opengis.net/wms}Capability/{http://www.opengis.net/wms}Request/{http://www.opengis.net/wms}GetFeatureInfo/{http://www.opengis.net/wms}DCPType/{http://www.opengis.net/wms}HTTP/{http://www.opengis.net/wms}Get/{http://www.opengis.net/wms}OnlineResource/@{http://www.w3.org/1999/xlink}href"

				}
			}
		}

	}

	def __init__(self, response):
		self._response = response
		self._load_xml()

		self._version = self.parser.xml.xpath('@version')

		assert self._version, 'missing wms version'

		self._version = self._version[0]

		#setup up the xpaths at least
		self._service_descriptors = self._versions[self._version]['service']
		self._endpoint_descriptors = self._versions[self._version]['endpoint']

	def return_exclude_descriptors(self):
		excluded = self._service_descriptors.values()

		for k, v in self._endpoint_descriptors.iteritems():
			excluded += v.values()

		return [e[1:] for e in excluded]
	
	def parse_endpoints(self):
		'''
		from osdd, it's a tuple (type, url, parameters)
		'''

		endpoints = []
		for k, v in self._endpoint_descriptors.iteritems():
			print k, v['url']
			endpoints.append(
				(
					k, 
					self.parser.find(v['url']),
					self.parser.find(v['formats'])
				)
			)

		return endpoints

	def parse_parameters(self):
		'''
		for any ogc, this can only be a hardcoded bit as parameter definitions
		but not for the supported values.
		'''
		return []


class WcsReader(BaseReader):
	pass



class WfsReader(BaseReader):
	#for v1.1.0
	_versions = {
		'1.1.0' :{
			"service": {
				"title": "/{http://www.opengis.net/wfs}WFS_Capabilities/{http://www.opengis.net/ows}ServiceIdentification/{http://www.opengis.net/ows}Title",
				"name": "/{http://www.opengis.net/wfs}WFS_Capabilities/{http://www.opengis.net/ows}ServiceIdentification/{http://www.opengis.net/ows}Name",
				"abstract": "/{http://www.opengis.net/wfs}WFS_Capabilities/{http://www.opengis.net/ows}ServiceIdentification/{http://www.opengis.net/ows}Abstract",
				"tags": "/{http://www.opengis.net/wfs}WFS_Capabilities/{http://www.opengis.net/ows}ServiceIdentification/{http://www.opengis.net/ows}KeywordList/{http://www.opengis.net/ows}Keyword",
				"contact": "/{http://www.opengis.net/wfs}WFS_Capabilities/{http://www.opengis.net/ows}ServiceProvider/{http://www.opengis.net/ows}ProviderName"
			},
			"endpoint": {
				"GetCapabilities": {
					"url": "/{http://www.opengis.net/wfs}WFS_Capabilities/{http://www.opengis.net/ows}OperationsMetadata/{http://www.opengis.net/ows}Operation[@{http://www.opengis.net/ows}name='GetCapabilities']/{http://www.opengis.net/ows}DCP/{http://www.opengis.net/ows}HTTP/{http://www.opengis.net/ows}Get/@{http://www.w3.org/1999/xlink}href",
					"formats": "/{http://www.opengis.net/wfs}WFS_Capabilities/{http://www.opengis.net/ows}OperationsMetadata/{http://www.opengis.net/ows}Operation[@{http://www.opengis.net/ows}name='GetCapabilities']/{http://www.opengis.net/ows}Parameter[@{http://www.opengis.net/ows}name='AcceptFormats']/{http://www.opengis.net/ows}Value"
				},
				"DescribeFeatureType": {
					"url": "/{http://www.opengis.net/wfs}WFS_Capabilities/{http://www.opengis.net/ows}OperationsMetadata/{http://www.opengis.net/ows}Operation[@{http://www.opengis.net/ows}name='DescribeFeatureType']/{http://www.opengis.net/ows}DCP/{http://www.opengis.net/ows}HTTP/{http://www.opengis.net/ows}Get/@{http://www.w3.org/1999/xlink}href",
					"formats": "/{http://www.opengis.net/wfs}WFS_Capabilities/{http://www.opengis.net/ows}OperationsMetadata/{http://www.opengis.net/ows}Operation[@{http://www.opengis.net/ows}name='DescribeFeatureType']/{http://www.opengis.net/ows}Parameter[@{http://www.opengis.net/ows}name='outputFormat']/{http://www.opengis.net/ows}Value"
				},
				"GetFeature": {
					"url": "/{http://www.opengis.net/wfs}WFS_Capabilities/{http://www.opengis.net/ows}OperationsMetadata/{http://www.opengis.net/ows}Operation[@{http://www.opengis.net/ows}name='GetFeature']/{http://www.opengis.net/ows}DCP/{http://www.opengis.net/ows}HTTP/{http://www.opengis.net/ows}Get/@{http://www.w3.org/1999/xlink}href",
					"formats": "/{http://www.opengis.net/wfs}WFS_Capabilities/{http://www.opengis.net/ows}OperationsMetadata/{http://www.opengis.net/ows}Operation[@{http://www.opengis.net/ows}name='GetFeature']/{http://www.opengis.net/ows}Parameter[@{http://www.opengis.net/ows}name='outputFormat']/{http://www.opengis.net/ows}Value"
				}
			}
		},
		'1.0.0': {
			"service": {
				"title": "/{http://www.opengis.net/wfs}WFS_Capabilities/{http://www.opengis.net/ows}Service/{http://www.opengis.net/ows}Title",
				"name": "/{http://www.opengis.net/wfs}WFS_Capabilities/{http://www.opengis.net/ows}Service/{http://www.opengis.net/ows}Name",
				"abstract": "/{http://www.opengis.net/wfs}WFS_Capabilities/{http://www.opengis.net/ows}Service/{http://www.opengis.net/ows}Abstract",
				"tags": "/{http://www.opengis.net/wfs}WFS_Capabilities/{http://www.opengis.net/ows}Service/{http://www.opengis.net/ows}KeywordList/{http://www.opengis.net/ows}Keyword",
				"contact": "/{http://www.opengis.net/wfs}WFS_Capabilities/{http://www.opengis.net/ows}Service/{http://www.opengis.net/ows}ContactInformation/{http://www.opengis.net/ows}ContactPersonPrimary"
			},
			"endpoint": {
				"GetCapabilities": {
					"url": "/{http://www.opengis.net/wfs}WFS_Capabilities/{http://www.opengis.net/wfs}Capability/{http://www.opengis.net/wfs}Request/{http://www.opengis.net/wfs}GetCapabilities/{http://www.opengis.net/wfs}DCPType/{http://www.opengis.net/wfs}HTTP/{http://www.opengis.net/wfs}Get/@{http://www.opengis.net/wfs}onineResource"
				},
				"DescribeFeatureType": {
					"url": "/{http://www.opengis.net/wfs}WFS_Capabilities/{http://www.opengis.net/wfs}Capability/{http://www.opengis.net/wfs}Request/{http://www.opengis.net/wfs}DescribeFeatureType/{http://www.opengis.net/wfs}DCPType/{http://www.opengis.net/wfs}HTTP/{http://www.opengis.net/wfs}Get/@{http://www.opengis.net/wfs}onineResource",
					"formats": "/{http://www.opengis.net/wfs}WFS_Capabilities/{http://www.opengis.net/wfs}Capability/{http://www.opengis.net/wfs}Request/{http://www.opengis.net/wfs}DescribeFeatureType/{http://www.opengis.net/wfs}SchemaDescriptionLanguage/{http://www.opengis.net/wfs}XMLSCHEMA/name()"
				},
				"GetFeature": {
					"url": "/{http://www.opengis.net/wfs}WFS_Capabilities/{http://www.opengis.net/wfs}Capability/{http://www.opengis.net/wfs}Request/{http://www.opengis.net/wfs}GetFeature/{http://www.opengis.net/wfs}DCPType/{http://www.opengis.net/wfs}HTTP/{http://www.opengis.net/wfs}Get/@{http://www.opengis.net/wfs}onineResource",
					"formats": "/{http://www.opengis.net/wfs}WFS_Capabilities/{http://www.opengis.net/wfs}Capability/{http://www.opengis.net/wfs}Request/{http://www.opengis.net/wfs}GetFeature/{http://www.opengis.net/wfs}ResultFormat/{http://www.opengis.net/wfs}GML2/name()"
				}
			}
		}
	}

	def __init__(self, response):
		self._response = response
		self._load_xml()

		self._version = self.parser.xml.xpath('@version')

		assert self._version, 'missing wfs version'

		self._version = self._version[0]

		#setup up the xpaths at least
		self._service_descriptors = self._versions[self._version]['service']
		self._endpoint_descriptors = self._versions[self._version]['endpoint']


	def return_exclude_descriptors(self):
		excluded = self._service_descriptors.values()


		return [e[1:] for e in excluded]

	def parse_endpoints(self):
		'''
		from osdd, it's a tuple (type, url, parameters)
		'''

		endpoints = []
		for k, v in self._endpoint_descriptors.iteritems():
			endpoints.append(
				(
					k, 
					self.parser.find(v['url']),
					self.parser.find(v['formats'])
				)
			)

		return endpoints

	def parse_parameters(self):
		'''
		for any ogc, this can only be a hardcoded bit as parameter definitions
		but not for the supported values.
		'''
		return []


class BaseOgcExtractor():

	_wxs_namespace_pattern = '{http://www.opengis.net/%(ns)s}'
	_service_patterns = {}
	_endpoint_patterns = {}

	def __init__(self, xml, service_type, prefix, namespaces):
		self.xml = xml
		self.service_type = service_type
		self.prefix = prefix
		self.namespaces = namespaces

		self.ns = self._wxs_namespace_pattern % {'ns': service_type.lower()}

	def generate_metadata_xpaths(self):
		'''

		'''
		return {
			k: [x % {"ns": self.ns, "upper": self.service_type.upper()} for x in v] 
				if isinstance(v, list) else v % {"ns": self.ns, "upper": self.service_type.upper()}
			for k, v in self._service_patterns.iteritems()
		}

	def generate_method_xpaths(self):
		pass

	def _strip_namespaces(self, string):
		'''
		strip out the namepspace from a tag and just return the tag
		'''
		return string.split('}')[-1]

	def _remap_namespaced_xpaths(self, xpath):
		'''
		and we don't really care for storage - we care for this path, this query
		'''

		for prefix, ns in self.namespaces.iteritems():
			wrapped_ns = '{%s}' % ns
			xpath = xpath.replace(wrapped_ns, prefix + ':')
		return xpath

class OwsExtractor(BaseOgcExtractor):
	'''
	to handle the more current OGC OWS metadata blocks (ows-namespaced blocks),
	we are just building xpath dictionaries

	build the ows metadata block (SERVICE description)
	build the endpoints by service_type & known available methods
	'''
	_service_patterns = {
		"title": "/%(ns)s%(upper)s_Capabilities/{http://www.opengis.net/ows}ServiceIdentification/{http://www.opengis.net/ows}Title",
		"name": "/%(ns)s%(upper)s_Capabilities/{http://www.opengis.net/ows}ServiceIdentification/{http://www.opengis.net/ows}Name",
		"abstract": "/%(ns)s%(upper)s_Capabilities/{http://www.opengis.net/ows}ServiceIdentification/{http://www.opengis.net/ows}Abstract",
		"tags": "/%(ns)s%(upper)s_Capabilities/{http://www.opengis.net/ows}ServiceIdentification/{http://www.opengis.net/ows}KeywordList/{http://www.opengis.net/ows}Keyword",
		"contact": "/%(ns)s%(upper)s_Capabilities/{http://www.opengis.net/ows}ServiceProvider/{http://www.opengis.net/ows}ProviderName"
	}
	_url_pattern = '/%(ns)s%(upper)s_Capabilities/{http://www.opengis.net/ows}OperationsMetadata'+ \
		'/{http://www.opengis.net/ows}Operation[@name="%(method)s"]/{http://www.opengis.net/ows}DCP/{http://www.opengis.net/ows}HTTP'+ \
		'/{http://www.opengis.net/ows}HTTP/{http://www.opengis.net/ows}%(type)s/@{http://www.w3.org/1999/xlink}href'

	_format_pattern = ''

	def generate_method_xpaths(self):

		return {}

class OgcExtractor(BaseOgcExtractor):
	'''
	for the older ogc services where the service metadata block is standard
	and we can make some decent assumptions about the capabilities

	and here's where the inconsistency in early wcs comes back to bite everyone.

	the xpaths are ugly because they have to be ugly for the excludes functionality.
	otherwise, yes, there are better ways.
	'''

	_service_patterns = {
		"title": [
			"/%(ns)s%(upper)s_Capabilities/%(ns)sService/%(ns)sTitle",
			"/%(ns)s%(upper)s_Capabilities/%(ns)sService/%(ns)stitle"
		],
		"name": [
			"/%(ns)s%(upper)s_Capabilities/%(ns)sService/%(ns)sName",
			"/%(ns)s%(upper)s_Capabilities/%(ns)sService/%(ns)sname"
		],
		"abstract": [
			"/%(ns)s%(upper)s_Capabilities/%(ns)sService/%(ns)sAbstract",
			"/%(ns)s%(upper)s_Capabilities/%(ns)sService/%(ns)sdescription"
		],
		"tags": [
			"/%(ns)s%(upper)s_Capabilities/%(ns)sService/%(ns)sKeywordList/%(ns)sKeyword",
			"/%(ns)s%(upper)s_Capabilities/%(ns)sService/%(ns)skeywords/%(ns)skeyword"
		],
		"contact": [
			"/%(ns)s%(upper)s_Capabilities/%(ns)sService/%(ns)sContactInformation/%(ns)sContactPersonPrimary",
			"/%(ns)s%(upper)s_Capabilities/%(ns)sService/%(ns)sresponsibleParty/%(ns)sorganisationName"
		]
	}

	_url_pattern = '/%(ns)s%(upper)s_Capabilities'+ \
		'/%(ns)sCapability/%(ns)sRequest'+ \
		'/%(local_ns)s%(method)s/%(ns)sDCPType'+ \
		'/%(ns)sHTTP/%(ns)s%(type)s'+ \
		'/%(ns)sOnlineResource/@{http://www.w3.org/1999/xlink}href'

	_format_pattern = '/%(ns)s%(upper)s_Capabilities'+ \
		'/%(ns)sCapability/%(ns)sRequest'+ \
		'/%(local_ns)s%(method)s/%(ns)sFormat'

	def generate_method_xpaths(self):
		'''
		for any capablility/request, pull the dcptype & link
		note that we can have standard ogc methods and extended service support
			through other namespaces

		and we're parsing the metadata to figure out how we should parse the metadata
		'''
		request_xpaths = ["/%(ns)s%(upper)s_Capabilities/%(ns)sCapability/%(ns)sRequest/%(ns)s*" % {
				"ns": self.ns, 
				"upper": self.service_type.upper()
			},
			"/%(ns)s%(upper)s_Capabilities/%(ns)sCapability/%(ns)sRequest/*[namespace-uri() != '%(ns_unbracketed)s']" % {
				"ns": self.ns, 
				"upper": self.service_type.upper(),
				"ns_unbracketed": self.ns[1:-1]
			}
		]

		endpoint_xpaths = {}
		for request_xpath in request_xpaths:
			xpath = self._remap_namespaced_xpaths(request_xpath)

			request_pattern = "%(ns)sDCPType/%(ns)sHTTP/%(ns)s*" % {"ns": self.ns}
			request_pattern = self._remap_namespaced_xpaths(request_pattern)

			requests = self.xml.xpath(xpath, namespaces=self.namespaces)
			
			for request in requests:
				method = self._strip_namespaces(request.tag)
				local_ns = request.tag[:request.tag.index('}') + 1]

				urls = request.xpath(request_pattern, namespaces=self.namespaces)
				methods = []
				for url in urls:
					request_method = self._strip_namespaces(url.tag)

					url_xpath = self._url_pattern % {"ns": self.ns, 
						'upper': self.service_type.upper(), 
						'method': method, 
						'type': request_method,
						'local_ns': local_ns
					}
				
					methods.append((request_method, url_xpath))

				endpoint_xpaths[method] = [{
					"url": m[1],
					"request_type": m[0],
					"parameters": self.return_parameters(method, local_ns) 
				} for m in methods]

		return endpoint_xpaths

	def return_parameters(self, method, local_ns):
		'''
		where the format element(s) 
		'''
		parameters = []

		#this is the enumeration
		formats = self._format_pattern % {"ns": self.ns, 
			'upper': self.service_type.upper(), 
			'method': method,
			'local_ns': local_ns
		}

		return parameters

	
		






