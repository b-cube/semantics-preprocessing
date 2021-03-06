import unittest
from lib.preprocessors.thredds_preprocessors import ThreddsReader
from lib.preprocessors.oaipmh_preprocessors import OaiPmhReader
from lib.preprocessors.opensearch_preprocessors import OpenSearchReader
from lib.preprocessors.xml_preprocessors import XmlReader
from lib.preprocessors.iso_preprocessors import IsoReader


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


class TestThreddsReaderAcdisc(unittest.TestCase):
    def setUp(self):
        # this response doesn't come from any harvest
        with open('tests/test_data/mod_acdisc.xml', 'r') as f:
            text = f.read()
        self.reader = ThreddsReader(text)
        self.reader._load_xml()

    def test_parse_endpoints(self):
        endpoints = self.reader.parse_endpoints()

        self.assertTrue(endpoints)
        self.assertTrue(len(endpoints) == 5)

        # get the parent dataset
        parent = next(iter([e for e in endpoints if e['source'] == 'dataset' and
                           'parentOf' in e]), [])
        self.assertTrue(parent)

        parent_id = parent['ID']
        children_ids = parent['parentOf']
        children = [e for e in endpoints if e['ID'] in children_ids]
        self.assertTrue(len(children) == 2)
        self.assertTrue(children[0]['childOf'] == parent_id)
        self.assertTrue('datasize' in children[0])
        self.assertTrue('access' in children[0])
        self.assertTrue(children[0]['access']['serviceName'] == 'file')
        self.assertTrue(children[0]['datasize']['units'] == 'bytes')

    def test_return_everything_else(self):
        pass


class TestThreddsReaderEol(unittest.TestCase):
    def setUp(self):
        # this response doesn't come from any harvest
        with open('tests/test_data/mod_eol_arcss.xml', 'r') as f:
            text = f.read()
        self.reader = ThreddsReader(text)
        self.reader._load_xml()

    def test_parse_endpoints(self):
        endpoints = self.reader.parse_endpoints()

        self.assertTrue(endpoints)
        self.assertTrue(len(endpoints) == 6)

        # get the parent dataset
        parent = next(iter([e for e in endpoints if e['source'] == 'dataset' and
                           'parentOf' in e]), [])
        self.assertTrue(parent)

        parent_id = parent['ID']
        children_ids = parent['parentOf']
        children = [e for e in endpoints if e['ID'] in children_ids]
        self.assertTrue(len(children) == 5)
        self.assertTrue(children[0]['childOf'] == parent_id)

        self.assertTrue(len([c for c in children if c['source'] == 'metadata']) == 1)
        self.assertTrue(len([c for c in children if c['source'] == 'catalogRef']) == 4)
        self.assertTrue('href' in children[2])
        self.assertTrue(parent['name'] == 'ARCSS: NSF Arctic System Science')

    def test_return_everything_else(self):
        pass


class TestThreddsReaderLadsweb(unittest.TestCase):
    def setUp(self):
        # this response doesn't come from any harvest
        with open('tests/test_data/mod_ladsweb.xml', 'r') as f:
            text = f.read()
        self.reader = ThreddsReader(text)
        self.reader._load_xml()

    def test_parse_endpoints(self):
        endpoints = self.reader.parse_endpoints()

        self.assertTrue(endpoints)
        self.assertTrue(len(endpoints) == 7)

        services = [c for c in endpoints if c['source'] == 'service']
        self.assertTrue(len(services) == 2)
        self.assertTrue(services[0]['name'] == 'dap')
        self.assertTrue(services[1]['serviceType'] == 'HTTPServer')

        # get the parent dataset
        parent = next(iter([e for e in endpoints if e['source'] == 'dataset' and
                           'parentOf' in e]), [])
        self.assertTrue(parent)

        parent_id = parent['ID']
        children_ids = parent['parentOf']
        children = [e for e in endpoints if e['ID'] in children_ids]

        self.assertTrue(len(children) == 4)
        self.assertTrue(children[0]['childOf'] == parent_id)

        self.assertTrue(len([c for c in children if c['source'] == 'dataset']) == 1)
        self.assertTrue(len([c for c in children if c['source'] == 'dataset' and
                             c['access']['serviceName'] == 'file']) == 1)
        self.assertTrue(len([c for c in children if c['source'] == 'catalogRef']) == 3)
        self.assertTrue('href' in children[2])
        self.assertTrue([c for c in children if c['source'] == 'catalogRef' and
                         c['ID'] == '/opendap/hyrax/allData/55/MOD17A3/2001/'])

        self.assertTrue(parent['name'] == '/allData/55/MOD17A3')

    def test_return_everything_else(self):
        pass


class TestThreddsReaderStellwagen(unittest.TestCase):
    def setUp(self):
        # this response doesn't come from any harvest
        with open('tests/test_data/mod_stellwagen.xml', 'r') as f:
            text = f.read()
        self.reader = ThreddsReader(text)
        self.reader._load_xml()

    def test_parse_endpoints(self):
        endpoints = self.reader.parse_endpoints()

        self.assertTrue(endpoints)
        self.assertTrue(len(endpoints) == 14)

        # get the parent dataset
        parent = next(iter([e for e in endpoints if e['source'] == 'dataset' and
                           'parentOf' in e]), [])
        self.assertTrue(parent)

        parent_id = parent['ID']
        children_ids = parent['parentOf']
        children = [e for e in endpoints if e['ID'] in children_ids]
        self.assertTrue(len(children) == 4)
        self.assertTrue(children[0]['childOf'] == parent_id)

        metadata = [c for c in children if c['source'] == 'metadata']
        self.assertTrue(len(metadata) == 1)
        self.assertTrue(metadata[0]['service'] == 'allServices')
        # no catalogRefs
        self.assertFalse(len([c for c in children if c['source'] == 'catalogRef']) > 0)
        self.assertTrue('urlPath' in children[2])
        self.assertTrue(parent['name'] == 'PV_SHELF')

    def test_return_everything_else(self):
        pass


class TestOaiPmhReader(unittest.TestCase):
    def setUp(self):
        # this response doesn't come from nay harvest
        with open('tests/test_data/oaipmh_identify.xml', 'r') as f:
            text = f.read()
        self.reader = OaiPmhReader(text)
        self.reader._load_xml()

    def test_return_descriptors(self):
        descriptors = self.reader.return_service_descriptors()

        self.assertTrue('Aberdeen' in descriptors['title'][0])
        self.assertTrue(descriptors['version'][0] == "2.0")
        self.assertTrue(descriptors['endpoints'][0]['url'] ==
                        'http://aura.abdn.ac.uk/dspace-oai/request')


class TestOpenSearchReader(unittest.TestCase):
    def setUp(self):
        with open('tests/test_data/basic_osdd_c1576284036448b5ef3d16b2cd37acbc.txt', 'r') as f:
            text = f.read()
        text = text.replace('\\n', ' ')
        self.reader = OpenSearchReader(text, '')
        self.reader._load_xml()

    def test_return_descriptors(self):
        descriptors = self.reader.return_service_descriptors()

        self.assertTrue('CEOS' in descriptors['title'][0])
        self.assertTrue('version' not in descriptors)
        self.assertTrue(descriptors['abstract'][0] is None)


class TestOpenSearchReaderWithEndpoints(unittest.TestCase):
    def setUp(self):
        with open('tests/test_data/opensearch-nasa.xml', 'r') as f:
            text = f.read()
        self.reader = OpenSearchReader(text, '')
        self.reader._load_xml()

    def test_parse_service(self):
        '''
        just the remainders right now
        '''

        should_not_have = '{http://a9.com/-/spec/opensearch/1.1/}' + \
                          'OpenSearchDescription/' + \
                          '{http://a9.com/-/spec/opensearch/1.1/}Url'
        service = self.reader.parse_service()

        self.assertTrue('remainder' in service)

        remainder = service['remainder']

        self.assertTrue(should_not_have in remainder)

    def test_parse_endpoints(self):
        endpoints = self.reader.parse_endpoints()

        print endpoints

        expected_endpoint = 'http://modwebsrv.modaps.eosdis.nasa.gov/axis2/' + \
                            'services/MODAPSservices/getOpenSearch?' + \
                            'products={MODAPSParameters:products}&' + \
                            'collection={MODAPSParameters:collection?}' + \
                            '&start={time:start}&stop={time:stop}&bbox={geo:box}' + \
                            '&coordsOrTiles={MODAPSParameters:coordsOrTiles?}' + \
                            '&dayNightBoth={MODAPSParameters:dayNightBoth?}'

        self.assertTrue(len(endpoints) == 2)
        self.assertTrue(len(endpoints[0]['parameters'][0]) == 5)
        self.assertTrue(isinstance(endpoints[0]['parameters'][0]['namespaces'], dict))
        self.assertTrue(endpoints[0]['parameters'][0]['prefix'] == 'MODAPSParameters')
        self.assertTrue(endpoints[0]['url'] == expected_endpoint)

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
        url_xpath = '/{http://a9.com/-/spec/opensearch/1.1/}OpenSearchDescription/' +\
                    '{http://a9.com/-/spec/opensearch/1.1/}Url'
        url = self.reader.parser.find(url_xpath)
        url = url[0].get('template', '')
        params = self.reader._extract_url_parameters(url)

        self.assertTrue(len(params) == 7)
        self.assertTrue(params[0]['name'] == 'coordsOrTiles')
        self.assertTrue(params[6]['formats'] == 'west, south, east, north')


class TestXmlReader(unittest.TestCase):
    def setUp(self):
        with open('tests/test_data/random_bit_of_xml.xml', 'r') as f:
            text = f.read()
        text = text.replace('\\n', ' ')
        self.reader = XmlReader(text)
        self.reader._load_xml()

    def test_return_service(self):
        service = self.reader.parse_service()

        fourth_tuple = {'attributes': None,
                        'text': '/namma/report/smart_commit',
                        'xpath': '{http://archipelago.phrasewise.com/rsd}rsd/' +
                                 '{http://archipelago.phrasewise.com/rsd}service/' +
                                 '{http://archipelago.phrasewise.com/rsd}homePageLink'}

        self.assertTrue('remainder' in service)
        self.assertTrue(len(service['remainder']) == 9)
        self.assertTrue('service' not in service)

        self.assertTrue(service['remainder'][3] == fourth_tuple)


class TestIsoReader(unittest.TestCase):
    def setUp(self):
        with open('tests/test_data/iso-19115_mi.xml', 'r') as f:
            text = f.read()
        text = text.replace('\\n', ' ')
        self.reader = IsoReader(text)
        self.reader._load_xml()

    def test_return_descriptors(self):
        descriptors = self.reader.return_service_descriptors()

        self.assertTrue('Survey, Massachusetts Bay, Massachusetts,' in descriptors['title'][0])
        self.assertTrue('version' not in descriptors)
        self.assertTrue('Massachusetts Bay' in descriptors['subject'])
        self.assertTrue(len(descriptors['subject']) == 15)
        self.assertTrue(descriptors['language'][0] == 'eng')

    def test_parse_endpoints(self):
        endpoints = self.reader.parse_endpoints()

        expected_url = 'http://surveys.ngdc.noaa.gov/mgg/NOS/coast/' + \
                       'H08001-H10000/H08413/Smooth_Sheets/H08413.tif.gz'
        expected_format = 'SMOOTH_SHEET'

        self.assertTrue(len(endpoints) == 4)
        self.assertTrue(endpoints[2]['type'] == 'download')
        self.assertTrue(endpoints[1]['url'] == expected_url)
        self.assertTrue(endpoints[1]['format'] == expected_format)
