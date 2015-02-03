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

	def load_xml(self, prepared_content):
		try:
			parser = etree.XMLParser(encoding="utf-8")
		except ParseError as pe:
			print pe
			sys.exit(1)

	def return_service_descriptors(self):
		'''
		basic service information

		title
		abtract
		keywords

		'''
		for k, v in self._service_descriptors.iteritems():


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
			are always without the query parameter definitions (to acutally id the 
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
	pass
class WcsReader(WxsReader):
	pass
class WfsReader(WxsReader):
	pass