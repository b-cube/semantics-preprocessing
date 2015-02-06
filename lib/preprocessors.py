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
		if endpoints:
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




