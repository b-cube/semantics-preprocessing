from lib.base_preprocessors import BaseReader
from lib.preprocessors.metadata_preprocessors import DcReader
from lib.xml_utils import extract_items, extract_elems, extract_item, extract_attrib, extract_elem
from lxml import etree


class OaiPmhReader(BaseReader):
    _service_descriptors = {
        "title": ["OAI-PMH", "Identify", "repositoryName"],
        "version": ["OAI-PMH", "Identify", "protocolVersion"]
    }

    def parse_endpoints(self):
        '''
        return the baseUrl (should match the base of the identify
            request anyway, but let's make it explicit)
        '''
        urls = extract_items(self.parser.xml, ["OAI-PMH", "Identify", "baseURL"])

        return [
            {
                "url": url
            } for url in urls
        ]

    def parse_result_set(self):
        results = []
        if self.parser.xml is None:
            return results

        metadata_prefix = extract_attrib(self.parser.xml, ['request', '@metadataPrefix'])
        if metadata_prefix not in ['oai_dc']:
            return results

        elems = extract_elems(self.parser.xml, ['ListRecords', 'record'])
        for elem in elems:
            # get a few bits from the header
            identifier = extract_item(elem, ['header', 'identifier'])
            timestamp = extract_item(elem, ['header', 'datestamp'])

            # send the actual record to a simple parser
            if metadata_prefix == 'oai_dc':
                dc_elem = extract_elem(elem, ['metadata', 'dc'])
                parser = DcReader(self._response, self._url)  # TODO: again not this
                results.append({
                    "identifier": identifier,
                    "timestamp": timestamp,
                    "metadata": parser.parse_item(dc_elem)
                })

        return results
