from semproc.utils import tidy_dict, extract_element_tag
from semproc.xml_utils import extract_item, extract_items
from semproc.xml_utils import extract_elem, extract_elems
from semproc.xml_utils import extract_attrib
from semproc.geo_utils import bbox_to_geom, to_wkt
from semproc.utils import generate_sha_urn, generate_uuid_urn
from datetime import datetime
# leaving this here for potential use in the json keys
# from semproc.ontology import _ontology_uris
# from rdflib.namespace import DC, DCTERMS, FOAF, XSD, OWL


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
    def __init__(self, elem, url, harvest_details):
        self.elem = elem
        self.url = url
        self.harvest_details = harvest_details

    def parse_item(self):
        pass

    def _generate_harvest_manifest(self, **kwargs):
        harvest = {
            "vcard:hasUrl": self.url,
            "bcube:atTime": self.harvest_details.get('harvest_date'),
            "bcube:HTTPStatusCodeValue": 200,
            "bcube:reasonPhrase": "OK",
            "bcube:HTTPStatusFamilyCode": 200,
            "bcube:HTTPStatusFamilyType": "Success message",
            "bcube:hasUrlSource": "",
            "bcube:hasConfidence": "",
            "bcube:validatedOn": self.harvest_details.get('harvest_date')
        }
        harvest.update(kwargs)
        return tidy_dict(harvest)


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
        self.parse_item()

    def parse_item(self):
        output = {}

        catalog_object_id = generate_sha_urn(self.url)

        output['catalog_record'] = {
            "object_id": catalog_object_id,
            "bcube:dateCreated": self.harvest_details.get('harvest_date', ''),
            "bcube:lastUpdated": self.harvest_details.get('harvest_date', ''),
            "dc:conformsTo": extract_attrib(
                self.elem, ['@noNamespaceSchemaLocation']).split(),
            "rdf:type": "FGDC:CSDGM",
            "relationships": [],
            "urls": []
        }

        # add the harvest info
        original_url = self._generate_harvest_manifest(**{
            "bcube:hasUrlSource": "Harvested",
            "bcube:hasConfidence": "Good",
            "vcard:hasUrl": self.url,
            "object_id": generate_uuid_urn()
        })
        # NOTE: this is not the sha from the url
        output['catalog_record']['urls'].append(original_url)
        output['catalog_record']['relationships'].append(
            {
                "relate": "bcube:originatedFrom",
                "object_id": original_url['object_id']
            }
        )

        datsetid = extract_item(self.elem, ['idinfo', 'datsetid'])
        dataset_object_id = generate_sha_urn(datsetid) if datsetid \
            else generate_uuid_urn()

        dataset = {
            "object_id": dataset_object_id,
            "dcterms:identifier": datsetid,
            "bcube:dateCreated": self.harvest_details.get('harvest_date', ''),
            "bcube:lastUpdated": self.harvest_details.get('harvest_date', ''),
            "dc:description": extract_item(
                self.elem, ['idinfo', 'descript', 'abstract']),
            "dcterms:title": extract_item(
                self.elem, ['idinfo', 'citation', 'citeinfo', 'title']),
            "urls": []
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
                "dc:spatial": bbox,
                "esip:westBound": west,
                "esip:eastBound": east,
                "esip:northBound": north,
                "esip:southBound": south
            })

        time = {}
        time_elem = extract_elem(self.elem, ['idinfo', 'timeperd', 'timeinfo'])
        if time_elem is not None:
            caldate = extract_item(time_elem, ['sngdate', 'caldate'])
            if caldate:
                # TODO: we should see if it's at least a valid date
                dataset['esip:startDate'] = self._convert_date(caldate)

            rngdate = extract_elem(time_elem, ['rngdates'])
            if rngdate is not None:
                dataset['esip:startDate'] = self._convert_date(
                    extract_item(rngdate, ['begdate']))
                dataset['esip:endDate'] = self._convert_date(
                    extract_item(rngdate, ['enddate']))
            # TODO: add the min/max of the list of dates

        dataset['relationships'] = [
            {
                "relate": "bcube:hasMetadataRecord",
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
            "relate": "dcterms:publisher",
            "object_id": publisher['object_id']
        })

        distrib_elems = extract_elems(
            self.elem, ['distinfo', 'stdorder', 'digform'])

        for distrib_elem in distrib_elems:
            link = extract_item(
                distrib_elem,
                ['digtopt', 'onlinopt', 'computer', 'networka', 'networkr'])
            # format = extract_item(distrib_elem, ['digtinfo', 'formname'])
            dist = self._generate_harvest_manifest(**{
                "bcube:hasUrlSource": "Harvested",
                "bcube:hasConfidence": "Good",
                "vcard:hasUrl": link,
                "object_id": generate_sha_urn(link)
            })
            if dist:
                dataset['urls'].append(dist)
                dataset['relationships'].append(
                    {
                        "relate": "dcterms:references",
                        "object_id": dist['object_id']
                    }
                )

        webpages = []
        onlink_elems = extract_elems(
            self.elem, ['idinfo', 'citation', 'citeinfo', 'onlink'])
        for onlink_elem in onlink_elems:
            link = onlink_elem.text.strip() if onlink_elem.text else ''
            if not link:
                continue
            dist = self._generate_harvest_manifest(**{
                "bcube:hasUrlSource": "Harvested",
                "bcube:hasConfidence": "Good",
                "vcard:hasUrl": link,
                "object_id": generate_sha_urn(link)
            })
            if dist:
                output['catalog_record']['urls'].append(dist)
                webpages.append({
                    "object_id": generate_uuid_urn(),
                    "relationships": [
                        {
                            "relate": "dcterms:references",
                            "object_id": dist['object_id']
                        }
                    ]
                })

        output['webpages'] = webpages
        for webpage in webpages:
            dataset['relationships'].append({
                "relate": "dcterms:references",
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
                        "dc:partOf": thesaurus,
                        "bcube:hasType": key_type,
                        "bcube:hasValue": terms
                    })
                )
        output['keywords'] = keywords
        for keyword in keywords:
            dataset['relationships'].append(
                {
                    "relate": "dc:conformsTo",
                    "object_id": keyword['object_id']
                }
            )

        output['datasets'] = [dataset]

        # add the metadata relate
        output['catalog_record']['relationships'].append(
            {
                "relate": "foaf:primaryTopic",
                "object_id": dataset_object_id
            }
        )

        self.description = tidy_dict(output)
