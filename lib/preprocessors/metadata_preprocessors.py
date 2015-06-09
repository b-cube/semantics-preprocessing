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
    def parse_item(self, elem):
        identifier = extract_item(elem, ['Entry_ID'])
        title = extract_item(elem, ['Entry_Title'])
        keywords = extract_items(elem, ['Keyword'])
        keywords += extract_items(elem, ['ISO_Topic_Category'])
        abstract = extract_item(elem, ['Summary'])
        organization = extract_item(elem, ['Originating_Center'])

        # temporal extent
        start_date = extract_item(elem, ['Temporal_Coverage', 'Start_Date'])
        end_date = extract_item(elem, ['Temporal_Coverage', 'End_Date'])

        # spatial extent
        west = extract_item(elem, ['SpatialCoverage', 'Westernmost_Longitude'])
        east = extract_item(elem, ['SpatialCoverage', 'Easternmost_Longitude'])
        south = extract_item(elem, ['SpatialCoverage', 'Southernmost_Latitude'])
        north = extract_item(elem, ['SpatialCoverage', 'Northernmost_Latitude'])

        distributions = []
        for related_url in extract_elems(elem, ['Related_URL']):
            url = extract_item(related_url, ['URL'])
            content_type = extract_item(related_url, ['URL_Content_Type', 'Type'])
            description = extract_item(related_url, ['Description'])
            distributions.append(tidy_dict({
                "url": url,
                "description": description,
                "content_type": content_type
            }))

        return tidy_dict({
            "id": identifier,
            "title": title,
            "keywords": keywords,
            "abstract": abstract,
            "organization": organization,
            "bbox": [west, south, east, north],
            "temporal": [start_date, end_date],
            "distributions": distributions
        })


class FgdcReader(BaseReader):
    def parse_item(self):
        # ha. hahahaha. let us now make this even more ridiculous.
        # you are welcome
        elem = self.parser.xml

        identifier = extract_item(elem, ['idinfo', 'datasetid'])

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

        onlink_elems = extract_elems(elem, ['idinfo', 'citation', 'citeinfo', 'onlink'])
        for onlink_elem in onlink_elems:
            distributions.append(tidy_dict({
                "url": onlink_elem.text.strip(),
                "type": onlink_elem.attrib.get('type', '')
            }))

        return tidy_dict({
            "id": identifier,
            "title": title,
            "abstract": abstract,
            "purpose": purpose,
            "subjects": keywords,
            "date": time,
            "bbox": bbox,
            "distributions": distributions
        })
