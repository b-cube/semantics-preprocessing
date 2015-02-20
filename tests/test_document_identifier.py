import unittest


from lib.document_identifier import Identifier


class TestDocumentIdentifier(unittest.TestCase):

    def test_json_loads_properly(self):
        pass

    def test_malformed_json_doesnot_break_the_class(self):
        pass

    def _id_protocol(self, json_input, DocumentType):
        identifier = Identifier(json_input)
        tagged_documents = identifier.identify_solr_response()
        for doc in tagged_documents:
            self.assertEquals(
                doc['response']['docs'][0]['DocumentType'],
                DocumentType)

    def test_class_identifies_services(self):
        inputfiles = {
             'tests/test_data/responses/isos.json': 'ISO 19115:2003/19139',
             'tests/test_data/responses/opendap.json': 'OPeNDAP:OPeNDAP',
             'tests/test_data/responses/thredds.json': 'THREDDS'
        }
        for key, value in inputfiles.iteritems():
            print key, value
            self._id_protocol(key, value)
