from lib.base_preprocessors import BaseReader
from lib.utils import tidy_dict
from lib.xml_utils import extract_item, extract_items, extract_elem, extract_elems


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
        # ha. hahahaha. let us now make this even more ridiculous.
        # you are welcome
        elem = self.parser.xml

        abstract = extract_item(elem, ['idinfo', 'descript', 'abstract'])
        purpose = extract_item(elem, ['idinfo', 'descript', 'purpose'])
        title = extract_item(elem, ['idinfo', 'citation', 'citeinfo', 'title'])
        bbox_elem = extract_elem(elem, ['idinfo', 'descript', 'spdom', 'bounding'])

        west = extract_item(bbox_elem, ['westbc'])
        east = extract_item(bbox_elem, ['eastbc'])
        north = extract_item(bbox_elem, ['northbc'])
        south = extract_item(bbox_elem, ['southbc'])
        bbox = [west, south, east, north]

        time_elem = extract_elem(elem, ['idinfo', 'descript', 'timeperd', 'timeinfo'])
        caldate = extract_item(time_elem, ['sngdate', 'caldate'])
        if not caldate:
            pass

        # TODO: finish this for ranges and note ranges and what do we want in the ontology
        time = {}

        keywords = extract_items(elem, ['idinfo', 'descript', 'keywords', 'theme', 'themekey'])
        keywords += extract_items(elem, ['idinfo', 'descript', 'keywords', 'place', 'placekey'])

        distrib_elems = extract_elems(elem, ['distinfo', 'distrib', 'stdorder', 'digform'])
        distributions = []
        for distrib_elem in distrib_elems:
            link = extract_item(
                distrib_elem,
                ['digtopt', 'onlinopt', 'computer', 'networka', 'networkr'])
            format = extract_item(distrib_elem, ['digtinfo', 'formname'])
            distributions.append(tidy_dict({"url": link, "format": format}))

        return tidy_dict({
            "title": title,
            "abstract": abstract,
            "purpose": purpose,
            "subjects": keywords,
            "date": time,
            "bbox": bbox,
            "distributions": distributions
        })
