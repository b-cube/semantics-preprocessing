import unittest
from lib.identifier import Identify
from lib.parser import Parser


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

        with open('tests/test_data/esri_wms_35bd4e2ce8cd13e8697b03976ffe1ee6.txt', 'r') as f:
            content = f.read()
        url = 'http://www.mapserver.com/cgi?SERVICE=WMS&VERSION=1.3.0&REQUEST=GETCAPABILITIES'

        parser_content = content.replace('\\n', '')
        parser = Parser(parser_content)
        options = {'parser': parser}

        self.identifier = Identify(yaml_file, content, url, **options)
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
        expected_service = 'WMS'
        returned_service = self.identifier._identify_service_of_protocol('OGC')

        self.assertTrue(returned_service)
        self.assertTrue(expected_service == returned_service)

    def test_is_error(self):
        returned_error = self.identifier._is_protocol_error('OGC')
        self.assertFalse(returned_error)

    def test_identify(self):
        # just run it again?

        self.identifier.identify()

        self.assertFalse(self.identifier.is_error)
        self.assertTrue(self.identifier.protocol == 'OGC')
        self.assertTrue(self.identifier.service == 'WMS')
        self.assertTrue(self.identifier.version)
        self.assertTrue(self.identifier.version == '1.3.0')

    def test_generate_urn(self):
        expected_urn = 'urn:OGC:WMS:1.3.0'
        self.identifier.identify()

        urn = self.identifier.generate_urn()

        self.assertTrue(urn == expected_urn)


class TestExceptionIdentification(unittest.TestCase):
    def setUp(self):
        yaml_file = 'tests/test_data/complex_identifier_test.yaml'

        with open('tests/test_data/wms_exception.xml', 'r') as f:
            content = f.read()
        url = 'http://www.mapserver.com/cgi?SERVICE=WMS&VERSION=1.3.0&REQUEST=GETCAPABILITIES'

        self.identifier = Identify(yaml_file, content, url)
        self.identifier.identify()

    def test_is_error(self):
        returned_error = self.identifier._is_protocol_error('OGC')
        self.assertTrue(returned_error)


class TestVersionExtraction(unittest.TestCase):
    def setUp(self):
        yaml_file = 'tests/test_data/complex_identifier_test.yaml'

        with open('tests/test_data/esri_wms_35bd4e2ce8cd13e8697b03976ffe1ee6.txt', 'r') as f:
            content = f.read()
        url = 'http://www.mapserver.com/cgi?SERVICE=WMS&VERSION=1.3.0&REQUEST=GETCAPABILITIES'

        self.identifier = Identify(yaml_file, content, url)
        self.identifier.identify()

        content = content.replace('\\n', '')
        self.parser = Parser(content)

    def test_identify_version(self):
        expected_version = '1.3.0'

        returned_version = self.identifier._identify_version('OGC', self.parser)

        self.assertTrue(expected_version == returned_version)

    def test_no_parser(self):
        returned_version = self.identifier._identify_version('OGC', None)
        self.assertTrue(not returned_version)


class TestVersionDefaults(unittest.TestCase):
    def setUp(self):
        yaml_file = 'tests/test_data/simple_identifier_test.yaml'

        content = '''<OpenSearch xmlns="http://a9.com/-/spec/opensearch/1.1/">
                        <element>OpenSearchDescription</element></OpenSearch>'''
        url = 'http://www.opensearch.com'

        self.identifier = Identify(yaml_file, content, url)
        self.identifier.identify()

    def test_default_version(self):
        expected_version = '1.1'

        returned_version = self.identifier._identify_version('OpenSearch', None)

        self.assertTrue(returned_version)
        self.assertTrue(expected_version == returned_version)


class TestVersionCombined(unittest.TestCase):
    def setUp(self):
        yaml_file = 'tests/test_data/combined_version_identifier_test.yaml'

        content = '''<catalog xmlns="http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0 http://www.unidata.ucar.edu/schemas/thredds/InvCatalog.1.0.2.xsd" 
    version="1.0.2" name="Actinic Flux measurements during OASIS Barrow field intensive Spring 2009"></catalog>'''
        url = 'http://www.unidata.com/hyrax/thredds'

        self.parser = Parser(content)

        self.identifier = Identify(yaml_file, content, url)
        self.identifier.identify()

    def test_default_version(self):
        expected_version = '1.0.2'

        returned_version = self.identifier._identify_version('UNIDATA', self.parser)

        self.assertTrue(returned_version)
        self.assertTrue(expected_version == returned_version)
