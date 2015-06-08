from lib.base_preprocessors import BaseReader
from lib.utils import tidy_dict
from lib.xml_utils import extract_item, extract_items


'''
note that these can be accessed as standalone XML responses
or as some item contained in a results set per CSW or OAI-PMH, etc.

'''


class DcReader(BaseReader):
    def parse_item(self, elem):
        '''
        parse just the dc element (like oai_dc:dc) so if you're pulling
        this from an oai-pmh service, etc, make sure that it's *not*
        the full document
        '''
        # TODO: this is not correct for the overall thing
        if elem is None:
            return {}

        title = extract_item(elem, ['title'])
        creator = extract_item(elem, ['creator'])
        subjects = extract_items(elem, ['subject'])
        description = extract_item(elem, ['description'])
        date = extract_item(elem, ['date'])
        language = extract_item(elem, ['language'])
        publisher = extract_item(elem, ['publisher'])
        sources = extract_items(elem, ['source'])
        types = extract_items(elem, ['type'])

        return tidy_dict({
            'title': title,
            'creator': creator,
            'subjects': subjects,
            'abstract': description,
            'language': language,
            'date': date,
            'publisher': publisher,
            'types': types,
            'sources': sources
        })


class DifReader(BaseReader):
    pass


class FgdcReader(BaseReader):
    def parse(self):
        pass
