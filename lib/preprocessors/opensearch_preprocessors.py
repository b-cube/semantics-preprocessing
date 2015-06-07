import re

from lib.base_preprocessors import BaseReader
from lib.utils import parse_url, tidy_dict
from lib.xml_utils import extract_item, extract_items, generate_localname_xpath
from lib.xml_utils import extract_elem, extract_elems


class OpenSearchReader(BaseReader):
    _service_descriptors = {
        "title": ["OpenSearchDescription", "ShortName"],
        "abstract": [["OpenSearchDescription", "LongName"],
                     ["OpenSearchDescription", "Description"]],
        "source": ["OpenSearchDescription", "Attribution"],
        "contact": ["OpenSearchDescription", "Developer"],
        "rights": ["OpenSearchDescription", "SyndicationRight"],
        "subject": ["OpenSearchDescription", "Tags"]
    }

    _parameter_formats = {
        "geo:box": "west, south, east, north",
        "time:start": "YYYY-MM-DDTHH:mm:ssZ",
        "time:stop": "YYYY-MM-DDTHH:mm:ssZ"
    }

    def parse_endpoints(self):
        '''

        '''
        urls = extract_elems(self.parser.xml, ["OpenSearchDescription", "Url"])

        endpoints = [
            tidy_dict({
                "protocol": self._remap_http_method(url.get('type', '')),
                "url": url.get('template', ''),
                "parameters": self._extract_url_parameters(url.get('template', '')),
                "actionable": 0 if 'rel' not in url.attrib.keys() else 2
            }) for url in urls
        ]

        return endpoints

    def _extract_parameter_type(self, param):
        '''
        return prefix, type from a string as prefix:type or {prefix:type}
        as tuple (prefix, type)
        '''
        pattern = '\{{0,1}(\S*):([\S][^}]*)'

        # TODO: this is probably a bad assumption (that there's just the
        #   one item in the list, not that urlparse returns the terms as a list)
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
              except the param=thing is probably a hardcoded term SO HOW DO WE MANAGE THAT?
              TODO: manage that (ex: ?product=MOD021QA&amp;collection={mp:collection?})

        tuple: (parameter name, namespace(s), param namespace prefix, param type, format)
        '''
        assert url, 'No URL'

        query_params = parse_url(url)
        # deal with the namespaced parameters as [query param key, prefix, type]
        query_params = [[k] + list(self._extract_parameter_type(v)) for k, v
                        in query_params.iteritems()]

        return [
            tidy_dict({
                "name": qp[0],
                "namespaces": self.parser._namespaces,
                "prefix": qp[1],
                "type": qp[2],
                "format": self._parameter_formats.get(':'.join(qp[1:]))
            })
            for qp in query_params
        ]
