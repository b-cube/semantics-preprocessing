import yaml
import re


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
                    return sums + self._evaluate(i, 0)

            if k == 'ands':
                # everything must be true
                sums += sum(v) == len(v)
            elif k == 'ors':
                # any one must be true
                sums += sum(v) > 0

        return sums

    def _identify_protocol(self):
        for protocol in self.protocols:
            protocol_filters = protocol['filters']

            # print protocol['name']

            for k, v in protocol_filters.iteritems():
                # print '\t', {k: self._filter(k, v, [])}
                is_match = self._evaluate({k: self._filter(k, v, [])}, 0)
                if is_match:
                    return protocol['name']

        return ''

    def _identify_service_of_protocol(self, protocol):
        protocol_data = next(p for p in self.protocols if p['name'] == protocol)
        if not protocol_data:
            return ''

        if 'services' not in protocol_data:
            return ''

        for service in protocol_data['services']:
            for k, v in service['filters'].iteritems():
                is_match = self._evaluate({k: self._filter(k, v, [])}, 0)
                if is_match:
                    return service['name']

        return ''

    def _identify_if_dataset_service(self, protocol):
        '''
        TODO: sort out if this needs to be a named
              response or just the boolean

        this will depend on the service type and version
        '''
        return False

    def _is_protocol_error(self, protocol):
        '''
        check to see if this is an error response for a protocol
        '''
        protocol_data = next(p for p in self.protocols if p['name'] == protocol)
        if not protocol_data:
            return False

        if 'errors' not in protocol_data:
            # we don't know how to determine error here
            return False

        filters = protocol_data['errors']['filters']
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
        protocol_data = next(p for p in self.protocols if p['name'] == protocol)
        if not protocol_data:
            return ''

        if 'versions' not in protocol_data:
            return ''

        versions = protocol_data['versions']

        # basic check for implied defaults
        if 'defaults' in versions:
            for k, v in versions['defaults'].iteritems():
                for f in v:
                    if f['type'] == 'simple':
                        filter_value = f['value']
                        filter_object = self.source_content if f['object'] == 'content' \
                            else self.source_url

                        if self.ignore_case:
                            filter_value = filter_value.upper()
                            filter_object = filter_object.upper()

                        if filter_value in filter_object:
                            return f['text']

        # run against any explicit version definition
        if 'checks' in versions:
            for k, v in versions['checks'].iteritems():
                # i am not dealing with recursive xpath checks tonight
                for f in v:
                    if f['type'] == 'xpath':
                        if not source_as_parser:
                            # TODO: log this
                            continue
                        value = source_as_parser.find(f['value'])
                        if value:
                            return value[0] if isinstance(value, list) else value

        return ''

    def generate_urn(self):
        pass

    def identify(self):
        '''
        execute all of the identification options
        '''
        self.protocols = self.yaml['protocols']

        # determine the protocol
        protocol = self._identify_protocol()

        if not protocol:
            return '', '', '', '', False

        # make sure it's not an error response
        is_error = self._is_protocol_error(protocol)
        if is_error:
            return protocol, '', '', '', is_error

        # and if it's a service description (and which)
        service = self._identify_service_of_protocol(protocol)
        if not service:
            return protocol, '', '', '', is_error

        # determine if it contains dataset-level info
        is_dataset = self._identify_if_dataset_service(protocol)

        # extract the version
        parser = self.options.get('parser', None)
        version = self._identify_version(protocol, parser)

        return protocol, service, is_dataset, version, False
