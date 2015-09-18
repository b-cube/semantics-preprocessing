from semproc.preprocessors.opensearch_preprocessors import OpenSearchReader
from semproc.preprocessors.iso_preprocessors import IsoReader
from semproc.preprocessors.oaipmh_preprocessors import OaiPmhReader
from semproc.preprocessors.thredds_preprocessors import ThreddsReader
from semproc.preprocessors.xml_preprocessors import XmlReader
from semproc.preprocessors.ogc_preprocessors import OgcReader
from semproc.preprocessors.rdf_preprocessors import RdfReader
from semproc.preprocessors.metadata_preprocessors import FgdcItemReader
from semproc.parser import Parser


class Router():
    '''
    just a little router for all of the preprocessors
    we have

    so we get processor.reader.parse_service()
    not great but let's hide all of the options away
    and not give the processors more than they need
    '''
    def __init__(self,
                 identification,
                 response,
                 source_url,
                 parse_as_xml=True):
        self.identity = identification
        self.source_url = source_url
        self.parse_as_xml = parse_as_xml
        self.reader = self._instantiate(response, source_url)

    def _instantiate(self, response, url):
        '''
        set up the router
        '''
        protocol = next(iter(self.identity), {})
        protocol = protocol.get('protocol', '')

        if not protocol and self.parse_as_xml:
            # we will try a generic xml parser
            return XmlReader(response, url)

        if protocol == 'OpenSearch':
            return OpenSearchReader(self.identity, response, url)
        elif protocol == 'OAI-PMH':
            return OaiPmhReader(self.identity, response, url)
        elif protocol == 'UNIDATA':
            return ThreddsReader(self.identity, response, url)
        elif protocol in ['ISO']:
            # TODO: update this for the data series and service metadata
            return IsoReader(self.identity, response, url)
        elif protocol == 'FGDC':
            # TODO: this is baked into the others,
            #       we should take care of that
            parser = Parser(response)
            # TODO: don't forget to handle the harvest date
            return FgdcItemReader(parser.xml, url, '')
        elif protocol in ['OGC'] and 'error' not in protocol:
            return OgcReader(self.identity, response, url)
        elif protocol == 'RDF':
            return RdfReader(self.identity, response, url)

        if self.parse_as_xml:
            return XmlReader(response, url)

        raise Exception('Parser not instantiated.')
