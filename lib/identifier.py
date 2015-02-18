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


def identify(yaml_file, source_content, source_url):
    def _parse_yaml(self):
        with open(yaml_file, 'r') as f:
            text = f.read()
        return yaml.load(text)

    def _filter(operator, filters):
        clauses = []
        for f in filters:
            filter_object = source_content if f['object'] == 'content' else source_url
            filter_value = f['value']
            filter_type = f['type']

            if filter_type == 'simple':
                clauses.append(filter_value in filter_object)
            elif filter_type == 'regex':
                clauses.append(len(re.findall(filter_value, filter_object)) > 0)
            elif filter_type == 'complex':
                filter_operator = f['operator']
                clauses.append(_filter(filter_operator, f['filters']))

        if operator == 'ands':
            # everything must be true
            return sum(clauses) == len(clauses)
        elif operator == 'ors':
            # any one must be true
            return sum(clauses) > 0

    def _identify_protocol():
        for protocol in protocols:
            protocol_filters = protocol['filters']

            for k, v in protocol_filters.iteritems():
                is_match = _filter(k, v)
                if is_match:
                    return protocol['name']

        return ''

    def _identify_service_of_protocol(protocol):
        protocol_data = next(p for p in protocols if p['name'] == protocol)
        if not protocol_data:
            LOGGER.warn('failed to identify protocol %s' % protocol)
            return False

        for service in protocol_data['services']:
            for k, v in service['filters'].iteritems():
                is_match = _filter(k, v)
                if is_match:
                    return service['name']

        return ''

    config_data = _parse_yaml()
    protocols = config_data['protocols']
