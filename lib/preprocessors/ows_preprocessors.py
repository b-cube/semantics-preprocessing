from owslib.wms import WebMapService
from owslib.wcs import WebCoverageService

'''
unmodified module supports:
    wms 1.1.1
    wfs 1.0.0, 1.1.0
    wcs 1.1.0

these do not inherit any of the BaseReader structures
but retain some of the method names for clarity
'''


class OwsWmsPreprocessor():
    '''
    getcapabilities parsing for 1.1.1

    TODO: handle multiple versions later
    TODO: check on how well owslib handles the third party
          namespaces (maybe it doesn't?)
    '''

    def __init__(self, xml_as_string, version):
        if version != '1.1.1':
            return

        self.version = version
        self.xml_as_string = xml_as_string

        self._get_reader()

    def _get_reader(self):
        self.reader = WebMapService('', xml=self.xml_as_string, version=self.version)

    def parse_reader(self):
        '''
        this is a little unnecessary
        '''
        service = {
            "service": self.return_service_descriptors(),
            "remainder": []
        }
        return service

    def return_service_descriptors(self):
        '''
        return the dict based on the wms object

        title
        abstract
        tags
        contact
        rights

        version
        language(?)

        endpoints
        '''
        services = {
            "title": self.reader.identification.title,
            "abstract": self.reader.identification.abstract,
            "tags": self.reader.identification.keywords,
            "rights": self.reader.identification.accessconstraints,
            "contact": self.reader.provider.contact.name,
            "version": self.version
        }

        # generate the endpoint info from what's listed and
        # the config for this service + version
        endpoints = {}
        for op in self.reader.operations:
            endpoints[op.name] = self._generate_endpoint(op.name)

        services['endpoints'] = endpoints

        return services

    def return_everything_else(self):
        '''
        i expect this to not be used in these parsers
        '''
        pass

    def _generate_endpoint(self, method):
        '''
        still a tuple:
            type
            url
            parameters as list of tuples
                tuple: (parameter name, namespace(s), param
                        namespace prefix, param type, format, enumerations)
        '''
        operation = self.reader.getOperationByName(method)

        links = operation.methods
        formats = operation.formatOptions

        endpoints = [
            (
                link['type'],
                link['url'],
                self._get_parameters(method.lower(), formats)
            )
            for link in links
        ]

        return endpoints

    def _get_parameters(self, method, formats):
        _vocabs = {
            "XMLSCHEMA": "application/xml"
        }

        def _check_controlled_vocabs(term):
            if term in _vocabs:
                return _vocabs[term]
            return term

        # TODO: add required!
        # TODO: revise for actually being 1.1.1 (based on 1.3.0)
        if method == 'getcapabilities':
            return [
                (
                    "Version",
                    "http://www.opengis.net/wms",
                    "wms",
                    "string",
                    "",
                    []
                ),
                (
                    "Request",
                    "http://www.opengis.net/wms",
                    "wms",
                    "string",
                    "",
                    []
                ),
                (
                    "Service",
                    "http://www.opengis.net/wms",
                    "wms",
                    "string",
                    "",
                    []
                ),
                (
                    "Format",
                    "http://www.opengis.net/wms",
                    "wms",
                    "string",
                    "",
                    [_check_controlled_vocabs(f) for f in formats]
                )
            ]
        elif method == 'getmap':
            return [
                (
                    "Version",
                    "http://www.opengis.net/wms",
                    "wms",
                    "string",
                    "",
                    []
                ),
                (
                    "Request",
                    "http://www.opengis.net/wms",
                    "wms",
                    "string",
                    "",
                    []
                ),
                (
                    "Service",
                    "http://www.opengis.net/wms",
                    "wms",
                    "string",
                    "",
                    []
                ),
                (
                    "Format",
                    "http://www.opengis.net/wms",
                    "wms",
                    "string",
                    "",
                    [_check_controlled_vocabs(f) for f in formats]
                ),
                (
                    "Layers",
                    "http://www.opengis.net/wms",
                    "wms",
                    "string",
                    "",
                    []
                ),
                (
                    "BBOX",
                    "http://www.opengis.net/wms",
                    "wms",
                    "string",
                    "minx,miny,maxx,maxy",
                    []
                ),
                (
                    "Height",
                    "http://www.opengis.net/wms",
                    "wms",
                    "integer",
                    "",
                    []
                ),
                (
                    "Width",
                    "http://www.opengis.net/wms",
                    "wms",
                    "integer",
                    "",
                    []
                ),
                (
                    "Styles",
                    "http://www.opengis.net/wms",
                    "wms",
                    "string",
                    "",
                    []
                ),
                (
                    "CRS",
                    "http://www.opengis.net/wms",
                    "wms",
                    "string",
                    "",
                    []
                ),
                (
                    "Transparent",
                    "http://www.opengis.net/wms",
                    "wms",
                    "boolean",
                    "",
                    []
                ),
                (
                    "BgColor",
                    "http://www.opengis.net/wms",
                    "wms",
                    "hexadecimal",
                    "",
                    []
                ),
                (
                    "Elevation",
                    "http://www.opengis.net/wms",
                    "wms",
                    "string",
                    "",
                    []
                ),
                (
                    "Time",
                    "http://www.opengis.net/wms",
                    "wms",
                    "string",
                    "",
                    []
                )
            ]
        elif method == 'getlegendgraphic':
            return ()
        elif method == 'getfeatureinfo':
            return [
                (
                    "Version",
                    "http://www.opengis.net/wms",
                    "wms",
                    "string",
                    "",
                    []
                ),
                (
                    "Request",
                    "http://www.opengis.net/wms",
                    "wms",
                    "string",
                    "",
                    []
                ),
                (
                    "Service",
                    "http://www.opengis.net/wms",
                    "wms",
                    "string",
                    "",
                    []
                ),
                (
                    "Info_Format",
                    "http://www.opengis.net/wms",
                    "wms",
                    "string",
                    "",
                    [_check_controlled_vocabs(f) for f in formats]
                ),
                (
                    "Feature_Count",
                    "http://www.opengis.net/wms",
                    "wms",
                    "integer",
                    "",
                    []
                )
            ]
        return []


class OwsWcsPreprocessor():
    def __init__(self, xml_as_string, version):
        if version != '1.0.0':
            return

        self.version = version
        self.xml_as_string = xml_as_string

        self._get_reader()

    def _get_reader(self):
        self.reader = WebCoverageService('', xml=self.xml_as_string, version=self.version)

    def parse_reader(self):
        '''
        this is a little unnecessary
        '''
        service = {
            "service": self.return_service_descriptors(),
            "remainder": []
        }
        return service

    def return_service_descriptors(self):
        '''
        return the dict based on the wms object

        title
        abstract
        tags
        contact
        rights

        version
        language(?)

        endpoints
        '''
        services = {
            "title": self.reader.identification.title,
            "abstract": self.reader.identification.abstract,
            "tags": self.reader.identification.keywords,
            "rights": self.reader.identification.accessConstraints,
            "contact": self.reader.provider.contact.name,
            "version": self.version
        }

        # generate the endpoint info from what's listed and
        # the config for this service + version
        endpoints = {}
        for op in self.reader.operations:
            endpoints[op.name] = self._generate_endpoint(op.name)

        services['endpoints'] = endpoints

        return services

    def _generate_endpoint(self, method):
        '''
        still a tuple:
            type
            url
            parameters as list of tuples
                tuple: (parameter name, namespace(s), param
                        namespace prefix, param type, format, enumerations)

        wcs 1.0.0 does not support formats? in the method identification
        '''
        operation = self.reader.getOperationByName(method)

        links = operation.methods

        endpoints = [
            (
                link['type'],
                link['url'],
                self._get_parameters(method.lower(), [])
            )
            for link in links
        ]

        return endpoints

    def _get_parameters(self, method, formats):
        _vocabs = {}

        def _check_controlled_vocabs(term):
            if term in _vocabs:
                return _vocabs[term]
            return term

        # TODO: add required!
        if method == 'getcapabilities':
            return [
                (
                    "Version",
                    "http://www.opengis.net/wcs",
                    "wcs",
                    "string",
                    "",
                    []
                ),
                (
                    "Request",
                    "http://www.opengis.net/wcs",
                    "wcs",
                    "string",
                    "",
                    []
                ),
                (
                    "Service",
                    "http://www.opengis.net/wcs",
                    "wcs",
                    "string",
                    "",
                    []
                )
            ]
        elif method == 'describecoverage':
            return [
                (
                    "Version",
                    "http://www.opengis.net/wcs",
                    "wcs",
                    "string",
                    "",
                    []
                ),
                (
                    "Request",
                    "http://www.opengis.net/wcs",
                    "wcs",
                    "string",
                    "",
                    []
                ),
                (
                    "Service",
                    "http://www.opengis.net/wcs",
                    "wcs",
                    "string",
                    "",
                    []
                ),
                (
                    "Coverage",
                    "http://www.opengis.net/wcs",
                    "wcs",
                    "string",
                    "",
                    []
                )
            ]
        elif method == 'getcoverage':
            return [
                (
                    "Version",
                    "http://www.opengis.net/wcs",
                    "wcs",
                    "string",
                    "",
                    []
                ),
                (
                    "Request",
                    "http://www.opengis.net/wcs",
                    "wcs",
                    "string",
                    "",
                    []
                ),
                (
                    "Service",
                    "http://www.opengis.net/wcs",
                    "wcs",
                    "string",
                    "",
                    []
                ),
                (
                    "Coverage",
                    "http://www.opengis.net/wcs",
                    "wcs",
                    "string",
                    "",
                    []
                ),
                (
                    "Format",
                    "http://www.opengis.net/wcs",
                    "wcs",
                    "string",
                    "",
                    [_check_controlled_vocabs(f) for f in formats]
                ),
                (
                    "BBOX",
                    "http://www.opengis.net/wcs",
                    "wcs",
                    "string",
                    "minx,miny,maxx,maxy",
                    []
                ),
                (
                    "Height",
                    "http://www.opengis.net/wcs",
                    "wcs",
                    "integer",
                    "",
                    []
                ),
                (
                    "Width",
                    "http://www.opengis.net/wcs",
                    "wcs",
                    "integer",
                    "",
                    []
                ),
                (
                    "CRS",
                    "http://www.opengis.net/wcs",
                    "wcs",
                    "string",
                    "",
                    []
                ),
                (
                    "Response_CRS",
                    "http://www.opengis.net/wcs",
                    "wcs",
                    "string",
                    "",
                    []
                ),
                (
                    "Time",
                    "http://www.opengis.net/wcs",
                    "wcs",
                    "string",
                    "",
                    []
                ),
                (
                    "Parameter",
                    "http://www.opengis.net/wcs",
                    "wcs",
                    "string",
                    "",
                    []
                ),
                (
                    "ResX",
                    "http://www.opengis.net/wcs",
                    "wcs",
                    "double",
                    "",
                    []
                ),
                (
                    "ResY",
                    "http://www.opengis.net/wcs",
                    "wcs",
                    "double",
                    "",
                    []
                ),
                (
                    "Interpolation",
                    "http://www.opengis.net/wcs",
                    "wcs",
                    "string",
                    "",
                    []
                ),
            ]


class OwsWFsPreprocessor():
    '''
    getcapabilities parsing for 1.1.0/1.0.0

    TODO: check on how well owslib handles the third party
          namespaces (maybe it doesn't?)
    TODO: I really truly profoundly hope that the parameter
          names are handled consistently across the versioned
          classes in owslib.
    '''

    def __init__(self, xml_as_string, version):
        if version not in ['1.1.0', '1.0.0']:
            return

        self.version = version
        self.xml_as_string = xml_as_string

        self._get_reader()

    def _get_reader(self):
        self.reader = WebMapService('', xml=self.xml_as_string, version=self.version)

    def parse_reader(self):
        '''
        this is a little unnecessary
        '''
        service = {
            "service": self.return_service_descriptors(),
            "remainder": []
        }
        return service

    def return_service_descriptors(self):
        '''
        return the dict based on the wms object

        title
        abstract
        tags
        contact
        rights

        version
        language(?)

        endpoints
        '''
        services = {
            "title": self.reader.identification.title,
            "abstract": self.reader.identification.abstract,
            "tags": self.reader.identification.keywords,
            "rights": self.reader.identification.accessconstraints,
            "contact": self.reader.provider.contact.name,
            "version": self.version
        }

        # generate the endpoint info from what's listed and
        # the config for this service + version
        endpoints = {}
        for op in self.reader.operations:
            endpoints[op.name] = self._generate_endpoint(op.name)

        services['endpoints'] = endpoints

        return services

    def return_everything_else(self):
        '''
        i expect this to not be used in these parsers
        '''
        pass

    def _generate_endpoint(self, method):
        '''
        still a tuple:
            type
            url
            parameters as list of tuples
                tuple: (parameter name, namespace(s), param
                        namespace prefix, param type, format, enumerations)
        '''
        operation = self.reader.getOperationByName(method)

        links = operation.methods
        # TODO: deal with the OWS parameter:value
        formats = operation.formatOptions

        endpoints = [
            (
                link['type'],
                link['url'],
                self._get_parameters(method.lower(), formats)
            )
            for link in links
        ]

        return endpoints
