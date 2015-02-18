import logging
import yaml
import re

LOGGER = logging.getLogger(__name__)

# TODO: put together a configuration widget for
#       to map protocol to some search filters
#       and some service description filters,
#       and some dataset filters so that we can
#       have one thing to map the priority set
#       vs the IDENTIFY ALL THE THINGS! set. oh,
#       and wind up with reasonable line lengths
#       for beto. :) so basically elasticsearch all
#       the things.
#
# _ors: [content filters] + [url filters] (ANY match)
# _ands [content filter + url filter (or other combo)]
# where an _ands can be a filter in an _ors
#
# add the bit about is it valid xml?
# add the bit about version extraction?
# add the bit about it's valid xml but a error response


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
        self.yaml_file = yaml_file
        self.source_content = source_content
        self.source_url = source_url
        self.options = options
        self.yaml = self._parse_yaml()

    def _parse_yaml(self):
        with open(self.yaml_file, 'r') as f:
            text = f.read()
        return yaml.load(text)

    def _filter(self, operator, filters):
        clauses = []
        for f in filters:
            print 'filter', f
            filter_type = f['type']

            if filter_type == 'complex':
                filter_operator = f['operator']
                clauses.append(self._filter(filter_operator, f['filters']))
                # TODO: get this to return the recursed clause list correctly
                print 'nested', clauses
            elif filter_type == 'simple':
                filter_object = self.source_content if f['object'] == 'content' else self.source_url
                filter_value = f['value']
                clauses.append(filter_value in filter_object)
            elif filter_type == 'regex':
                filter_object = self.source_content if f['object'] == 'content' else self.source_url
                filter_value = f['value']
                clauses.append(len(re.findall(filter_value, filter_object)) > 0)

        print clauses
        return self._evaluate(operator, clauses)

    def _evaluate(self, operator, clauses):
        if operator == 'ands':
            # everything must be true
            return sum(clauses) == len(clauses)
        elif operator == 'ors':
            # any one must be true
            return sum(clauses) > 0

    def _identify_protocol(self):
        for protocol in self.protocols:
            protocol_filters = protocol['filters']

            for k, v in protocol_filters.iteritems():
                is_match = self._filter(k, v)
                if is_match:
                    return protocol['name']

        return ''

    def _identify_service_of_protocol(self, protocol):
        protocol_data = next(p for p in self.protocols if p['name'] == protocol)
        if not protocol_data:
            LOGGER.warn('failed to identify protocol %s' % protocol)
            return False

        for service in protocol_data['services']:
            for k, v in service['filters'].iteritems():
                print k, v
                is_match = self._filter(k, v)
                if is_match:
                    return service['name']

        return ''

    def _identify_if_dataset_service(self, protocol):
        '''
        TODO: sort out if this needs to be a named
              response or just the boolean
        '''
        return False

    def _is_protocol_error(self, protocol):
        '''
        TODO: get the xpath? or whatever for the
              protocol to determine if error
        '''
        return False

    def _identify_version(self, protocol):
        '''
        TODO: get the xpath? or whatever for the
              protocol to determine the version
              if that is possible at all
        '''
        return ''

    def identify(self):
        self.protocols = self.yaml['protocols']
