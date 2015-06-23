import re
import urlparse
import urllib
from itertools import chain
from semproc.processor import Processor
from semproc.utils import parse_url, tidy_dict
from semproc.xml_utils import extract_elems, extract_items, extract_item


class OpenSearchReader(Processor):
    def __init__(self, identify, response, url, parent_url=''):
        self.response = response
        self.url = url
        self.identify = identify
        self.parent_url = parent_url
        self.description = {}

        self._load_xml()

    def parse(self):
        self.description = {}

        if self.parent_url:
            # TODO: consider making this a sha
            self.description['childOf'] = self.parent_url

        if 'service' in self.identify:
            self.description['service'] = self._parse_service()

        if 'resultset' in self.identify:
            # TODO: get the root stats
            self.description['children'] = self._parse_children(
                self.identify['resultset'].get('dialect', ''))

        self.description = tidy_dict(self.description)

    def _parse_service(self):
        output = {}
        output['title'] = extract_items(self.parser.xml, ["ShortName"])
        output['abstract'] = extract_items(self.parser.xml, ["LongName"]) + \
            extract_items(self.parser.xml, ["Description"])
        output['source'] = extract_items(self.parser.xml, ["Attribution"])
        output['contact'] = extract_items(self.parser.xml, ["Developer"])
        output['rights'] = extract_items(self.parser.xml, ["SyndicationRight"])
        output['subject'] = extract_items(self.parser.xml, ["Tags"])

        output['endpoints'] = [self._parse_endpoint(e) for e
                               in extract_elems(self.parser.xml, ['Url'])]

        return tidy_dict(output)

    def _parse_endpoint(self, elem):
        endpoint = {}
        endpoint['mimetype'] = elem.attrib.get('type', '')
        endpoint['template'] = elem.attrib.get('template', '')
        endpoint['parameters'] = self._extract_params(elem)
        endpoint['actionable'] = 'NOPE'
        endpoint['url'] = self._generate_url(endpoint['mimetype'], endpoint['template'])

        return tidy_dict(endpoint)

    # NOTE: this is duplicated from the link builder because idk
    def _extract_parameter_key(self, value, params):
        # sort out the query parameter name for a parameter
        # and don't send curly bracketed things, please
        return {k: v.split(':')[-1].replace('?', '') for k, v
                in params.iteritems()
                if value in v}

    def _extract_template(self, template_url, append_limit):
        parts = urlparse.urlparse(template_url)
        if not parts.scheme:
            return '', '', {}

        base_url = urlparse.urlunparse((
            parts.scheme,
            parts.netloc,
            parts.path,
            None,
            None,
            None
        ))

        qp = {k: v[0] for k, v in urlparse.parse_qs(parts.query).iteritems()}

        # get the hard-coded params
        defaults = {k: v for k, v in qp.iteritems()
                    if not v.startswith('{')
                    and not v.endswith('}')}

        # get the rest (and ignore the optional/namespaces)
        parameters = {k: v[1:-1] for k, v in qp.iteritems()
                      if v.startswith('{')
                      and v.endswith('}')}

        if append_limit:
            terms = self._extract_parameter_key('count', parameters)
            if terms:
                defaults = dict(
                    chain(defaults.items(), {k: 5 for k in terms.keys()}.items())
                )

        # note: not everyone manages url-encoded query parameter delimiters
        #       and not everyone manages non-url-encoded values so yeah. we are
        #       ignoring the non-url-encoded group.
        return base_url, defaults, parameters

    def _generate_url(self, mimetype, template):
        url_base, defaults, params = self._extract_template(template, None)
        if not url_base:
            return ''

        search_terms = self._extract_parameter_key('searchTerms', params)
        if search_terms:
            qps = dict(
                chain(
                    defaults.items(),
                    {search_terms.keys()[0]: ''}.items()
                )
            )
        else:
            qps = {}

        return url_base + '?' + urllib.urlencode(qps.items())

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
