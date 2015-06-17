from lib.processor import Processor
from lib.preprocessors.metadata_preprocessors import DcItemReader
from lib.xml_utils import extract_items, extract_elems, extract_item, extract_elem
from lib.utils import tidy_dict
from itertools import chain


class OaiPmhReader(Processor):
    def parse(self):
        self.description = {}
        if self.parent_url:
            self.description['childOf'] = self.parent_url

        if 'service' in self.identify:
            self.description['service'] = self._parse_service()

        if 'resultset' in self.identify:
            self.description['children'] = self._parse_children(
                self.identify['resultset'].get('dialect', ''))

        self.description = tidy_dict(self.description)

    def _parse_service(self):
        output = {}
        output['title'] = extract_items(self.parser.xml, ["Identify", "repositoryName"])
        output['version'] = extract_items(self.parser.xml, ["Identify", "protocolVersion"])
        output['endpoints'] = [{'url': e} for e
                               in extract_items(self.parser.xml, ["Identify", "baseURL"])]

        return tidy_dict(output)

    def _parse_children(self, dialect):
        elems = extract_elems(self.parser.xml, ['ListRecords', 'record'])
        return [self._parse_child(child, dialect) for child in elems]

    def _parse_child(self, child, dialect):
        identifier = extract_item(child, ['header', 'identifier'])
        timestamp = extract_item(child, ['header', 'datestamp'])

        if dialect == 'oai_dc':
            dc_elem = extract_elem(child, ['metadata', 'dc'])
            dc_parser = DcItemReader(dc_elem)
            return dict(
                chain(
                    {"identifier": identifier, "timestamp": timestamp}.items(),
                    dc_parser.parse().items()
                )
            )


    # def parse_result_set(self):
    #     results = []
    #     if self.parser.xml is None:
    #         return results

    #     metadata_prefix = extract_attrib(self.parser.xml, ['request', '@metadataPrefix'])
    #     if metadata_prefix not in ['oai_dc']:
    #         return results

    #     elems = extract_elems(self.parser.xml, ['ListRecords', 'record'])
    #     for elem in elems:
    #         # get a few bits from the header
    #         identifier = extract_item(elem, ['header', 'identifier'])
    #         timestamp = extract_item(elem, ['header', 'datestamp'])

    #         # send the actual record to a simple parser
    #         if metadata_prefix == 'oai_dc':
    #             dc_elem = extract_elem(elem, ['metadata', 'dc'])
    #             parser = DcReader(self._response, self._url)  # TODO: again not this
    #             results.append({
    #                 "identifier": identifier,
    #                 "timestamp": timestamp,
    #                 "metadata": parser.parse_item(dc_elem)
    #             })

    #     return results
