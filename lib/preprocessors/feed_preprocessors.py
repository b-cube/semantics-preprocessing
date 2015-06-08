import sys
from lib.base_preprocessors import BaseReader
from lib.xml_utils import extract_item, extract_items, generate_localname_xpath
from lib.utils import tidy_dict


class FeedReader():
    def __init__(self, dialect=''):
        # TODO: add the actual xml parsing (ha)
        self.parser = None

        # let's assume today that we have parsed things
        namespace = 'atom' if [ns for ns in self.parser.namespaces
                               if 'atom' in ns.lower()] else 'rss'
        self.dialect = dialect if dialect else namespace

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
        xp = generate_localname_xpath(['//*', key])
        elems = self.parser.xml.xpath(xp)
        items = [self.item_class(elem) for elem in elems]

        # TODO: add the root level parsing
        title = extract_item(self.parser.xml, ['feed', 'title'])
        updated = extract_item(self.parser.xml, ['feed', 'updated'])
        author_name = extract_item(self.parser.xml, ['feed', 'author', 'name'])

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
        return self._parse_item(elem)

    def _parse_item(self, elem):
        entry = {}

        entry['title'] = extract_item(elem, ['title'])
        entry['id'] = extract_item(elem, ['id'])
        entry['creator'] = extract_item(elem, ['creator'])
        entry['author'] = extract_item(elem, ['author', 'name'])
        entry['date'] = extract_item(elem, ['date'])
        entry['updated'] = extract_item(elem, ['updated'])
        entry['published'] = extract_item(elem, ['published'])

        entry['contents'] = []
        xp = generate_localname_xpath(['content'])
        contents = elem.xpath(xp)
        for content in contents:
            text = content.text.strip() if content.text else ''
            content_type = content.attrib.get('type', '')
            entry['contents'].append({'content': text, 'type': content_type})

        entry['links'] = []
        xp = generate_localname_xpath(['link'])
        links = elem.xpath(xp)
        for link in links:
            href = link.attrib.get('href', '')
            rel = link.attrib.get('rel', '')
            entry['links'].append({'href': href, 'rel': rel})

        return tidy_dict(entry)


class RssItem():
    '''
    '''
    def __init__(self, elem):
        return self._parse_item(elem)

    def _parse_item(self, elem):
        item = {}
        item['title'] = extract_item(elem, ['title'])
        item['language'] = extract_item(elem, ['language'])
        item['author'] = extract_item(elem, ['author'])

        item['subjects'] = extract_items(elem, ['category'])
        item['published'] = extract_item(elem, ['pubDate'])

        xp = generate_localname_xpath(['link'])
        item['links'] = [e.text.strip() for e in elem.xpath(xp)]
        xp = generate_localname_xpath(['docs'])
        item['links'] += [e.text.strip() for e in elem.xpath(xp)]

        return tidy_dict(item)
