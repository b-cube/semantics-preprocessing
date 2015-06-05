from lib.base_preprocessors import BaseReader


def generate_localname_xpath(tags):
    return '/'.join(['*[local-name()="%s"]' % t if t not in ['*', '..', '.', '//*'] else t
                    for t in tags])


class AtomReader(BaseReader):
    '''
    for a feed, parse the atom items
    '''

    def parse_items(self):
        xp = generate_localname_xpath(['//*', 'entry'])
        entry_elems = self.parser.xml.xpath(xp)
        entries = []

        for entry_elem in entry_elems:
            entry = {}

            

            entries.append(entry)

        return entries


class RssReader(BaseReader):
    '''
    '''
    def parse_items(self):
        pass
