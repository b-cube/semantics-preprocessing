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
        self.assertTrue(self.identifier.yaml)
        self.assertTrue(len(self.identifier.yaml) == 1)
        self.assertTrue(self.identifier.yaml[0]['name'] == 'OpenSearch')

        names = [p['name'] for p in self.identifier.yaml]
        self.assertTrue(len(names) == 1)

    def test_identify_protocol(self):
        expected_protocol = 'OpenSearch'
        returned_protocol, returned_subtype = self.identifier._identify_protocol()
        self.assertTrue(expected_protocol == returned_protocol)
        self.assertTrue('service' == returned_subtype)

    def test_identify_service_from_protocol(self):
        expected_service = 'OpenSearchDescription'
        protocol_data = next(p for p in self.identifier.yaml if p['name'] == 'OpenSearch')
        returned_service = self.identifier._identify_service_of_protocol(protocol_data)

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
        self.assertTrue(self.identifier.yaml[2]['name'] == 'OGC:WMS')

        names = [p['name'] for p in self.identifier.yaml]
        self.assertTrue(len(names) == 6)

        ogc_protocol = self.identifier.yaml[0]
        self.assertTrue('service_description' in ogc_protocol)
        self.assertTrue(len(ogc_protocol['service_description']) == 1)

    def test_identify_protocol(self):
        expected_protocol = 'OGC:WMS'
        returned_protocol, returned_subtype = self.identifier._identify_protocol()
        self.assertTrue(expected_protocol == returned_protocol)

    def test_identify_service_from_protocol(self):
        expected_service = 'GetCapabilities'
        protocol_data = next(p for p in self.identifier.yaml if p['name'] == 'OGC:WMS')
        returned_service = self.identifier._identify_service_of_protocol(protocol_data)

        self.assertTrue(returned_service)
        self.assertTrue(expected_service == returned_service)

    def test_is_error(self):
        protocol_data = next(p for p in self.identifier.yaml if p['name'] == 'OGC:WMS')
        returned_error = self.identifier._is_protocol_error(protocol_data)
        self.assertFalse(returned_error)

    def test_identify(self):
        # just run it again?

        self.identifier.identify()

        self.assertFalse(self.identifier.is_error)
        self.assertTrue(self.identifier.protocol == 'OGC:WMS')
        self.assertTrue(self.identifier.service == 'GetCapabilities')
        self.assertTrue(self.identifier.version)
        self.assertTrue(self.identifier.version == '1.3.0')

    def test_generate_urn(self):
        expected_urn = 'urn:OGC:WMS:GetCapabilities:1.3.0'
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
        protocol_data = next(p for p in self.identifier.yaml if p['name'] == 'OGC:error')
        returned_error = self.identifier._is_protocol_error(protocol_data)
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

        protocol_data = next(p for p in self.identifier.yaml if p['name'] == 'OGC:WMS')
        returned_version = self.identifier._identify_version(protocol_data, self.parser)

        self.assertTrue(expected_version == returned_version)

    def test_no_parser(self):
        protocol_data = next(p for p in self.identifier.yaml if p['name'] == 'OGC:WMS')
        returned_version = self.identifier._identify_version(protocol_data, None)
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

        protocol_data = next(p for p in self.identifier.yaml if p['name'] == 'OpenSearch')

        returned_version = self.identifier._identify_version(protocol_data, None)

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

        protocol_data = next(p for p in self.identifier.yaml if p['name'] == 'UNIDATA')

        returned_version = self.identifier._identify_version(protocol_data, self.parser)

        self.assertTrue(returned_version)
        self.assertTrue(expected_version == returned_version)


class TestIso(unittest.TestCase):
    def setUp(self):
        self.yaml_file = 'lib/configs/iso_identifier.yaml'

    def test_if_returning_iso_protocol_for_chunk(self):
        with open('tests/test_data/invalid_iso_chunk.xml', 'r') as f:
            content = f.read()
        url = 'http://www.mapserver.com/some_iso'

        content = content.replace('\\n', '')
        parser = Parser(content)

        identifier = Identify(self.yaml_file, content, url, **{'parser': parser})
        identifier.identify()

        self.assertFalse(identifier.protocol == 'ISO-19115')

    def test_if_returning_iso_protocol_for_mi(self):
        with open('tests/test_data/iso-19115_mi.xml', 'r') as f:
            content = f.read()
        url = 'http://www.mapserver.com/some_iso'

        content = content.replace('\\n', '')
        parser = Parser(content)

        identifier = Identify(self.yaml_file, content, url, **{'parser': parser})
        identifier.identify()

        self.assertTrue(identifier.protocol == 'ISO-19115')

    def test_if_returning_iso_protocol_for_md(self):
        with open('tests/test_data/iso-19115_md.xml', 'r') as f:
            content = f.read()
        url = 'http://www.mapserver.com/some_iso'

        content = content.replace('\\n', '')
        parser = Parser(content)

        identifier = Identify(self.yaml_file, content, url, **{'parser': parser})
        identifier.identify()

        self.assertTrue(identifier.protocol == 'ISO-19115')

    def test_if_returning_iso_protocol_for_ds(self):
        with open('tests/test_data/iso-19115_ds.xml', 'r') as f:
            content = f.read()
        url = 'http://www.mapserver.com/some_iso'

        content = content.replace('\\n', '')
        parser = Parser(content)

        identifier = Identify(self.yaml_file, content, url, **{'parser': parser})
        identifier.identify()

        self.assertTrue(identifier.protocol == 'ISO-19115 DS')
        self.assertTrue(identifier.version == 'ISO19115 (2003/Cor.1:2006)')


class TestWfsIdentification(unittest.TestCase):
    def setUp(self):
        yaml_file = 'tests/test_data/complex_identifier_test.yaml'

        with open('tests/test_data/wfs_v1_1_0.xml', 'r') as f:
            content = f.read()
        url = 'http://www.mapserver.com/cgi?SERVICE=WFS&VERSION=1.1.0&REQUEST=GETCAPABILITIES'

        content = content.replace('\\n', '')
        parser = Parser(content)

        self.identifier = Identify(yaml_file, content, url, **{'parser': parser})
        # self.identifier.identify()

    def test_identify_dataset(self):
        protocol_data = next(p for p in self.identifier.yaml if p['name'] == 'OGC:WFS')
        has_dataset = self.identifier._identify_dataset_service(protocol_data)

        self.assertTrue(has_dataset)

    def test_identify_metadata(self):
        protocol_data = next(p for p in self.identifier.yaml if p['name'] == 'OGC:WFS')
        has_metadata = self.identifier._identify_metadata_service(protocol_data)

        self.assertTrue(has_metadata)


class TestWmsIdentification(unittest.TestCase):
    def setUp(self):
        yaml_file = 'tests/test_data/complex_identifier_test.yaml'

        with open('tests/test_data/esri_wms_35bd4e2ce8cd13e8697b03976ffe1ee6.txt', 'r') as f:
            content = f.read()
        url = 'http://www.mapserver.com/cgi?SERVICE=WMS&VERSION=1.3.0&REQUEST=GETCAPABILITIES'

        content = content.replace('\\n', '')
        parser = Parser(content)

        self.identifier = Identify(yaml_file, content, url, **{'parser': parser})
        # self.identifier.identify()

    def test_identify_dataset(self):
        protocol_data = next(p for p in self.identifier.yaml if p['name'] == 'OGC:WMS')
        has_dataset = self.identifier._identify_dataset_service(protocol_data)

        self.assertFalse(has_dataset)

    def test_identify_metadata(self):
        protocol_data = next(p for p in self.identifier.yaml if p['name'] == 'OGC:WMS')
        has_metadata = self.identifier._identify_metadata_service(protocol_data)

        self.assertFalse(has_metadata)
