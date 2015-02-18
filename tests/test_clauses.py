import unittest
import json

from lib.clause_generator import *


class TestClauseGenerator(unittest.TestCase):
    def setUp(self):
        self.yaml_file = 'lib/configs/identifiers.yaml'

        self.data = build_clauses(self.yaml_file)

    def test_load_yaml(self):
        self.assertTrue(self.data['protocols'][0]['name'] == 'OGC')

        names = [p['name'] for p in self.data['protocols']]
        self.assertTrue(len(names) == 6)

    def test_build_clauses_by_protocol(self):
        protocol = 'OpenSearch'

        service = build_service_clauses(protocol, self.yaml_file,
            'i am some content OpenSearchDescription of stuff', 'http://opensearch.com')
        self.assertTrue(service is not None)
        self.assertTrue('OpenSearchDescription' == service)
