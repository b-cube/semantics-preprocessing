from lib.parser import BasicParser
from lib.utils import tidy_dict
from lib.xml_utils import extract_elems, extract_items
# from lib.identifier import Identify


class Processor(object):
    '''
    where routes is the tag sets to run as namespace-free
    xpath. the service, metadata and dataset keys are the dicts of
    tag lists (in case we have different locations for y) and the
    resultset list is the tag list to the result children
    '''
    _routes = {
        "service": {},
        "metadata": {},
        "dataset": {},
        "resultset": []
    }

    def __init__(self, identify, response, url, parent_url=''):
        self.response = response
        self.url = url
        self.identify = identify
        self.parent_url = parent_url

        self._load_xml()

    def parse(self):
        output = {}

        for k, v in self.identify.iteritems():
            if k == 'resultset':
                output[k] = self._parse_items()
            else:
                routes = self._routes.get(k, {})
                if routes:
                    output[k] = self._parse_route(routes)

        return tidy_dict(output)

    def _parse_route(self, routes):
        output = {}
        for key, items in routes.iteritems():
            if key == 'endpoint':
                # we need to do a thing that is different.
                output[key] = self._parse_endpoint()
            else:
                output[key] = []
                for item in items:
                    # run the xpaths (could be defined in different ways)
                    output[key] += extract_items(self.parser.xml, item)

        return tidy_dict(output)

    def _parse_items(self, item=None):
        if item is None:
            item = self.parser.xml
        subprocessor = SubProcessor(item)
        return subprocessor.parse_children()

    def _parse_endpoint(self):
        pass

    def _load_xml(self):
        self.parser = BasicParser(self.response)


class SubProcessor(object):
    def __init__(self, elem):
        self.elem = elem

    def _parse(self, item):
        return {}

    def parse_children(self, tags=[]):
        children = []
        if tags:
            children = extract_elems(self.elem, tags)
        else:
            children = [child for child in self.elem.iterchildren()]

        for child in children:
            parsed = self._parse(child)
            if parsed:
                yield parsed
