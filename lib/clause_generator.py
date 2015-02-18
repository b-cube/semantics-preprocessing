import yaml
import re


def build_clauses(yaml_file):
    with open(yaml_file, 'r') as f:
        text = f.read()
    data = yaml.load(text)

    for protocol in data['protocols']:
        print protocol['name']

    return data


def build_service_clauses(protocol, yaml_file, source_content, source_url):
    def is_service(filters):
        clauses = []
        for f in filters:
            filter_object = source_content if f['object'] == 'content' else source_url
            filter_value = f['value']
            filter_type = f['type']

            if filter_type == 'simple':
                clauses.append(filter_value in filter_object)
            elif filter_type == 'regex':
                clauses.append(len(re.findall(filter_value, filter_object)) > 0)

        return sum(clauses) == len(clauses)

    with open(yaml_file, 'r') as f:
        text = f.read()
    data = yaml.load(text)['protocols']

    protocol_data = next(p for p in data if p['name'] == protocol)

    assert protocol_data, 'Could not locate protocol'

    print protocol_data

    services = protocol_data['services']

    assert services, 'No services!'

    for service in services:
        filter_definitions = service['filters']
        print filter_definitions

        for operator, filter_defs in filter_definitions.iteritems():
            print operator, filter_defs
            if operator == 'ands':
                continue

            found = is_service(filter_defs)
            if found:
                return service['name']
    return ''
