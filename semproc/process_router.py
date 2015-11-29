from semproc.preprocessors.opensearch_preprocessors import OpenSearchReader
from semproc.preprocessors.iso_preprocessors import IsoReader
from semproc.preprocessors.oaipmh_preprocessors import OaiPmhReader
from semproc.preprocessors.thredds_preprocessors import ThreddsReader
from semproc.preprocessors.xml_preprocessors import XmlReader
from semproc.preprocessors.ogc_preprocessors import OgcReader
from semproc.preprocessors.rdf_preprocessors import RdfReader
from semproc.preprocessors.metadata_preprocessors import FgdcItemReader
from semproc.parser import Parser
import sys


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
                 harvest_details={},
                 **kwargs):
        '''
        optional **kwargs keys:
            ignore_protocols: list of protocols
            parse_as_xml: if unknown identity, parse as basic XML
        '''
        # TODO: removed parent_url but may need to revisit as a
        #       harvest_detail AND where to get it
        self.optional_params = kwargs
        self.reader = self._instantiate(
            identification, response, source_url, harvest_details)

    def _instantiate(self, identity, response, url, harvest_details):
        '''
        set up the router
        '''
        # TODO: add a filter for known protocol with type
        #       data and bail
        identity = next(iter(identity), {})
        protocol = identity.get('protocol', '')

        if protocol and protocol in self.optional_params.get(
                'ignore_protocols', []):
            return None

        # remap for the reader names without "Reader"
        _remap = {
            "OAI-PMH": "OaiPmh",
            "OGC": "Ogc",
            "UNIDATA": "Thredds",
            "ISO": "Iso",
            "RDF": "Rdf",
            "FGDC": "FgdcItem"
        }
        # this is bad naming, but if the protocol value is
        # a key, get the value otherwise just hang onto it
        protocol = _remap.get(protocol, protocol)

        # we're going to pull the class name trick for the set
        # that is straightforward and hope not many are wonky
        protocol = 'Xml' if self.optional_params.get('parse_as_xml', False) \
            and not protocol else protocol

        # see if it's a loaded object
        try:
            reader_class = getattr(sys.modules[__name__], protocol + 'Reader')
        except AttributeError:
            # if it's not, we can't parse anyway
            return None

        if reader_class.__name__ in [
                'OpenSearchReader',
                'OaiPmhReader',
                'ThreddsReader',
                'IsoReader',
                'XmlReader',
                'OgcReader',
                'RdfReader']:
            # it's the standard processor init
            return reader_class(
                identity,
                response,
                url,
                harvest_details
            )
        elif reader_class.__name__ == 'FgdcItemReader':
            # TODO: this is baked into the others,
            #       we should take care of that
            parser = Parser(response)
            # TODO: don't forget to handle the harvest date
            return reader_class(parser.xml, url, harvest_details)

        return None
