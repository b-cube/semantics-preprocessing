import json


class Identifier():
    '''
    For now this class is using json files but eventually it will have to
    be used in the context of the whole stack. i.e.

    services = identify(SolrResponseObject)

    Services will be a JSON object with the solr response
    plus the kvp "DocType" : "OpenSearch" for each document.
    '''

    def __init__(self, solr_response):
        with open('local/fingerprints.json', 'r') as fp:
            self.fingerprints = json.loads(fp.read())
        with open(solr_response, 'r') as sr:
            response = json.loads(sr.read())
        self.responses = response['responses']
        # Eventually Solr response should be what's inside of Solr docs

    def _get_raw_content(self, doc):
        '''
        This method will change depending on what we agree on
        what should be returned from solr.py
        '''
        try:
            content = doc['response']['docs'][0]['raw_content'].encode(
                'unicode_escape').replace("<![CDATA[", "").replace("]]>", "")
        except Exception:
            print Exception
            content = None
        return content

    def _get_url(self, doc):
        '''
        This method will change depending on what we agree on
        what should be returned from solr.py
        '''
        try:
            url = doc['response']['docs'][0]['id']
        except Exception:
            print Exception
            url = None
        return url

    def _save_tagged_files(self, path):
        '''
        This method will save the tagged documents into a file
        or it will send it to a REST endpoint.
        '''
        with open(path, 'w') as out:
            json.dump(self.responses, out)

    def _set_document_type(self, doc, doc_type):
        doc['response']['docs'][0]['DocumentType'] = doc_type

    def identify_solr_response(self):
        for response in self.responses:
            raw_content = self._get_raw_content(response)
            url = self._get_url(response)
            doc_type = self.identify(raw_content, url)
            self._set_document_type(response, doc_type)
        return self.responses

    def identify(self, raw_content, url):
        for doc_type in self.fingerprints:
            for fp in doc_type['fingerprint']:
                print fp
                if (fp in raw_content or doc_type['url'] in url):
                    return doc_type["DocType"]
        return None
