import unittest
import json

from lib.document_identifier import Identifier


class TestDocumentIdentifier(unittest.TestCase):

    def setUp(self):
        self.identifier = Identifier('tests/test_data/isos.json')

    def tearDown(self):
        self.identifier = None

    def test_json_loads_properly(self):
        pass

    def test_malformed_json_doesnot_break_the_class(self):
        pass

    def test_class_identifies_solr_response(self):
        tagged_documents = self.identifier.identify_solr_response()
        for doc in tagged_documents:
            self.assertEquals(
                doc['response']['docs'][0]['DocumentType'],
                "ISO 19115:2003/19139")
