from owslib.wms import WebMapService
from owslib.wcs import WebCoverageService
from owslib.wfs import WebFeatureService
from owslib.csw import CatalogueServiceWeb
from lib.yaml_configs import import_yaml_configs


class OgcPreprocessor():
    '''
    base class to handle OWSLib responses

    support for: WMS 1.1.1
                 WFS 1.0.0
                 WFS 1.1.0
                 WCS 1.0.0
                 WCS 1.1.0
                 CSW 2.0.2
    '''
    def __init__(self, service, version, response_as_string):
        self.service = service
        self.version = version
        self.response = response_as_string

        # get the owslib object
        self.reader = self._get_reader()

    def _get_reader(self):
        if self.service == 'WMS' and self.version in ['1.1.1']:
            reader = WebMapService('', xml=self.response, version=self.version)
        elif self.service == 'WFS' and self.version in ['1.0.0', '1.1.0']:
            reader = WebFeatureService('', xml=self.response, version=self.version)
        elif self.service == 'WCS' and self.version in ['1.0.0', '1.1.0']:
            reader = WebCoverageService('', xml=self.response, version=self.version)
        elif self.service == 'CSW' and self.version in ['2.0.2']:
            reader = CatalogueServiceWeb('', xml=self.response, version=self.version)

        return reader

    def _get_config(self):
        data = import_yaml_configs(['lib/configs/ogc_parameters.yaml'])
        self.config = next(d for d in data if d['name'] == self.service.upper() +
                           self.version.replace('.', ''))

    def _get_operations(self):
        '''
        each operation can have more than one endpoint (get and post, ex)

        formatOptions = output format of the response method that can be some
                        controlled vocab value (XMLSCHEMA, etc)

                        this is incorrectly handled in wfs 1.1.0 (hardcoded value)

                        later versions can have an outputFormat parameter instead
                        BUT it comes down to whether that is a proper query parameter
                        or simply the delivered response (no choice in the spec)

        parameters = {name: {values: list}}
        '''
        _vocabs = {
            "XMLSCHEMA": "application/xml",
            "GML2": "text/xml; subtype=gml/2.1.2"
        }

        def _check_controlled_vocabs(term):
            if term in _vocabs:
                return _vocabs[term]
            return term

        def _replace_nones(to_check):
            return '' if to_check is None else to_check

        def _merge_params(op_name, found_params):
            '''
            for some parameter structure:
                {'resultType': {'values': ['results', 'hits']}}
            integrate into the config params with the common elements

            '''
            # TODO: how to handle aliases (if necessary)
            defaults = self.config.get('common', []) + next(iter([d for d in self.config['methods']
                                                                  if d['name'] == op_name.upper()])
                                                            ).get('params', [])

            if not found_params:
                return defaults

            for k, v in found_params.iteritems():
                found_param = next(d for d in defaults if d['name'] == k.lower())
                if not found_param:
                    continue

                found_index = defaults.index(found_param)
                found_param['values'] = v['values']
                defaults[found_index] = found_param

            return defaults

        operations = []
        for o in self.reader.operations:
            # TODO: handle the differing formatOptions

            # get the parameter values if supported by the service
            try:
                params = o.parameters
            except AttributeError:
                params = []

            # merge with defaults (where it can be add the whole element
            #   OR parts of the element)
            params = _merge_params(o.name, params)

            # get the formatOptions
            try:
                formats = [_check_controlled_vocabs(fo) for fo in o.formatOptions]
            except AttributeError:
                formats = []

            endpoint = [
                {
                    "name": o.name,
                    "type": m.get('type', ''),
                    "url": m.get('url', ''),
                    "constraints": m.get('constraints', []),
                    "formats": formats,
                    "parameters": [{
                        "name": p.get('name', ''),
                        "type": p.get('type', ''),
                        "format": p.get('format', ''),
                        "values": p.get('values', [])
                    } for p in params]
                } for m in o.methods
            ]

            operations += endpoint

        return operations

    def parse_service(self):
        '''
        this is a little unnecessary
        '''
        service = {
            "service": self.return_service_descriptors(),
            "remainder": []
        }
        return service

    def return_service_descriptors(self):
        try:
            rights = self.reader.identification.accessconstraints
        except AttributeError:
            rights = ''
        try:
            contact = self.reader.provider.contact.name
        except AttributeError:
            contact = ''

        return {
            "title": self.reader.identification.title,
            "abstract": self.reader.identification.abstract,
            "tags": self.reader.identification.keywords,
            "rights": rights,
            "contact": contact,
            "endpoints": self._get_operations()
        }
