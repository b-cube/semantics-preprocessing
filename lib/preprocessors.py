from lxml import etree
import sys
from copy import deepcopy

#note: this is from b-cube/semantics
from parser import Parser

'''
strip out some identified set of elements for the
triplestore/ontology definitions

strip out the rest of the text with associated, namespaced xpath
just in case?
'''

class BaseReader():
	'''

	parameters:
		_service_descriptors: dict containing the "generic" key and the xpath for 
			that element in the specific xml structure, ie abstract: idinfo/descript/abstract
	'''

	_service_descriptors = {}

	def __init__(self, response):
		self._response = response
		self._load_xml()

	def _load_xml(self):
		self.parser = Parser(self._response)

	def return_service_descriptors(self):
		'''
		basic service information

		title
		abtract

		note: what to do about keywords (thesaurus + list + type)?
		keywords

		'''
		service_elements = {}
		for k, v in self._service_descriptors.iteritems():
			elems = self.parser.find(v)
			if elems:
				service_elements[k] = [e.text for e in elems] if len(elems) > 0 else elems[0].text

		endpoints = self.parse_endpoints()
		if cendpoints:
			service_elements['endpoints'] = endpoints
		return service_elements

	def return_everything_else(self, excluded_elements):
		'''
		return any text value/attribute that wasn't extracted
		for the main service definition or endpoint definition
		or any ontology-related need
		'''
		return self.parser.find_nodes(excluded_elements)

	def parse_service(self):
		'''
		main service parsing method: pull all defined elements, 
			pull anything else text/attribute related

		returns:
			dict {service: 'anything ontology-driven', remainder: 'any other text/attribute value'}
		'''
		service = {
			"service": self.return_service_descriptors()
		}
		excluded = self.return_exclude_descriptors()
		service['remainder'] = self.return_everything_else(excluded)
		return service

	def return_exclude_descriptors(self):
		'''
		return a list of fully qualified xpaths used for the service description,
			endpoint description, etc, to flag those as "excluded" from the 
			rest of the xml parsing

		note:
			this might have certain nested structures depending on the service 
		'''
		pass

class IsoReader(BaseReader):
	pass

class ThreddsReader(BaseReader):
	pass

class OaiPmhReader(BaseReader):
	pass

class WadlReader(BaseReader):
	pass

class DifReader():
	pass

class FgdcReader():
	pass

class AtomReader():
	'''
	atom + opensearch + georss parsing as well
	'''
	pass

class WmsReader(BaseReader):
	_service_descriptors = {
		"title": "/{http://www.opengis.net/wms}WMS_Capabilities/{http://www.opengis.net/wms}Service/{http://www.opengis.net/wms}Title",
		"name": "/{http://www.opengis.net/wms}WMS_Capabilities/{http://www.opengis.net/wms}Service/{http://www.opengis.net/wms}Name",
		"abstract": "/{http://www.opengis.net/wms}WMS_Capabilities/{http://www.opengis.net/wms}Service/{http://www.opengis.net/wms}Abstract",
		"tags": "/{http://www.opengis.net/wms}WMS_Capabilities/{http://www.opengis.net/wms}Service/{http://www.opengis.net/wms}KeywordList/{http://www.opengis.net/wms}Keyword",
		"contact": "/{http://www.opengis.net/wms}WMS_Capabilities/{http://www.opengis.net/wms}Service/{http://www.opengis.net/wms}ContactInformation/{http://www.opengis.net/wms}ContactPersonPrimary",
		"minx": "/{http://www.opengis.net/wms}WMS_Capabilities/{http://www.opengis.net/wms}Capability/{http://www.opengis.net/wms}Layer/{http://www.opengis.net/wms}EX_GeographicBoundingBox/{http://www.opengis.net/wms}westBoundLongitude",
		"miny": "/{http://www.opengis.net/wms}WMS_Capabilities/{http://www.opengis.net/wms}Capability/{http://www.opengis.net/wms}Layer/{http://www.opengis.net/wms}EX_GeographicBoundingBox/{http://www.opengis.net/wms}southBoundLatitude",
		"maxx": "/{http://www.opengis.net/wms}WMS_Capabilities/{http://www.opengis.net/wms}Capability/{http://www.opengis.net/wms}Layer/{http://www.opengis.net/wms}EX_GeographicBoundingBox/{http://www.opengis.net/wms}eastBoundLongitude",
		"maxy": "/{http://www.opengis.net/wms}WMS_Capabilities/{http://www.opengis.net/wms}Capability/{http://www.opengis.net/wms}Layer/{http://www.opengis.net/wms}EX_GeographicBoundingBox/{http://www.opengis.net/wms}northBoundLatitude"
	}

	_endpoint_descriptors = {
		"GetCapabilities": {
				"formats": "/{http://www.opengis.net/wms}WMS_Capabilities/{http://www.opengis.net/wms}Capability/{http://www.opengis.net/wms}Request/{http://www.opengis.net/wms}GetCapabilities/{http://www.opengis.net/wms}Format",
				"url": "/{http://www.opengis.net/wms}WMS_Capabilities/{http://www.opengis.net/wms}Capability/{http://www.opengis.net/wms}Request/{http://www.opengis.net/wms}GetCapabilities/{http://www.opengis.net/wms}/DCPType/{http://www.opengis.net/wms}HTTP/{http://www.opengis.net/wms}Get/{http://www.opengis.net/wms}OnlineResource/@{http://www.w3.org/1999/xlink}href"

			},
			"GetMap": {
				"formats": "/{http://www.opengis.net/wms}WMS_Capabilities/{http://www.opengis.net/wms}Capability/{http://www.opengis.net/wms}Request/{http://www.opengis.net/wms}GetMap/{http://www.opengis.net/wms}Format",
				"url": "/{http://www.opengis.net/wms}WMS_Capabilities/{http://www.opengis.net/wms}Capability/{http://www.opengis.net/wms}Request/{http://www.opengis.net/wms}GetMap/{http://www.opengis.net/wms}/DCPType/{http://www.opengis.net/wms}HTTP/{http://www.opengis.net/wms}Get/{http://www.opengis.net/wms}OnlineResource/@{http://www.w3.org/1999/xlink}href"

			},
			"GetFeatureInfo": {
				"formats": "/{http://www.opengis.net/wms}WMS_Capabilities/{http://www.opengis.net/wms}Capability/{http://www.opengis.net/wms}Request/{http://www.opengis.net/wms}GetFeatureInfo/{http://www.opengis.net/wms}Format",
				"url": "/{http://www.opengis.net/wms}WMS_Capabilities/{http://www.opengis.net/wms}Capability/{http://www.opengis.net/wms}Request/{http://www.opengis.net/wms}GetFeatureInfo/{http://www.opengis.net/wms}/DCPType/{http://www.opengis.net/wms}HTTP/{http://www.opengis.net/wms}Get/{http://www.opengis.net/wms}OnlineResource/@{http://www.w3.org/1999/xlink}href"

			}
	}

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
					"url": "",
					"formats": ""
				},
				"GetFeature": {
					"url": "",
					"formats": ""
				}
			}
		},
		'1.0.0': {
			"service": {},
			"endpoint": {}
		}
	}

	def __init__(self):
		self._response = response
		self._load_xml()

		self._version = self.parser.xml.xpath('@version')

		assert self._version, 'missing wfs version'

		self._version = self._version[0]

		#setup up the xpaths at least
		self._service_descriptors = self._versions[version]['service']
		self._endpoint_descriptors = self._versions[version]['endpoint']


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












