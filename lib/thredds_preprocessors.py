from lib.preprocessors import *

class ThreddsReader(BaseReader):
	_service_descriptors = {
		"title": "@name",
		"version": "@version"
	}

	def return_exclude_descriptors(self):
		excluded = self._service_descriptors.values()
		return [e[1:] for e in excluded]

	def parse_endpoints(self):
		pass