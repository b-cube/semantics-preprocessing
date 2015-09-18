from semproc.utils import tidy_dict, extract_element_tag
from semproc.xml_utils import extract_item, extract_items
from semproc.xml_utils import extract_elem, extract_elems
from semproc.xml_utils import extract_attrib
from semproc.geo_utils import bbox_to_geom, to_wkt
from semproc.utils import generate_sha_urn, generate_uuid_urn
from rdflib.namespace import DC, DCTERMS, FOAF, XSD, OWL
from datetime import datetime


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


class BaseItemReader():
    _technical_debt = {
        'bcube': 'http://purl.org/BCube/#',
        'vcard': 'http://www.w3.org/TR/vcard-rdf/#',
        'esip': 'http://purl.org/esip/#',
        'vivo': 'http://vivo.ufl.edu/ontology/vivo-ufl/#',
        'bibo': 'http://purl.org/ontology/bibo/#',
        'dcat': 'http://www.w3.org/TR/vocab-dcat/#',
        "prov": "http://purl.org/net/provenance/ns#",
        'dc': str(DC),
        'dct': str(DCTERMS),
        'foaf': str(FOAF),
        'xsd': str(XSD),
        'owl': str(OWL)
    }

    def __init__(self, elem, url, harvest_date):
        self.elem = elem
        self.url = url
        self.harvest_date = harvest_date

    def parse_item(self):
        pass


class FgdcItemReader(BaseItemReader):
    '''
    spitballing.

    an fgdc metadata record has one dataset entity.
    the dataset entity *may* have an identifier (datsetid).

    TODO: probably not a lot of this across the suite of parsers
    '''
    def _convert_date(self, datestr):
        # convert the 4-8 char to an iso date and deal with unknowns
        if datestr.lower() in ['unknown', 'none']:
            return ''

        year = datestr[:4]
        month = datestr[4:6] if len(datestr) > 4 else '1'
        day = datestr[6:] if len(datestr) > 6 else '1'
        try:
            d = datetime(int(year), int(month), int(day))
            return d.isoformat()
        except:
            return ''

    # TODO: this is possibly the worst plan of the day
    def parse(self):
        return self.parse_item()

    def parse_item(self):
        output = {}

        catalog_object_id = generate_sha_urn(self.url)

        output['catalog_record'] = {
            "object_id": catalog_object_id,
            "url": self.url,
            "harvestDate": self.harvest_date,
            "conformsTo": extract_attrib(
                self.elem, ['@noNamespaceSchemaLocation']).split()
        }

        datsetid = extract_item(self.elem, ['idinfo', 'datsetid'])
        dataset_object_id = generate_sha_urn(datsetid) if datsetid \
            else generate_uuid_urn()

        dataset = {
            "object_id": dataset_object_id,
            "identifier": datsetid,
            "abstract": extract_item(
                self.elem, ['idinfo', 'descript', 'abstract']),
            "title": extract_item(
                self.elem, ['idinfo', 'citation', 'citeinfo', 'title'])
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

            dataset.update({
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
                time['startDate'] = self._convert_date(caldate)

            rngdate = extract_elem(time_elem, ['rngdates'])
            if rngdate is not None:
                time['startDate'] = self._convert_date(
                    extract_item(rngdate, ['begdate']))
                time['endDate'] = self._convert_date(
                    extract_item(rngdate, ['enddate']))
            # TODO: add the min/max of the list of dates

        dataset['temporal_extent'] = tidy_dict(time)

        dataset['relationships'] = [
            {
                "relate": "description",
                "object_id": catalog_object_id
            }
        ]

        publisher = {
            "object_id": generate_uuid_urn(),
            "name": extract_item(
                self.elem,
                ['idinfo', 'citation', 'citeinfo', 'pubinfo', 'publish']),
            "location": extract_item(
                self.elem,
                ['idinfo', 'citation', 'citeinfo', 'pubinfo', 'pubplace'])
        }
        output['publisher'] = publisher
        dataset['relationships'].append({
            "relate": "publisher",
            "object_id": publisher['object_id']
        })

        # TODO: is the distribution bit working? not in the example
        distrib_elems = extract_elems(
            self.elem, ['distinfo', 'distrib', 'stdorder', 'digform'])
        webpages = []
        for distrib_elem in distrib_elems:
            link = extract_item(
                distrib_elem,
                ['digtopt', 'onlinopt', 'computer', 'networka', 'networkr'])
            format = extract_item(distrib_elem, ['digtinfo', 'formname'])
            dist = tidy_dict(
                {
                    "object_id": generate_sha_urn(link),
                    "url": link,
                    "format": format
                }
            )
            if dist:
                webpages.append(dist)

        onlink_elems = extract_elems(
            self.elem, ['idinfo', 'citation', 'citeinfo', 'onlink'])
        for onlink_elem in onlink_elems:
            link = onlink_elem.text.strip() if onlink_elem.text else ''
            if not link:
                continue
            dist = tidy_dict({
                "object_id": generate_sha_urn(link),
                "url": link,
                "type": onlink_elem.attrib.get('type', '')
            })
            if dist:
                webpages.append(dist)

        output['webpages'] = webpages
        for webpage in webpages:
            dataset['relationships'].append({
                "relate": "relation",
                "object_id": webpage['object_id']
            })

        # retain the keyword sets with type, thesaurus name and split
        # the terms as best we can
        keywords = []
        key_elem = extract_elem(self.elem, ['idinfo', 'keywords'])
        for child in key_elem.iterchildren():
            key_type = extract_element_tag(child.tag)
            key_tag = 'strat' if key_type == 'stratum' else key_type
            key_tag = 'temp' if key_tag == 'temporal' else key_tag
            thesaurus = extract_item(child, ['%skt' % key_tag])

            # TODO: split these up
            terms = extract_items(child, ['%skey' % key_tag])

            if terms:
                # if there's a parsing error (bad cdata, etc) may not have
                # TODO: add something for a set without a thesaurus name
                keywords.append(
                    tidy_dict({
                        "object_id": generate_uuid_urn(),
                        "thesaurus": thesaurus,
                        "type": key_type,
                        "terms": terms
                    })
                )
        output['keywords'] = keywords
        for keyword in keywords:
            dataset['relationships'].append(
                {
                    "relate": "conformsTo",
                    "object_id": keyword['object_id']
                }
            )

        output['datasets'] = [dataset]

        # add the metadata relate
        output['catalog_record']['relationships'] = [
            {
                "relate": "primaryTopic",
                "object_id": dataset_object_id
            }
        ]

        return tidy_dict(output)
