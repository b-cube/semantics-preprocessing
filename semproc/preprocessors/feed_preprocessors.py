import sys
from semproc.base_preprocessors import BaseReader
from semproc.xml_utils import extract_item, extract_items, extract_elems
from semproc.utils import tidy_dict


class FeedReader(BaseReader):
    def __init__(self, response, url, dialect=''):
        self._response = response
        self._url = url
        self._load_xml()

        if not dialect:
            self.dialect = 'atom' if [ns for ns in self.parser.namespaces.values()
                                      if 'atom' in ns.lower()] else 'rss'
        else:
            self.dialect = dialect

        item_name = 'AtomItem' if self.dialect == 'atom' else 'RssItem'
        self.item_class = getattr(sys.modules[__name__], item_name)

    def parse_results_set_info(self):
        # so if it includes the opensearch namespace,
        # we can get things like total count and page

        # TODO: convert to numbers
        total = extract_item(self.parser.xml, ['feed', 'totalResults'])
        start_index = extract_item(self.parser.xml, ['feed', 'startIndex'])
        per_page = extract_item(self.parser.xml, ['feed', 'itemsPerPage'])
        return total, start_index, per_page

    def parse(self):
        '''
        key = entry for atom and item for rss
        '''
        key = 'entry' if self.dialect == 'atom' else 'item'
        elems = extract_elems(self.parser.xml, ['//*', key])
        items = [self.item_class(elem).item for elem in elems]

        # TODO: add the root level parsing, ie the difference btwn atom and rss
        title = extract_item(self.parser.xml, ['title'])
        updated = extract_item(self.parser.xml, ['updated'])
        author_name = extract_item(self.parser.xml, ['author', 'name'])

        return {
            "title": title,
            "updated": updated,
            "author": author_name,
            "items": items
        }


class AtomItem():
    '''
    parse the atom item
    '''
    def __init__(self, elem):
        self.item = self._parse_item(elem)

    def _parse_item(self, elem):
        entry = {}

        entry['title'] = extract_item(elem, ['title'])
        entry['id'] = extract_item(elem, ['id'])
        entry['creator'] = extract_item(elem, ['creator'])
        entry['author'] = extract_item(elem, ['author', 'name'])
        entry['date'] = extract_item(elem, ['date'])
        entry['updated'] = extract_item(elem, ['updated'])
        entry['published'] = extract_item(elem, ['published'])

        entry['subjects'] = [e.attrib.get('term', '') for e in extract_elems(elem, ['category'])]

        entry['contents'] = []
        contents = extract_elems(elem, ['content'])
        for content in contents:
            text = content.text.strip() if content.text else ''
            content_type = content.attrib.get('type', '')
            entry['contents'].append({'content': text, 'type': content_type})

        entry['links'] = []
        links = extract_elems(elem, ['link'])
        for link in links:
            href = link.attrib.get('href', '')
            rel = link.attrib.get('rel', '')
            entry['links'].append({'href': href, 'rel': rel})

        return tidy_dict(entry)


class RssItem():
    '''
    '''
    def __init__(self, elem):
        self.item = self._parse_item(elem)

    def _parse_item(self, elem):
        item = {}
        item['title'] = extract_item(elem, ['title'])
        item['language'] = extract_item(elem, ['language'])
        item['author'] = extract_item(elem, ['author'])
        # TODO: go sort out what this is: http://purl.org/rss/1.0/modules/content/
        item['encoded'] = extract_item(elem, ['encoded'])
        item['id'] = extract_item(elem, ['guid'])
        item['creator'] = extract_item(elem, ['creator'])

        item['subjects'] = extract_items(elem, ['category'])
        item['published'] = extract_item(elem, ['pubDate'])
        item['timestamp'] = extract_item(elem, ['date'])

        item['links'] = extract_items(elem, ['link'])
        item['links'] += extract_items(elem, ['docs'])

        return tidy_dict(item)
