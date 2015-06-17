from bcube_owslib.wms import WebMapService
from bcube_owslib.wcs import WebCoverageService
from bcube_owslib.wfs import WebFeatureService
from bcube_owslib.csw import CatalogueServiceWeb
from bcube_owslib.sos import SensorObservationService
from lib.preprocessors import Processor
from lib.preprocessors.csw_preprocessors import CswReader
from lib.yaml_configs import import_yaml_configs
from lib.geo_utils import bbox_to_geom, reproject, to_wkt
from lib.utils import tidy_dict, remap_http_method
import dateutil.parser as dateparser


class OgcReader(Processor):
    '''
    base class to handle OWSLib responses

    support for: WMS 1.1.1
                 WMS 1.3.0
                 WFS 1.0.0
                 WFS 1.1.0
                 WCS 1.0.0
                 WCS 1.1.0
                 WCS 1.1.1
                 WCS 1.1.2
                 CSW 2.0.2
                 SOS 1.0.0
    '''
    def _get_service_reader(self):
        if self.service == 'WMS' and self.version in ['1.1.1', '1.3.0']:
            reader = WebMapService('', xml=self.response, version=self.version)
        elif self.service == 'WFS' and self.version in ['1.0.0', '1.1.0']:
            reader = WebFeatureService('', xml=self.response, version=self.version)
        elif self.service == 'WCS' and self.version in ['1.0.0', '1.1.0', '1.1.1', '1.1.2']:
            reader = WebCoverageService('', xml=self.response, version=self.version)
        elif self.service == 'CSW' and self.version in ['2.0.2']:
            reader = CatalogueServiceWeb('', xml=self.response, version=self.version)
        elif self.service == 'SOS' and self.version in ['1.0.0']:
            reader = SensorObservationService('', xml=self.response, version=self.version)
        else:
            return None
        return reader

    def _get_service_config(self):
        # get the config file
        data = import_yaml_configs(['lib/configs/ogc_parameters.yaml'])
        self.config = next(d for d in data if d['name'] == self.service.upper() +
                           self.version.replace('.', ''))

    def _get_operations(self, reader):
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

        def _append_params(base_url, operation):
            if not base_url[-1] == '?':
                base_url += '?'
            return base_url + 'SERVICE=%s&VERSION=%s&REQUEST=%s' % (self.service,
                                                                    self.version,
                                                                    operation)

        def _merge_params(op_name, found_params):
            '''
            for some parameter structure:
                {'resultType': {'values': ['results', 'hits']}}
            integrate into the config params with the common elements

            '''
            # TODO: how to handle aliases (if necessary)
            req_methods = self.config.get('methods', [])
            req_params = next(
                iter(
                    [d for d in req_methods if d['name'] == op_name.upper()]
                ), {}
            ).get('params', [])
            req_params = [] if not req_params else req_params
            defaults = self.config.get('common', []) + req_params

            if not found_params:
                return defaults

            for k, v in found_params.iteritems():
                param = next(iter(d for d in defaults if d['name'] == k.lower()), [])
                if not param:
                    continue

                found_index = defaults.index(param)
                param['values'] = [_check_controlled_vocabs(a) for a in v['values']]
                defaults[found_index] = param

            return defaults

        def _return_parameter(param):
            # return a parameter dict without empty values
            parameter = {}
            for key in ['name', 'type', 'format', 'values']:
                if key in param and param[key]:
                    parameter[key] = param[key]
            return parameter

        operations = []
        for o in reader.operations:
            # TODO: handle the differing formatOptions

            # get the parameter values if supported by the service
            try:
                params = o.parameters
            except AttributeError:
                params = {}

            # merge with defaults (where it can be add the whole element
            #   OR parts of the element)
            params = _merge_params(o.name, params)

            # get the formatOptions
            try:
                formats = [_check_controlled_vocabs(fo) for fo in o.formatOptions]
            except AttributeError:
                formats = []

            endpoints = [
                tidy_dict({
                    "name": o.name,
                    "protocol": remap_http_method(m.get('type', '')),
                    "url": _append_params(m.get('url', ''), o.name),
                    "constraints": m.get('constraints', []),
                    "mimeType": formats,
                    "actionable": 1 if o.name == 'GetCapabilities' else 2,
                    "parameters": [_return_parameter(p) for p in params]
                }) for m in o.methods
            ]

            operations += endpoints

        return operations

    def _return_timerange(self, timepositions):
        '''
        from a set of timeposition or dimension/extent=temporal elements,
        try to parse the dates (iso 8601) from each element and return
        the min/max of the set

        structures:
            - an iso 8601 timestamp
            - a comma-delimited list of timestamps
            - a forward-slash delimited list of timestamps where the last
              item is the period (not a timestamp)
        '''
        timestamps = []
        for default_time, timeposition in timepositions:
            if ',' in timeposition:
                parts = timeposition.split(',')
            elif '/' in timeposition:
                parts = timeposition.split('/')[:-1]
            else:
                parts = [timeposition]

            for part in parts:
                try:
                    d = dateparser.parse(part)
                    timestamps.append(d)
                except:
                    continue

        return min(timestamps), max(timestamps)

    def parse(self):
        self.description = {}

        if 'service' in self.identity:
            # run the owslib getcapabilities parsers
            reader = self._get_reader()
            if not reader:
                return {}
            self._get_config()
            self.description['service'] = self._parse_service(reader)

        if 'dataset' in self.identity:
            # run the owslib wcs/wfs describe* parsers
            request = self.identity['dataset'].get('request', '')
            service = self.identity['dataset'].get('name', '')
            if not request or not service:
                return {}

            if service == 'WMS' and request == 'GetCapabilities':
                # this is a rehash of the getcap parsing
                # but *only* returning the layers set
                reader = WebMapService('', xml=self.response, version=self.version)
                self.description['datasets'] = self._parse_getcap_datasets(reader)
            if service == 'WCS' and request == 'DescribeCoverage':
                reader = None
            elif service == 'SOS' and request == 'DescribeObservation':
                reader = None
            elif service == 'WFS' and request == 'DescribeFeatureType':
                reader = None

        if 'resultset' in self.identity:
            # assuming csw, run the local csw reader
            reader = CswReader(self.identity, self.response, self.url)

        self.description = tidy_dict(self.description)

    def _parse_service(self, reader):
        rights = [reader.identification.accessconstraints]
        try:
            contact = [reader.provider.contact.name]
        except AttributeError:
            contact = []

        abstract = [reader.identification.abstract]
        keywords = reader.identification.keywords
        endpoints = self._get_operations(reader)

        service = {
            "title": [reader.identification.title]
        }

        if rights:
            service['rights'] = rights

        if contact:
            service['contact'] = contact

        if abstract:
            service['abstract'] = abstract

        if keywords:
            service['subject'] = keywords

        if endpoints:
            service['endpoints'] = endpoints

        return service

    def _parse_getcap_datasets(self, reader):
        '''
        from some content metadata object, get all of the
        layers/features/coverages

        output:
            name
            title
            srs
            bounding boxes
            wgs84 bbox

            style

            metadataurl (should be a relate)

            elevation
            time

        note: the values are lists to handle other service responses
              that may have multiple values for that element.
        '''
        datasets = []

        if reader.contents is None:
            return []

        for name, dataset in reader.contents.iteritems():
            d = {}

            d['name'] = name
            if dataset.title:
                d['title'] = [dataset.title]

            if dataset.abstract:
                d['abstract'] = [dataset.abstract]

            if dataset.boundingBoxes:
                d['bboxes'] = dataset.boundingBoxes

            # if dataset.boundingBoxWGS84:
            #     d['bbox'] = [dataset.boundingBoxWGS84]

            try:
                # fconvert to wkt (and there's something about sos - maybe not harmonized)
                if dataset.boundingBoxWGS84:
                    bbox = bbox_to_geom(dataset.boundingBoxWGS84)
                    d['bbox'] = [to_wkt(bbox)]
            except AttributeError:
                pass

            if dataset.crsOptions:
                d['spatial_refs'] = dataset.crsOptions

            if dataset.attribution:
                d['rights'] = [dataset.attribution]

            if dataset.timepositions:
                d['temporal'] = dataset.timepositions

                begin_time, end_time = self._return_timerange(dataset.timepositions)
                d['temporal_extent'] = {"begin": begin_time.isoformat(),
                                        "end": end_time.isoformat()}

            datasets.append(d)

        return datasets

    def return_metadata_descriptors(self):
        '''
        children of the content widget
        '''
        if self.reader.contents is None:
            return []

        metadatas = []
        for name, dataset in self.reader.contents.iteritems():
            d = {}

            if dataset.metadataUrls:
                d['name'] = name
                d['metadata_urls'] = dataset.metadataUrls
                metadatas.append(d)

        return metadatas
