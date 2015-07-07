from semproc.utils import tidy_dict, extract_element_tag
from semproc.xml_utils import extract_item, extract_items
from semproc.xml_utils import extract_elem, extract_elems
from semproc.xml_utils import extract_attrib
from semproc.geo_utils import bbox_to_geom, to_wkt


'''
note that these can be accessed as standalone XML responses
or as some item contained in a results set per CSW or OAI-PMH, etc.

'''


class DcItemReader():
    def __init__(self, elem):
        self.elem = elem

    def parse_item(self):
        '''
        parse just the dc element (like oai_dc:dc) so if you're pulling
        this from an oai-pmh service, etc, make sure that it's *not*
        the full document
        '''
        # TODO: this is not correct for the overall thing
        if self.elem is None:
            return {}

        title = extract_item(self.elem, ['title'])
        creator = extract_item(self.elem, ['creator'])
        subjects = extract_items(self.elem, ['subject'])
        description = extract_item(self.elem, ['description'])
        date = extract_item(self.elem, ['date'])
        language = extract_item(self.elem, ['language'])
        publisher = extract_item(self.elem, ['publisher'])
        sources = extract_items(self.elem, ['source'])
        types = extract_items(self.elem, ['type'])

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


class DifItemReader():
    def __init__(self, elem):
        self.elem = elem

    def parse_item(self, elem):
        identifier = extract_item(self.elem, ['Entry_ID'])
        title = extract_item(self.elem, ['Entry_Title'])
        keywords = extract_items(self.elem, ['Keyword'])
        keywords += extract_items(self.elem, ['ISO_Topic_Category'])
        abstract = extract_item(self.elem, ['Summary'])
        organization = extract_item(self.elem, ['Originating_Center'])

        # temporal extent
        start_date = extract_item(
            self.elem, ['Temporal_Coverage', 'Start_Date'])
        end_date = extract_item(self.elem, ['Temporal_Coverage', 'End_Date'])
        temporal = [start_date, end_date] if start_date and end_date else []

        # spatial extent
        west = extract_item(
            self.elem, ['Spatial_Coverage', 'Westernmost_Longitude'])
        east = extract_item(
            self.elem, ['Spatial_Coverage', 'Easternmost_Longitude'])
        south = extract_item(
            self.elem, ['Spatial_Coverage', 'Southernmost_Latitude'])
        north = extract_item(
            self.elem, ['Spatial_Coverage', 'Northernmost_Latitude'])
        bbox = [west, south, east, north] if \
            west and east and north and south else []
        bbox = bbox_to_geom(bbox)
        bbox = to_wkt(bbox)

        distributions = []
        for related_url in extract_elems(self.elem, ['Related_URL']):
            url = extract_item(related_url, ['URL'])
            content_type = extract_item(
                related_url, ['URL_Content_Type', 'Type'])
            description = extract_item(related_url, ['Description'])
            dist = tidy_dict({
                "url": url,
                "description": description,
                "content_type": content_type
            })
            if dist:
                distributions.append(dist)

        return tidy_dict({
            "id": identifier,
            "title": title,
            "keywords": keywords,
            "abstract": abstract,
            "organization": organization,
            "bbox": bbox,
            "temporal": temporal,
            "distributions": distributions
        })


class FgdcItemReader():
    '''
    spitballing.

    an fgdc metadata record has one dataset entity.
    the dataset entity *may* have an identifier (datsetid).
    '''
    def __init__(self, elem):
        self.elem = elem

    def parse_item(self):
        output = {}
        output['catalog_record'] = {
            "url": "",  # WE DO NOT HAVE THE URL HERE
            "harvestDate": "",  # NOR DO WE HAVE THE DATE
            "conformsTo": extract_attrib(
                self.elem, ['@noNamespaceSchemaLocation'])
        }

        output['dataset'] = {
            "identifier": extract_item(self.elem, ['idinfo', 'datasetid']),
            "abstract": extract_item(
                self.elem, ['idinfo', 'descript', 'abstract']),
            "title": extract_item(
                self.elem, ['idinfo', 'citation', 'citeinfo', 'title'])
        }

        publisher = extract_item(
            self.elem,
            ['idinfo', 'citation', 'citeinfo', 'pubinfo', 'publish'])
        pubplace = extract_item(
            self.elem,
            ['idinfo', 'citation', 'citeinfo', 'pubinfo', 'pubplace'])
        output['publisher'] = {
            "name": publisher,
            "location": pubplace
        }

        bbox_elem = extract_elem(self.elem, ['idinfo', 'spdom', 'bounding'])
        if bbox_elem is not None:
            # that's not even valid
            west = extract_item(bbox_elem, ['westbc'])
            east = extract_item(bbox_elem, ['eastbc'])
            north = extract_item(bbox_elem, ['northbc'])
            south = extract_item(bbox_elem, ['southbc'])
            bbox = [west, south, east, north]
            bbox = bbox_to_geom(bbox)
            bbox = to_wkt(bbox)

            output['dataset'].update({
                "spatial_extent": {
                    "wkt": bbox,
                    "west": west,
                    "east": east,
                    "north": north,
                    "south": south
                }})

        time = {}
        time_elem = extract_elem(self.elem, ['idinfo', 'timeperd', 'timeinfo'])
        if time_elem is not None:
            caldate = extract_item(time_elem, ['sngdate', 'caldate'])
            if caldate:
                # TODO: we should see if it's at least a valid date
                time['startDate'] = caldate

            rngdate = extract_elem(time_elem, ['rngdates'])
            if rngdate is not None:
                time['startDate'] = extract_item(rngdate, ['begdate'])
                time['endDate'] = extract_item(rngdate, ['enddate'])
            # TODO: add the min/max of the list of dates

        output['temporal_extent'] = tidy_dict(time)

        # retain the keyword sets with type, thesaurus name and split
        # the terms as best we can
        keywords = []
        key_elem = extract_elem(self.elem, ['idinfo', 'keywords'])
        for child in key_elem.iterchildren():
            key_type = extract_element_tag(child.tag)
            thesaurus = extract_item(child, ['%skt' % key_type])

            # TODO: split these up
            terms = extract_items(child, ['%skey' % key_type])

            # TODO: add something for a set without a thesaurus name
            keywords.append(
                tidy_dict({
                    "thesaurus": thesaurus,
                    "type": key_type,
                    "terms": terms
                })
            )
        output['keywords'] = keywords

        distrib_elems = extract_elems(
            self.elem, ['distinfo', 'distrib', 'stdorder', 'digform'])
        webpages = []
        for distrib_elem in distrib_elems:
            link = extract_item(
                distrib_elem,
                ['digtopt', 'onlinopt', 'computer', 'networka', 'networkr'])
            format = extract_item(distrib_elem, ['digtinfo', 'formname'])
            dist = tidy_dict({"url": link, "format": format})
            if dist:
                webpages.append(dist)

        onlink_elems = extract_elems(
            self.elem, ['idinfo', 'citation', 'citeinfo', 'onlink'])
        for onlink_elem in onlink_elems:
            dist = tidy_dict({
                "url": onlink_elem.text.strip() if onlink_elem.text else '',
                "type": onlink_elem.attrib.get('type', '')
            })
            if dist:
                webpages.append(dist)

        output['webpages'] = webpages

        return tidy_dict(output)
