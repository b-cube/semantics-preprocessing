from lxml import etree

from lib.parser import BasicParser
from lib.utils import tidy_dict

'''
we are doing away with any pretext of namespace-caring
today. so just a parser that does some tidying and
then the magic of local-names (where again, not worried
    about speed so much).

note: no effs given about py3 either.
'''


class BaseReader():
    '''

    parameters:
        _service_descriptors: dict containing the "generic" key
            and the xpath for that element in the specific xml
            structure, ie abstract: idinfo/descript/abstract
    '''

    _service_descriptors = {}

    def __init__(self, response, url):
        self._response = response
        self._url = url
        self._load_xml()

    def _load_xml(self):
        self.parser = BasicParser(self._response)

    def _remap_http_method(self, original_method):
        '''
        return the "full" http method from some input
        '''
        definition = {
            "HTTP GET": ['get'],
            "HTTP POST": ['post']
        }
        for k, v in definition.iteritems():
            if original_method.lower() in v:
                return k
        return original_method

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
            # v can be a list of possible xpaths where we want
            # to keep all returned values from any xpath within
            items = []
            xpaths = v if isinstance(v, list) else [v]
            for xp in xpaths:
                if '@' in xp[-1]:
                    items = extract_attribs(self.parser.xml, xp)
                else:
                    items += extract_items(self.parser.xml, xp)

            service_elements[k] = items

        endpoints = self.parse_endpoints()
        if endpoints:
            service_elements['endpoints'] = endpoints
        return service_elements

    def return_dataset_descriptors(self):
        '''
        no generic handling for this unfortunately.
        '''
        pass

    def return_metadata_descriptors(self):
        '''
        no generic handling for this unfortunately.
        '''
        pass

    def parse_service(self):
        '''
        main service parsing method: pull all defined elements,
            pull anything else text/attribute related

        returns:
            dict {service: 'anything ontology-driven', remainder: 'any other text/attribute value'}
        '''
        service = {
            "service": self.return_service_descriptors(),
            "dataset": self.return_dataset_descriptors(),
            "metadata": self.return_metadata_descriptors()
        }
        excluded = self.return_exclude_descriptors()
        service['remainder'] = self.return_everything_else(excluded)
        self.service = tidy_dict(service)

        return self.service

    def parse_endpoints(self):
        return []
