import re
from semproc.processor import Processor
from semproc.utils import parse_url, tidy_dict
from semproc.xml_utils import extract_elems, extract_items, extract_item
from semproc.urlbuilders.opensearch_links import OpenSearchLink
from semproc.utils import generate_sha_urn, generate_uuid_urn


class OpenSearchReader(Processor):
    # parent_url is contained in harvest_details
    def parse(self):
        self.description = {}

        if "parent_url" in self.harvest_details:
            # TODO: consider making this a sha
            self.description['childOf'] = self.harvest_details['parent_url']

        if 'service' in self.identify:
            self.description = self._parse_service()

        if 'resultset' in self.identify:
            # TODO: get the root stats
            self.description['children'] = self._parse_children(
                self.identify['resultset'].get('dialect', ''))

        self.description = tidy_dict(self.description)

    def _parse_service(self):
        output = {}
        urls = set()

        service = {
            "object_id": generate_uuid_urn(),
            "bcube:dateCreated": self.harvest_details.get('harvest_date', ''),
            "bcube:lastUpdated": self.harvest_details.get('harvest_date', ''),
            "rdf:type": 'OpenSearch1.1:Description',
            "dcterms:title": extract_item(self.parser.xml, ["ShortName"]),
            "dc:description": ' '.join(
                extract_items(self.parser.xml, ["LongName"]) +
                extract_items(self.parser.xml, ["Description"])
            ),
            "urls": [],
            "webpages": [],
            "relationships": []
        }
        url_sha = generate_sha_urn(self.url)
        urls.add(url_sha)
        original_url = self._generate_harvest_manifest(**{
            "bcube:hasUrlSource": "Harvested",
            "bcube:hasConfidence": "Good",
            "vcard:hasUrl": self.url,
            "object_id": url_sha
        })
        service['urls'].append(original_url)
        service['relationships'].append({
            "relate": "bcube:originatedFrom",
            "object_id": url_sha
        })

        # output['source'] = extract_items(
        #   self.parser.xml, ["Attribution"])
        # output['contact'] = extract_items(
        #     self.parser.xml, ["Developer"])
        # output['rights'] = extract_items(
        #   self.parser.xml, ["SyndicationRight"])

        key_id = generate_uuid_urn()
        output['keywords'] = [
            {
                "object_id": key_id,
                "bcube:hasValue": extract_items(self.parser.xml, ["Tags"])
            }
        ]
        service['relationships'].append({
            "relate": "dc:conformsTo",
            "object_id": key_id
        })

        for t in extract_elems(self.parser.xml, ['Url']):
            ep = self._parse_endpoint(t)
            url_sha = generate_sha_urn(ep['url'])
            if url_sha not in urls:
                urls.add(url_sha)
                dist = self._generate_harvest_manifest(**{
                    "bcube:hasUrlSource": "Generated",
                    "bcube:hasConfidence": "Not Sure",
                    "vcard:hasUrl": ep['url'],
                    "object_id": url_sha
                })
                service['urls'].append(dist)
                service['webpages'].append({
                    "object_id": generate_uuid_urn(),
                    "relationships": [
                        {
                            "relate": "dcterms:references",
                            "object_id": url_sha
                        }
                    ]
                })

        output['services'] = [service]

        return tidy_dict(output)

    def _parse_endpoint(self, elem):
        endpoint = {}
        endpoint['mimetype'] = elem.attrib.get('type', '')
        endpoint['template'] = elem.attrib.get('template', '')
        endpoint['parameters'] = self._extract_params(elem)
        endpoint['actionable'] = 'NOPE'
        # endpoint['url'] = self._generate_url(
        #   endpoint['mimetype'], endpoint['template'])

        osl = OpenSearchLink(elem)
        endpoint['url'] = osl.url

        return tidy_dict(endpoint)

    def _parse_children(self, dialect):
        ''' i fundamentally do not like this '''
        if dialect == 'ATOM':
            reader = OpenSearchAtomReader(None, self.response, self.url)
        elif dialect == 'RSS':
            reader = OpenSearchRssReader(None, self.response, self.url)
        return reader.parse()

    def _extract_params(self, endpoint):
        def _extract_prefix(param):
            pattern = '\{{0,1}(\S*):([\S][^}]*)'

            # TODO: this is probably a bad assumption (that there's just the
            #   one item in the list, not that urlparse returns the terms as a list)
            if isinstance(param, list):
                param = param[0]

            if ':' not in param:
                return ('', param)

            m = re.search(pattern, param)
            return m.groups()

        _parameter_formats = {
            "geo:box": "west, south, east, north",
            "time:start": "YYYY-MM-DDTHH:mm:ssZ",
            "time:stop": "YYYY-MM-DDTHH:mm:ssZ"
        }
        url = endpoint.get('template', '')
        query_params = parse_url(url)

        # deal with the namespaced parameters as [query param key, prefix, type]
        query_params = [[k] + list(_extract_prefix(v)) for k, v
                        in query_params.iteritems()]

        return [
            tidy_dict({
                "name": qp[0],
                "prefix": qp[1],
                "type": qp[2],
                "format": _parameter_formats.get(':'.join(qp[1:]))
            }) for qp in query_params]


class OpenSearchAtomReader(Processor):
    def parse(self):
        output = {}
        output['items'] = [child for child in self.parse_children(tags=['//*', 'entry'])]
        return tidy_dict(output)

    def _parse_child(self, child):
        entry = {}

        entry['title'] = extract_item(child, ['title'])
        entry['id'] = extract_item(child, ['id'])
        entry['creator'] = extract_item(child, ['creator'])
        entry['author'] = extract_item(child, ['author', 'name'])
        entry['date'] = extract_item(child, ['date'])
        entry['updated'] = extract_item(child, ['updated'])
        entry['published'] = extract_item(child, ['published'])

        entry['subjects'] = [e.attrib.get('term', '') for e in extract_elems(child, ['category'])]

        entry['contents'] = []
        contents = extract_elems(child, ['content'])
        for content in contents:
            text = content.text.strip() if content.text else ''
            content_type = content.attrib.get('type', '')
            entry['contents'].append({'content': text, 'type': content_type})

        entry['links'] = []
        links = extract_elems(child, ['link'])
        for link in links:
            href = link.attrib.get('href', '')
            rel = link.attrib.get('rel', '')
            entry['links'].append({'href': href, 'rel': rel})

        return tidy_dict(entry)


class OpenSearchRssReader(Processor):
    def parse(self):
        output = {}
        output['items'] = [child for child in self.parse_children(tags=['//*', 'item'])]
        return tidy_dict(output)

    def _parse_child(self, child):
        item = {}
        item['title'] = extract_item(child, ['title'])
        item['language'] = extract_item(child, ['language'])
        item['author'] = extract_item(child, ['author'])
        # TODO: go sort out what this is: http://purl.org/rss/1.0/modules/content/
        item['encoded'] = extract_item(child, ['encoded'])
        item['id'] = extract_item(child, ['guid'])
        item['creator'] = extract_item(child, ['creator'])

        item['subjects'] = extract_items(child, ['category'])
        item['published'] = extract_item(child, ['pubDate'])
        item['timestamp'] = extract_item(child, ['date'])

        item['links'] = extract_items(child, ['link'])
        item['links'] += extract_items(child, ['docs'])

        return tidy_dict(item)
