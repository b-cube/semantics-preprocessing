from lib.base_preprocessors import BaseReader
from lib.xml_utils import extract_item, extract_items, generate_localname_xpath
from lib.utils import tidy_dict


class AtomReader(BaseReader):
    '''
    for a feed, parse the atom items
    '''

    def _item(self):
        xp = generate_localname_xpath(['//*', 'entry'])
        return self.parser.xml.xpath(xp)

    def parse_item(self, elem):
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


class RssReader(BaseReader):
    '''
    '''
    def parse_item(self, elem):
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
