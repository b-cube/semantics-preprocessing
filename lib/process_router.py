from lib.preprocessors.opensearch_preprocessors import OpenSearchReader
from lib.preprocessors.iso_preprocessors import IsoReader
from lib.preprocessors.oaipmh_preprocessors import OaiPmhReader
from lib.preprocessors.thredds_preprocessors import ThreddsReader
from lib.preprocessors.xml_preprocessors import XmlReader
from lib.preprocessors.ogc_preprocessors import OgcReader


class Processor():
    '''
    just a little router for all of the preprocessors
    we have

    so we get processor.reader.parse_service()
    not great but let's hide all of the options away
    and not give the processors more than they need
    '''
    def __init__(self, identification, response, source_url):
        self.identity = identification
        self.source_url = source_url
        self._instantiate(response, source_url)

    def _instantiate(self, response, url):
        '''
        set up the router
        '''
        protocol = self.identity['protocol']
        version = self.identity['version']

        if not protocol:
            return None

        if protocol == 'OpenSearch':
            self.reader = OpenSearchReader(response, url)
        elif protocol == 'OAI-PMH':
            self.reader = OaiPmhReader(response, url)
        elif protocol == 'UNIDATA':
            self.reader = ThreddsReader(response, url)
        elif protocol in ['ISO-19115']:
            # TODO: update this for the data series and service metadata
            self.reader = IsoReader(response, url)
        elif protocol.startswith('OGC:') and 'error' not in protocol:
            self.reader = OgcReader(protocol.split(':')[-1], version, response, url)
        else:
            # we will try a generic xml parser
            self.reader = XmlReader(response, url)
