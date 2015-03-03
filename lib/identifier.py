import yaml
import re
from itertools import chain


class Identify():
    '''
    parameters:
        yaml_file: path to the yaml definition yaml
        source_content: the content string for comparisons
        source_url: the url string for comparisons
        options: dict containing the filtering options, ie
                 identify which protocol, identify which service
                 of a protocol, identify if it's a dataset service
                 for a protocol
    '''
    def __init__(self, yaml_file, source_content, source_url, **options):
        '''
        **options:
            parser: Parser from source_content
            ignore_case: bool
        '''
        self.yaml_file = yaml_file
        self.source_content = source_content
        self.source_url = source_url
        self.options = options
        self.yaml = self._parse_yaml()

        self.ignore_case = options['ignore_case'] if 'ignore_case' in options else False

    def _parse_yaml(self):
        with open(self.yaml_file, 'r') as f:
            text = f.read()
        return yaml.load(text)

    def _filter(self, operator, filters, clauses):
        '''
        generate a list of dicts for operator and booleans
        that can be rolled up into some bool for a match
        '''
        for f in filters:
            filter_type = f['type']

            if filter_type == 'complex':
                filter_operator = f['operator']
                clauses.append(self._filter(filter_operator, f['filters'], []))
            elif filter_type == 'simple':
                filter_object = self.source_content if f['object'] == 'content' else self.source_url
                filter_value = f['value']

                if self.ignore_case:
                    # TODO: a better solution than this
                    filter_value = filter_value.upper()
                    filter_object = filter_object.upper()
                clauses.append(filter_value in filter_object)
            elif filter_type == 'regex':
                filter_object = self.source_content if f['object'] == 'content' else self.source_url
                filter_value = f['value']
                clauses.append(len(re.findall(filter_value, filter_object)) > 0)
            elif filter_type == 'xpath':
                # if the filter is xpath, we can only run against
                # the provided xml (parser) and ONLY evaluate for existence
                # ie the xpath returned some element, list, text value
                # but we don't care what it returned
                parser = self.options.get('parser', None)
                xpath = f['value']
                if not parser:
                    # nothing to find, this is an incorrect filter
                    clauses.append(False)

                clauses.append(parser.find(xpath) is not None)

        return {operator: clauses}

    def _evaluate(self, clauses, sums):
        '''
        evaluate a list a dicts where the key is
        the operator and the value is a list of
        booleans
        '''
        if isinstance(clauses, bool):
            # so this should be the rolled up value
            return clauses

        for k, v in clauses.iteritems():
            if isinstance(v, dict):
                return sums + self._evaluate(v, 0)
            elif isinstance(v, list) and not all(isinstance(i, bool) for i in v):
                # TODO: this is not a good assumption
                for i in v:
                    sums += self._evaluate(i, 0)
                return sums
            if k == 'ands':
                # everything must be true
                sums += sum(v) == len(v)
                print k, v, sums
            elif k == 'ors':
                # any one must be true
                sums += sum(v) > 0

        return sums

    def _identify_protocol(self):
        for protocol in self.yaml:
            protocol_filters = protocol['filters']

            for k, v in protocol_filters.iteritems():
                is_match = self._evaluate({k: self._filter(k, v, [])}, 0)
                if is_match:
                    return protocol['name'], protocol['subtype']

        return '', ''

    def _identify_service_of_protocol(self, protocol):
        if 'service_description' not in protocol:
            return ''

        for service in protocol['service_description']:
            for k, v in service['filters'].iteritems():
                is_match = self._evaluate({k: self._filter(k, v, [])}, 0)
                if is_match:
                    return service['name']

        return ''

    def _identify_within(self, protocol, subtype='dataset'):
        '''
        for a service, identify if the response contains
        a subtype (dataset, metadata, viz) structure

        ex: ogc:wfs contains dataset information at the feature
            level
        ex: oai-pmh contains metadata information as dc.

        return identifier for subtype if found
        '''
        pass

    def _identify_dataset_service(self, protocol):
        '''
        TODO: sort out if this needs to be a named
              response or just the boolean

        this will depend on the service type and version
        '''
        if 'datasets' not in protocol:
            return False
        if not protocol['datasets']:
            return False

        for option in protocol['datasets']:
            for k, v in option['filters'].iteritems():
                print 'dataset', k, v
                is_match = self._evaluate({k: self._filter(k, v, [])}, 0)
                if is_match:
                    return True

        return False

    def _identify_metadata_service(self, protocol):
        '''
        TODO: sort out if this needs to be a named
              response or just the boolean (prob a named
              response to handle oai-pmh:dc situations)
        '''
        if 'metadatas' not in protocol:
            return False
        if not protocol['metadatas']:
            return False

        for k, v in protocol['metadatas']['filters'].iteritems():
            is_match = self._evaluate({k: self._filter(k, v, [])}, 0)
            if is_match:
                return True

        return False

    def _is_protocol_error(self, protocol):
        '''
        check to see if this is an error response for a protocol
        '''
        if 'errors' not in protocol:
            # we don't know how to determine error here
            return False
        if not protocol['errors']:
            return False

        filters = protocol['errors']['filters']
        for k, v in filters.iteritems():
            is_match = self._evaluate({k: self._filter(k, v, [])}, 0)
            if is_match:
                return True

        return False

    def _identify_version(self, protocol, source_as_parser):
        '''
        this is likely to be some xml action, so xpaths and
        the parsed xml (as a Parser obj)

        and not using the _filter method - we need to return
        the value from the source, not just an existence flag
        '''
        if 'versions' not in protocol:
            return ''

        versions = protocol['versions']

        def _process_type(f):
            if f['type'] == 'simple':
                filter_value = f['value']
                filter_object = self.source_content if f['object'] == 'content' \
                    else self.source_url

                if self.ignore_case:
                    filter_value = filter_value.upper()
                    filter_object = filter_object.upper()

                if filter_value in filter_object:
                    return f['text']

            elif f['type'] == 'xpath':
                if not source_as_parser:
                    # TODO: log this
                    return ''
                value = source_as_parser.find(f['value'])
                if value:
                    return value[0] if isinstance(value, list) else value

            return ''

        # check against either set of things (default vs check)
        to_check = dict(chain(versions.get('defaults', {}).items(),
                        versions.get('checks', {}).items()))

        for k, v in to_check.iteritems():
            for f in v:
                version = _process_type(f)
                if version:
                    return version

        return ''

    def to_json(self):
        return {
            "protocol": self.protocol,
            "service": self.service,
            "version": self.version,
            "is_dataset": self.is_dataset,
            "is_error": self.is_error
        }

    def generate_urn(self):
        '''
        this assumes that it is a good identification

        urn:{type}:{protocol}:{service}:{version}

        any unknown is represented as UNK (that is terrible)
        '''
        if not self.protocol:
            return ''

        return ':'.join([
            'urn',
            self.protocol,
            self.service if self.service else 'UNK',
            self.version if self.service else 'UNK'
        ])

    def identify(self):
        '''
        execute all of the identification options
        '''
        # determine the protocol
        protocol, subtype = self._identify_protocol()

        self.protocol = protocol
        self.service = ''
        self.version = ''
        self.is_dataset = False
        self.is_error = False
        self.subtype = subtype

        if not protocol:
            return

        protocol_data = next(p for p in self.yaml if p['name'] == protocol)
        if not protocol_data:
            return

        # and if it's a service description (and which)
        self.service = self._identify_service_of_protocol(protocol_data)
        if not self.service:
            return

        # make sure it's not an error response (we still
        #    like knowing which service)
        self.is_error = self._is_protocol_error(protocol_data)
        if self.is_error:
            return

        # determine if it contains dataset-level info
        self.is_dataset = self._identify_dataset_service(protocol_data)

        # extract the version
        parser = self.options.get('parser', None)
        self.version = self._identify_version(protocol_data, parser)
