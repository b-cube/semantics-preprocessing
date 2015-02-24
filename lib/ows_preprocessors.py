from owslib import WebMapService
# from owslib import WebCoverageService

'''
unmodified module supports:
    wms 1.1.1
    wfs 1.0.0, 1.1.0
    wcs 1.1.0

these do not inherit any of the BaseReader structures
'''


class OwsWmsPreprocessor():
    '''
    getcapabiltiies parsing for 1.1.1

    TODO: handle multiple versions later
    TODO: check on how well owslib handles the third party
          namespaces (maybe it doesn't?)
    '''

    def __init__(self, xml_as_string, version):
        if version != '1.1.1':
            return

        self.version = version
        self.xml_as_string = xml_as_string

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
                        namespace prefix, param type, format)
        '''
        operation = self.reader.getOperationByName(method)

        links = operation.methods
        formats = operation.formatOptions

        endpoints = [
            (
                link['type'],
                link['url'],

            )
            for link in links
        ]

        return endpoints

    def _get_parameters(self, method, formats):
        if method.lower() == 'getcapabiltiies':
            return [
                (
                    "Version",
                    "http://www.opengis.net/wms",
                    "wms",
                    "string",
                    ""
                )
            ]
        elif method.lower() == 'getmap':
            return ()
        elif method.lower() == 'getlegendgraphic':
            return ()
        return ()
