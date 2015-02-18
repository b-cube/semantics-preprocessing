import unittest
from lib.identifier import Identify


class TestBasicIdentifiers(unittest.TestCase):
    # we are testing private methods because testing
    def setUp(self):
        yaml_file = 'tests/test_data/simple_identifier_test.yaml'

        content = '''<OpenSearch xmlns="http://a9.com/-/spec/opensearch/1.1/">
                        <element>OpenSearchDescription</element></OpenSearch>'''
        url = 'http://www.opensearch.com'

        self.identifier = Identify(yaml_file, content, url)
        self.identifier.identify()

    def test_load_yaml(self):
        self.assertTrue(self.identifier.yaml['protocols'][0]['name'] == 'OpenSearch')
        self.assertTrue(self.identifier.protocols)

        names = [p['name'] for p in self.identifier.protocols]
        self.assertTrue(len(names) == 1)

    def test_identify_protocol(self):
        expected_protocol = 'OpenSearch'
        returned_protocol = self.identifier._identify_protocol()
        self.assertTrue(expected_protocol == returned_protocol)

    def test_identify_service_from_protocol(self):
        expected_service = 'OpenSearchDescription'
        returned_service = self.identifier._identify_service_of_protocol('OpenSearch')

        self.assertTrue(returned_service)
        self.assertTrue(expected_service == returned_service)


class TestComplexIdentifiers(unittest.TestCase):
    def setUp(self):
        yaml_file = 'tests/test_data/complex_identifier_test.yaml'

        content = '''<OpenSearch xmlns="http://a9.com/-/spec/opensearch/1.1/">
                        <element>Nope</element></OpenSearch>'''
        url = 'http://www.opensearch.com'

        self.identifier = Identify(yaml_file, content, url)
        self.identifier.identify()

    def test_load_yaml(self):
        self.assertTrue(self.identifier.yaml['protocols'][0]['name'] == 'OGC')

        names = [p['name'] for p in self.identifier.protocols]
        self.assertTrue(len(names) == 2)

        ogc_protocol = self.identifier.yaml['protocols'][0]
        self.assertTrue('services' in ogc_protocol)
        self.assertTrue(len(ogc_protocol['services']) == 3)

    def test_identify_protocol(self):
        expected_protocol = 'OGC'
        returned_protocol = self.identifier._identify_protocol()
        self.assertTrue(expected_protocol == returned_protocol)

    def test_identify_service_from_protocol(self):
        expected_service = 'OpenSearchDescription'
        returned_service = self.identifier._identify_service_of_protocol('OpenSearch')

        self.assertTrue(returned_service)
        self.assertTrue(expected_service == returned_service)

