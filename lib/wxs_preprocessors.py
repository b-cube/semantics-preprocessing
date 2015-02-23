from lib.preprocessors import *
import json


class WmsReader(BaseReader):

    def __init__(self, response):
        self._response = response
        self._load_xml()

        self._version = self.parser.xml.xpath('@version')

        assert self._version, 'missing wms version'

        self._version = self._version[0]

        # setup up the xpaths at least
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
    def __init__(self, response):
        self._response = response
        self._load_xml()

        self._version = self.parser.xml.xpath('@version')

        assert self._version, 'missing wfs version'

        self._version = self._version[0]

        extractor = OwsExtractor(self.parser.xml, self._version, 'wfs', 'wfs', self.parser._namespaces) \
            if self._version in ['1.1.0'] else OgcExtractor(self.parser.xml, self._version, 'wfs', 'wfs', self.parser._namespaces)

        self._service_descriptors = extractor.generate_metadata_xpaths()
        self._endpoint_descriptors = extractor.generate_method_xpaths()

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


class OgcDefaults():
    '''
    a container for the parameter definitions
    '''
    def __init__(self, service_type, version):
        with open('lib/ogc_parameter_defaults.json', 'r') as f:
            self.defaults = json.loads(f.read())

        self.defaults = self._get_defaults(service_type, version)

    def _get_defaults(self, service_type, version):
        '''
        return the method/parameter set for the service and version
        keys: WMS-1.0.0
        '''
        key = service_type.upper() + '-' + version
        return self.defaults[key] if key in self.defaults else {}


class BaseOgcExtractor():

    _wxs_namespace_pattern = '{http://www.opengis.net/%(ns)s}'
    _service_patterns = {}
    _endpoint_patterns = {}

    def __init__(self, xml, version, service_type, prefix, namespaces):
        self.xml = xml
        self.service_type = service_type
        self.prefix = prefix
        self.namespaces = namespaces

        self.ns = self._wxs_namespace_pattern % {'ns': service_type.lower()}

        defaults = OgcDefaults(service_type, version)
        self.parameter_defaults = defaults.defaults

    def generate_metadata_xpaths(self):
        '''
        map the list or a singleton depending on the differences in the implementations
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
        strip out the namespace from a tag and just return the tag
        '''
        return string[string.index('}') + 1:]

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

    note: this does not appear to have the same issue with third-party
        method extensions
    '''
    _service_patterns = {
        "title": "/%(ns)s*/{http://www.opengis.net/ows}ServiceIdentification/{http://www.opengis.net/ows}Title",
        "name": "/%(ns)s*/{http://www.opengis.net/ows}ServiceIdentification/{http://www.opengis.net/ows}Name",
        "abstract": "/%(ns)s*/{http://www.opengis.net/ows}ServiceIdentification/{http://www.opengis.net/ows}Abstract",
        "tags": "/%(ns)s*/{http://www.opengis.net/ows}ServiceIdentification/{http://www.opengis.net/ows}KeywordList/{http://www.opengis.net/ows}Keyword",
        "contact": "/%(ns)s*/{http://www.opengis.net/ows}ServiceProvider/{http://www.opengis.net/ows}ProviderName"
    }
    _url_pattern = '/%(ns)s*/{http://www.opengis.net/ows}OperationsMetadata'+ \
        '/{http://www.opengis.net/ows}Operation[@name="%(method)s"]/{http://www.opengis.net/ows}DCP'+ \
        '/{http://www.opengis.net/ows}HTTP/{http://www.opengis.net/ows}%(type)s/@{http://www.w3.org/1999/xlink}href'

    def generate_method_xpaths(self):
        request_xpath = "/%(ns)s*/{http://www.opengis.net/ows}OperationsMetadata/{http://www.opengis.net/ows}Operation" % {
            "ns": self.ns
        }

        endpoint_xpaths = {}
        request_xpath = self._remap_namespaced_xpaths(request_xpath)

        url_xpath = "{http://www.opengis.net/ows}DCP/{http://www.opengis.net/ows}HTTP/{http://www.opengis.net/ows}*"
        url_xpath = self._remap_namespaced_xpaths(url_xpath)

        param_xpath = "{http://www.opengis.net/ows}Parameter"
        param_xpath = self._remap_namespaced_xpaths(param_xpath)

        requests = self.xml.xpath(request_xpath, namespaces=self.namespaces)
        for request in requests:
            method = request.attrib['name']

            print url_xpath

            urls = request.xpath(url_xpath, namespaces=self.namespaces)
            methods = []
            for url in urls:
                request_method = self._strip_namespaces(url.tag)

                url_xpath = self._url_pattern % {
                    'ns': self.ns,
                    'method': method,
                    'type': request_method
                }

                methods.append((request_method, url_xpath))

            # get the parameters
            method_params = self.parameter_defaults.get(method.upper(), '')
            assert method_params, 'Invalid method definition for Method %s' % method

            params = request.xpath(param_xpath, namespaces=self.namespaces)

            defs = [self._get_parameter(p, method_params) for p in params]

            endpoint_xpaths[method] = [
                {
                    'url': m[1],
                    'request_type': m[0],
                    'parameters': defs
                } for m in methods
            ]

        return endpoint_xpaths

    def _get_parameter(self, node, parameter_options):
        '''
        using some combination of default info (see OgcDefaults) and
        node information, return the json element for this parameter
        '''
        node_name = node.attrib.get('name', '')
        assert node_name, 'Invalid parameter node for ows:Parameter'

        # check for a one-to-one
        default = {node_name.upper(): parameter_options[node_name.upper()]} if node_name.upper() in parameter_options \
            else {k: v for k, v in parameter_options.iteritems() if (v['Remap']['remapped'] == node_name if 'Remap' in v else False)}

        if not default:
            # TODO: return something very basic but not a null dict
            # AND this will not be triggered
            return {}

        k, v = next(default.iteritems())
        return (k, v['Namespace'], v['Prefix'], '', (v['Format'] if 'Format' in v else ''))


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
            "/%(ns)s*/%(ns)sService/%(ns)sTitle",
            "/%(ns)s%(upper)s_Capabilities/%(ns)sService/%(ns)stitle"
        ],
        "name": [
            "/%(ns)s*/%(ns)sService/%(ns)sName",
            "/%(ns)s*/%(ns)sService/%(ns)sname"
        ],
        "abstract": [
            "/%(ns)s*/%(ns)sService/%(ns)sAbstract",
            "/%(ns)s*/%(ns)sService/%(ns)sdescription"
        ],
        "tags": [
            "/%(ns)s*/%(ns)sService/%(ns)sKeywordList/%(ns)sKeyword",
            "/%(ns)s*/%(ns)sService/%(ns)skeywords/%(ns)skeyword"
        ],
        "contact": [
            "/%(ns)s*/%(ns)sService/%(ns)sContactInformation/%(ns)sContactPersonPrimary",
            "/%(ns)s*/%(ns)sService/%(ns)sresponsibleParty/%(ns)sorganisationName"
        ]
    }

    _url_pattern = '/%(ns)s*' + \
        '/%(ns)sCapability/%(ns)sRequest' + \
        '/%(local_ns)s%(method)s/%(ns)sDCPType' + \
        '/%(ns)sHTTP/%(ns)s%(type)s'+ \
        '/%(ns)sOnlineResource/@{http://www.w3.org/1999/xlink}href'

    _format_pattern = '/%(ns)s*' + \
        '/%(ns)sCapability/%(ns)sRequest' + \
        '/%(local_ns)s%(method)s/%(ns)sFormat'

    def generate_method_xpaths(self):
        '''
        for any capablility/request, pull the dcptype & link
        note that we can have standard ogc methods and extended service support
            through other namespaces

        and we're parsing the metadata to figure out how we should parse the metadata
        '''
        request_xpaths = ["/%(ns)s*/%(ns)sCapability/%(ns)sRequest/%(ns)s*" % {
                "ns": self.ns
            },
            "/%(ns)s*/%(ns)sCapability/%(ns)sRequest/*[namespace-uri() != '%(ns_unbracketed)s']" % {
                "ns": self.ns,
                "ns_unbracketed": self.ns[1:-1]
            }
        ]

        request_pattern = "%(ns)sDCPType/%(ns)sHTTP/%(ns)s*" % {"ns": self.ns}
        request_pattern = self._remap_namespaced_xpaths(request_pattern)

        endpoint_xpaths = {}
        for request_xpath in request_xpaths:
            xpath = self._remap_namespaced_xpaths(request_xpath)

            requests = self.xml.xpath(xpath, namespaces=self.namespaces)

            for request in requests:
                method = self._strip_namespaces(request.tag)
                local_ns = request.tag[:request.tag.index('}') + 1]

                urls = request.xpath(request_pattern, namespaces=self.namespaces)
                methods = []
                for url in urls:
                    request_method = self._strip_namespaces(url.tag)

                    url_xpath = self._url_pattern % {"ns": self.ns, 
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
