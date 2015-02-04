from lxml import etree
import sys

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

	def _load_xml(self):
		#TODO: add the encoding widgetry
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
				service_elements[k] = elements
		return service_elements

	def return_everything_else(self, excluded_elements):
		'''
		so not service descriptors and not anything else that
		may be extracted based on the service type (so deepcopy + append)
		'''
		#TODO: parse the results of this (it's pretty nasty) into 
		#      something that at least understands prefix, namespace uri, value
		return self.parser.find_text_nodes(excluded_elements)

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

class WxsReader(BaseReader):
	'''
	generic getcapabilities parsing

	note:
		we are ignoring layers right now and the fact that the endpoint urls
			are always without the query parameter definitions (to actually id the 
			things). 
	
		we are not ignoring the parent layer element - it contains the bbox(es)
	'''

	def parse_capabilities(self):
		'''
		this is the Capability element containing the supported
		service endpoints
		'''
		pass

class WmsReader(WxsReader):
	_service_descriptors = {
		"title": "{http://www.opengis.net/wms}WMS_Capabilities/{http://www.opengis.net/wms}Service/{http://www.opengis.net/wms}Title",
		"name": "{http://www.opengis.net/wms}WMS_Capabilities/{http://www.opengis.net/wms}Service/{http://www.opengis.net/wms}Name'",
		"abstract": "{http://www.opengis.net/wms}WMS_Capabilities/{http://www.opengis.net/wms}Service/{http://www.opengis.net/wms}Abstract",
		"tags": "{http://www.opengis.net/wms}WMS_Capabilities/{http://www.opengis.net/wms}Service/{http://www.opengis.net/wms}KeywordList/{http://www.opengis.net/wms}Keyword",
		"contact": "{http://www.opengis.net/wms}WMS_Capabilities/{http://www.opengis.net/wms}Service/{http://www.opengis.net/wms}ContactInformation/{http://www.opengis.net/wms}ContactPersonPrimary" 
	}
	
	def parse_capabilities(self):
		'''
		go get the bboxes, endpoints, etc
		'''

		endpoint_descriptors = {
			"GetCapabilities": {
				"formats": "{http://www.opengis.net/wms}WMS_Capabilities/{http://www.opengis.net/wms}Capability/{http://www.opengis.net/wms}Request/{http://www.opengis.net/wms}GetCapabilities/{http://www.opengis.net/wms}Format",
				"url": "{http://www.opengis.net/wms}WMS_Capabilities/{http://www.opengis.net/wms}Capability/{http://www.opengis.net/wms}Request/{http://www.opengis.net/wms}GetCapabilities/{http://www.opengis.net/wms}/DCPType/{http://www.opengis.net/wms}HTTP/{http://www.opengis.net/wms}Get/{http://www.opengis.net/wms}OnlineResource/{}@href"

			},
			"GetMap": {}

		}

		endpoints = [
			(

			)
		]



class WcsReader(WxsReader):
	pass
class WfsReader(WxsReader):
	pass