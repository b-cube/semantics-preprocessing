import unittest
from lib.preprocessors.thredds_preprocessors import ThreddsReader
from lib.preprocessors.oaipmh_preprocessors import OaiPmhReader
from lib.preprocessors.opensearch_preprocessors import OpenSearchReader
from lib.preprocessors.xml_preprocessors import XmlReader


class TestBaseReader(unittest.TestCase):
    def setUp(self):
        pass

    def test_load_xml(self):
        # honestly, this is just a parser test
        pass

    def test_return_descriptors(self):
        pass

    def return_everything_else(self):
        pass


class TestThreddsReader(unittest.TestCase):
    def setUp(self):
        # this response doesn't come from nay harvest
        with open('tests/test_data/thredds_catalog_eol.xml', 'r') as f:
            text = f.read()
        self.reader = ThreddsReader(text)
        self.reader._load_xml()

    def test_return_descriptors(self):
        descriptors = self.reader.return_service_descriptors()

        self.assertTrue('Actinic Flux' in descriptors['title'])
        self.assertTrue(descriptors['version'] == "1.0.2")

    def test_return_everything_else(self):
        excluded = self.reader.return_exclude_descriptors()
        remainder = self.reader.return_everything_else(excluded)

        self.assertTrue(len(remainder) > 0)
        self.assertTrue(remainder[1][2][0][0] == 'codiac_order')
        self.assertTrue(remainder[2][1] == '{http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0}catalog/{http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0}dataset')


class TestOaiPmhReader(unittest.TestCase):
    def setUp(self):
        # this response doesn't come from nay harvest
        with open('tests/test_data/oaipmh_identify.xml', 'r') as f:
            text = f.read()
        self.reader = OaiPmhReader(text)
        self.reader._load_xml()

    def test_return_descriptors(self):
        descriptors = self.reader.return_service_descriptors()

        self.assertTrue('Aberdeen' in descriptors['title'])
        self.assertTrue(descriptors['version'] == "2.0")
        self.assertTrue(descriptors['source'] == 'http://aura.abdn.ac.uk/dspace-oai/request')


class TestOpenSearchReader(unittest.TestCase):
    def setUp(self):
        with open('tests/test_data/basic_osdd_c1576284036448b5ef3d16b2cd37acbc.txt', 'r') as f:
            text = f.read()
        text = text.replace('\\n', ' ')
        self.reader = OpenSearchReader(text)
        self.reader._load_xml()

    def test_return_descriptors(self):
        descriptors = self.reader.return_service_descriptors()

        self.assertTrue('CEOS' in descriptors['title'])
        self.assertTrue('version' not in descriptors)
        self.assertTrue(descriptors['description'] is None)


class TestOpenSearchReaderWithEndpoints(unittest.TestCase):
    def setUp(self):
        with open('tests/test_data/opensearch-nasa.xml', 'r') as f:
            text = f.read()
        self.reader = OpenSearchReader(text)
        self.reader._load_xml()

    def test_parse_endpoints(self):
        endpoints = self.reader.parse_endpoints()

        self.assertTrue(len(endpoints) == 2)
        self.assertTrue(len(endpoints[0][2][0]) == 5)
        self.assertTrue(isinstance(endpoints[0][2][0][1], dict))
        self.assertTrue(endpoints[0][2][0][2] == 'MODAPSParameters')
        self.assertTrue(endpoints[0][1] == 'http://modwebsrv.modaps.eosdis.nasa.gov/axis2/services/MODAPSservices/getOpenSearch?products={MODAPSParameters:products}&collection={MODAPSParameters:collection?}&start={time:start}&stop={time:stop}&bbox={geo:box}&coordsOrTiles={MODAPSParameters:coordsOrTiles?}&dayNightBoth={MODAPSParameters:dayNightBoth?}')

    def test_extract_parameter_type(self):
        with_brackets = '{geo:bbox}'
        without_brackets = 'time:start'
        singleton = 'coords'

        test_tuple = self.reader._extract_parameter_type(singleton)
        self.assertTrue(test_tuple == ('', singleton))

        test_tuple = self.reader._extract_parameter_type(with_brackets)
        self.assertTrue(test_tuple[0] == 'geo')
        self.assertTrue(test_tuple[1] == 'bbox')

        test_tuple = self.reader._extract_parameter_type(without_brackets)
        self.assertTrue(test_tuple[0] == 'time')
        self.assertTrue(test_tuple[1] == 'start')

    def test_extract_url_parameters(self):
        url = self.reader.parser.find('/{http://a9.com/-/spec/opensearch/1.1/}OpenSearchDescription/{http://a9.com/-/spec/opensearch/1.1/}Url')
        url = url[0].get('template', '')
        params = self.reader._extract_url_parameters(url)

        self.assertTrue(len(params) == 7)
        self.assertTrue(params[0][0] == 'coordsOrTiles')
        self.assertTrue(params[6][4] == 'west, south, east, north')


class TestXmlReader(unittest.TestCase):
    def setUp(self):
        with open('tests/test_data/random_bit_of_xml.xml', 'r') as f:
            text = f.read()
        text = text.replace('\\n', ' ')
        self.reader = XmlReader(text)
        self.reader._load_xml()

    def test_return_service(self):
        service = self.reader.parse_service()

        fourth_tuple = ('/namma/report/smart_commit',
               '{http://archipelago.phrasewise.com/rsd}rsd/{http://archipelago.phrasewise.com/rsd}service/{http://archipelago.phrasewise.com/rsd}homePageLink',
               None)

        self.assertTrue('remainder' in service)
        self.assertTrue(len(service['remainder']) == 9)
        self.assertTrue('service' not in service)

        self.assertTrue(service['remainder'][3] == fourth_tuple)
