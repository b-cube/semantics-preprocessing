from semproc.preprocessors.opensearch_preprocessors import OpenSearchReader
from semproc.preprocessors.iso_preprocessors import IsoReader
from semproc.preprocessors.oaipmh_preprocessors import OaiPmhReader
from semproc.preprocessors.thredds_preprocessors import ThreddsReader
from semproc.preprocessors.xml_preprocessors import XmlReader
from semproc.preprocessors.ogc_preprocessors import OgcReader
from semproc.preprocessors.rdf_preprocessors import RdfReader


class Router():
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
            # we will try a generic xml parser
            self.reader = XmlReader(response, url)

        if protocol == 'OpenSearch':
            self.reader = OpenSearchReader(self.identity, response, url)
        elif protocol == 'OAI-PMH':
            self.reader = OaiPmhReader(self.identity, response, url)
        elif protocol == 'UNIDATA':
            self.reader = ThreddsReader(self.identity, response, url)
        elif protocol in ['ISO']:
            # TODO: update this for the data series and service metadata
            self.reader = IsoReader(self.identity, response, url)
        elif protocol in ['OGC'] and 'error' not in protocol:
            self.reader = OgcReader(self.identity, protocol, version, response, url)
        elif protocol == 'RDF':
            self.reader = RdfReader(self.identity, response, url)
