from semproc.processor import Processor
from semproc.preprocessors.metadata_preprocessors import DcItemReader
from semproc.xml_utils import extract_items, extract_elems, extract_item, extract_elem
from semproc.utils import tidy_dict
from itertools import chain
from semproc.utils import generate_sha_urn, generate_uuid_urn


class OaiPmhReader(Processor):
    def parse(self):
        self.description = {}
        if 'parent_url' in self.harvest_details:
            self.description['childOf'] = self.harvest_details['parent_url']

        if 'service' in self.identify:
            self.description = self._parse_service()

        if 'resultset' in self.identify:
            self.description['children'] = self._parse_children(
                self.identify['resultset'].get('dialect', ''))

        self.description = tidy_dict(self.description)

    def _parse_service(self):
        output = {}

        service = {
            "object_id": generate_uuid_urn(),
            "dcterms:title": ' '.join(extract_items(
                self.parser.xml, ["Identify", "repositoryName"])),
            "rdf:type": "OAI-PMH",
            "relationships": [],
            "urls": []
        }
        url_id = generate_uuid_urn()
        dist = self._generate_harvest_manifest(**{
            "bcube:hasUrlSource": "Harvested",
            "bcube:hasConfidence": "Good",
            "vcard:hasURL": self.url,
            "object_id": url_id,
            "dc:identifier": generate_sha_urn(self.url)
        })
        service['urls'] = [dist]
        service['relationships'].append({
            "relate": "bcube:originatedFrom",
            "object_id": url_id
        })

        # output['version'] = extract_items(self.parser.xml, ["Identify", "protocolVersion"])
        # output['endpoints'] = [{'url': e} for e
        #                        in extract_items(self.parser.xml, ["Identify", "baseURL"])]

        output['services'] = [service]
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
                    dc_parser.parse_item().items()
                )
            )
