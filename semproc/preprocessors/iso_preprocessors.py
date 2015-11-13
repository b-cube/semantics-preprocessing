from semproc.parser import Parser
from semproc.utils import tidy_dict
from semproc.xml_utils import extract_item, extract_items
from semproc.xml_utils import generate_localname_xpath
from semproc.xml_utils import extract_elem, extract_elems, extract_attrib
from semproc.geo_utils import bbox_to_geom, gml_to_geom, reproject, to_wkt
from semproc.utils import generate_sha_urn, generate_uuid_urn
from itertools import chain
import dateutil.parser as dateparser
# leaving this here for potential use in the json keys
# from semproc.ontology import _ontology_uris
# from rdflib.namespace import DC, DCTERMS, FOAF, XSD, OWL


'''
NOTE: for all of the ISO parsers, I am using the local-path "trick".
      It is a known performance hit but the harmonization across -1,
      -2, -3, INSPIRE, data.gov, whatever, is a not insignificant chunk
      of dev time as well. I am willing to make this tradeoff given
      the ETL workflow.
'''


class IsoReader():
    '''
    this assumes we're reading from a response as the root
    and will iterate over whatever that flavor of iso is:
        data series with some mx (with some sv)
        service identification
        mi/md
    '''
    def __init__(self, identity, text, url, harvest_details):
        self.text = text
        self.identity = identity
        self.url = url
        self.harvest_details = harvest_details

        # parse
        self.parser = Parser(text)
        self.parse()

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

    def _version_to_urn(self):
        metadata_name = self.identity.get('metadata', {}).get('name')
        if metadata_name == '19115':
            return 'ISO 19115:2003/19139'
        return 'NaN'

    def parse(self):
        '''
        run the routing
        '''

        if not self.identity:
            # we're going to have to sort it out
            self.identity = {}

        metadata = self.identity.get('metadata', {})
        if not metadata:
            return {}

        metadata_type = metadata.get('name', '')
        if not metadata_type:
            return {}

        # TODO: this is unlikely to be correct, given the ds record
        #       but we're not going there just yet
        # TODO: deal with conformsTo (multiple schemaLocations, etc)
        catalog_record = {
            "object_id": generate_sha_urn(self.url),
            "rdf:type": self._version_to_urn(),
            "bcube:dateCreated": self.harvest_details.get('harvest_date', ''),
            "bcube:lastUpdated": self.harvest_details.get('harvest_date', ''),
            "dc:conformsTo": extract_attrib(self.parser.xml, ['@schemaLocation']).split(),
            "relationships": [],
            "urls": []
        }
        catalog_record['urls'].append(
            self._generate_harvest_manifest(**{
                "bcube:hasUrlSource": "Harvested",
                "bcube:hasConfidence": "Good",
                "vcard:hasUrl": self.url,
                "object_id": generate_uuid_urn()
            })
        )

        if metadata_type == 'Data Series':
            # run the set
            self.reader = DsParser(self.parser.xml, catalog_record)
        elif metadata_type == '19119':
            # run that
            for srv in extract_elems(
                self.parser.xml,
                    ['identificationInfo', 'SV_ServiceIdentification']):
                reader = SrvParser(srv, catalog_record)
                reader.parse()
        elif metadata_type == '19115':
            # it's a mi/md so run that
            self.reader = MxParser(
                self.parser.xml,
                catalog_record,
                self.harvest_details
            )
            self.reader.parse()

        # self.reader.parse()
        # # pass it back up the chain a bit
        self.description = self.reader.output


class IsoParser(object):
    def __init__(self, elem, catalog_record, harvest_details):
        pass

    def _generate_harvest_manifest(self, **kwargs):
        harvest = {
            "vcard:hasUrl": "",
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

    # helper methods
    def _parse_identification_info(self, elem):
        # ignoring the larger get all the identifiers above
        # in favor of, hopefully, getting a better dataset id
        dataset_identifier = extract_item(elem, [
            'citation',
            'CI_Citation',
            'identifier',
            'MD_Identifier',
            'code',
            'CharacterString'
        ])

        dataset = {
            "object_id": generate_sha_urn(dataset_identifier)
                if dataset_identifier else generate_uuid_urn(),
            "dc:identifier": dataset_identifier,
            "dc:description": extract_item(elem, ['abstract', 'CharacterString']),
            "dcterms:title": extract_item(elem, [
                'citation', 'CI_Citation', 'title', 'CharacterString']),
            "relationships": []
        }

        # TODO: i think the rights blob is not in the ontology prototypes
        # the rights information from MD_Constraints or MD_LegalConstraints
        # rights = extract_item(elem, ['resourceConstraints', '*', 'useLimitation', 'CharacterString'])

        # deal with the extent
        extents = self._parse_extent(elem)
        dataset.update(extents)

        keywords = self._parse_keywords(elem)
        for keyword in keywords:
            dataset['relationships'].append({
                "relate": "dc:conformsTo",
                "object_id": keyword['object_id']
            })
        return tidy_dict(dataset), keywords

    def _parse_keywords(self, elem):
        '''
        for each descriptiveKeywords block
        in an identification block
        '''
        keywords = []

        for key_elem in extract_elems(elem, ['descriptiveKeywords']):
            # TODO: split these up (if *-delimited in some way)
            terms = extract_items(
                key_elem,
                ['MD_Keywords', 'keyword', 'CharacterString'])
            key_type = extract_attrib(
                key_elem,
                ['MD_Keywords', 'type', 'MD_KeywordTypeCode', '@codeListValue']
            )
            thesaurus = extract_item(
                key_elem,
                [
                    'MD_Keywords',
                    'thesaurusName',
                    'CI_Citation',
                    'title',
                    'CharacterString'
                ]
            )

            if terms:
                keywords.append(
                    tidy_dict({
                        "object_id": generate_uuid_urn(),
                        "dc:partOf": thesaurus,
                        "bcube:hasType": key_type,
                        "bcube:hasValue": terms
                    })
                )

        # TODO: add the Anchor element handling
        #       ['descriptiveKeywords', 'MD_Keywords', 'keyword', 'Anchor']

        # add a generic set for the iso topic category
        isotopics = extract_items(
            elem, ['topicCategory', 'MD_TopicCategoryCode'])
        if isotopics:
            keywords.append(
                tidy_dict({
                    "object_id": generate_uuid_urn(),
                    "dc:partOf": 'IsoTopicCategories',
                    "bcube:hasValue": isotopics
                })
            )

        return keywords

    def _parse_extent(self, elem):
        '''
        handle the spatial and/or temporal extent
        starting from the *:extent element
        '''
        extents = {}
        geo_elem = extract_elem(
            elem, ['extent', 'EX_Extent', 'geographicElement'])
        if geo_elem is not None:
            # we need to sort out what kind of thing it
            # is bbox, polygon, list of points
            bbox_elem = extract_elem(geo_elem, ['EX_GeographicBoundingBox'])
            if bbox_elem is not None:
                extents.update(self._handle_bbox(bbox_elem))

            # NOTE: this will obv overwrite the above
            poly_elem = extract_elem(geo_elem, ['EX_BoundingPolygon'])
            if poly_elem is not None:
                extents.update(self._handle_polygon(poly_elem))

        time_elem = extract_elem(
            elem,
            [
                'extent',
                'EX_Extent',
                'temporalElement',
                'EX_TemporalExtent',
                'extent',
                'TimePeriod'
            ]
        )
        if time_elem is not None:
            begin_position = extract_elem(time_elem, ['beginPosition'])
            end_position = extract_elem(time_elem, ['endPosition'])

            if begin_position is not None and 'indeterminatePosition' not in begin_position.attrib:
                begin_position = self._parse_timestamp(begin_position.text)
            if end_position is not None and 'indeterminatePosition' not in end_position.attrib:
                end_position = self._parse_timestamp(end_position.text)

            extents.update({
                "esip:startDate": begin_position.isoformat(),
                "esip:endDate": end_position.isoformat()
            })

        return extents

    def _handle_bbox(self, elem):
        west = extract_item(elem, ['westBoundLongitude', 'Decimal'])
        west = float(west) if west else 0

        east = extract_item(elem, ['eastBoundLongitude', 'Decimal'])
        east = float(east) if east else 0

        south = extract_item(elem, ['southBoundLatitude', 'Decimal'])
        south = float(south) if south else 0

        north = extract_item(elem, ['northBoundLatitude', 'Decimal'])
        north = float(north) if north else 0

        bbox = [west, south, east, north] \
            if east and west and north and south else []

        geom = bbox_to_geom(bbox)
        return {
            "dc:spatial": to_wkt(geom),
            "esip:westBound": west,
            "esip:eastBound": east,
            "esip:southBound": south,
            "esip:northBound": north
        }

    def _handle_polygon(self, polygon_elem):
        elem = extract_elem(polygon_elem, ['polygon', 'Polygon'])
        srs_name = elem.attrib.get('srsName', 'EPSG:4326')

        geom = gml_to_geom(elem)
        if srs_name != '':
            geom = reproject(geom, srs_name, 'EPSG:4326')

        # TODO: generate the envelope?
        return {"dc:spatial": to_wkt(geom)}

    def _handle_points(self, point_elem):
        # this may not exist in the -2?
        pass

    def _parse_timestamp(self, text):
        '''
        generic handler for any iso date/datetime/time/whatever element
        '''
        try:
            # TODO: deal with timezones if this doesn't
            return dateparser.parse(text)
        except ValueError:
            return None

    def _parse_distribution(self, elem):
        ''' from the distributionInfo element '''
        webpages = []

        for dist_elem in extract_elems(elem, ['MD_Distribution']):
            # this is going to get ugly.
            # super ugly
            # get the transferoptions block
            # get the url, the name, the description, the size
            # get the format from a parent node
            # but where the transferoptions can be in some nested
            # distributor thing or at the root of the element (NOT
            # the root of the file)
            transfer_elems = extract_elems(
                dist_elem, ['//*', 'MD_DigitalTransferOptions'])
            for transfer_elem in transfer_elems:
                # _transfer = {}
                # transfer['url'] = extract_item(
                #     transfer_elem,
                #     ['onLine', 'CI_OnlineResource', 'linkage', 'URL'])
                # transfer['objectid'] = generate_sha_urn(transfer['url'])

                # xp = generate_localname_xpath(
                #     ['..', '..', 'distributorFormat', 'MD_Format'])
                # format_elem = next(iter(transfer_elem.xpath(xp)), None)
                # if format_elem is not None:
                #     transfer['format'] = ' '.join([
                #         extract_item(format_elem,
                #                      ['name', 'CharacterString']),
                #         extract_item(
                #             format_elem, ['version', 'CharacterString'])])

                # NOTE: it's a uuid identifier given that the urls might be
                #       repeated in a record
                dist = self._generate_harvest_manifest(**{
                    "bcube:hasUrlSource": "Harvested",
                    "bcube:hasConfidence": "Good",
                    "vcard:hasUrl": extract_item(
                        transfer_elem,
                        ['onLine', 'CI_OnlineResource', 'linkage', 'URL']),
                    "object_id": generate_uuid_urn()
                })

                webpages.append(dist)

        return webpages

    def _parse_contact(self, elem):
        '''
        parse any CI_Contact
        '''
        contact = {}

        if elem is None:
            return contact

        contact['phone'] = extract_item(
            elem, ['phone', 'CI_Telephone', 'voice', 'CharacterString'])
        contact['addresses'] = extract_items(
            elem, ['address', 'CI_Address', 'deliveryPoint', 'CharacterString'])
        contact['city'] = extract_item(
            elem, ['address', 'CI_Address', 'city', 'CharacterString'])
        contact['state'] = extract_item(
            elem, ['address', 'CI_Address', 'administrativeArea', 'CharacterString'])
        contact['postal'] = extract_item(
            elem, ['address', 'CI_Address', 'postalCode', 'CharacterString'])
        contact['country'] = extract_item(
            elem, ['address', 'CI_Address', 'country', 'CharacterString'])
        contact['email'] = extract_item(
            elem, ['address', 'CI_Address', 'electronicMailAddress', 'CharacterString'])
        return tidy_dict(contact)

    def _parse_responsibleparty(self, elem):
        '''
        parse any CI_ResponsibleParty
        '''
        individual_name = extract_item(
            elem, ['individualName', 'CharacterString'])
        organization_name = extract_item(
            elem, ['organisationName', 'CharacterString'])
        position_name = extract_item(
            elem, ['positionName', 'CharacterString'])

        e = extract_elem(elem, ['contactInfo', 'CI_Contact'])
        contact = self._parse_contact(e)

        return tidy_dict({
            "individual": individual_name,
            "organization": organization_name,
            "position": position_name,
            "contact": contact
        })
    # end helpers


class MxParser(IsoParser):
    '''
    parse an mi or md element (as whole record or some csw/oai-pmh/ds child)
    '''

    def __init__(self, elem, catalog_record, harvest_details):
        ''' starting at Mx_Metadata
        which can be within a DS composedOf block, within a
        CSW result set, as the series descriptor for a dataseries
        or part of some other catalog service
        '''
        self.elem = elem
        self.output = {
            "catalog_record": catalog_record,
            "datasets": [],
            "keywords": [],
            "publishers": [],
            "webpages": []
        }
        self.harvest_details = harvest_details

    def parse(self):
        '''
        from the root node, parse:
            identification (title, abstract, point of contact, keywords,
            extent) if identificationInfo contains SV_ServiceIdentification,
            add as child distribution info
        '''
        for id_elem in extract_elems(self.elem, ['//*', 'identificationInfo', 'MD_DataIdentification']):
            dataset, keywords = self._parse_identification_info(id_elem)
            dataset['relationships'].append({
                "relate": "bcube:hasMetadataRecord",
                "object_id": self.output['catalog_record']['object_id']
            })
            dataset.update({
                "bcube:dateCreated": self.harvest_details.get('harvest_date', ''),
                "bcube:lastUpdated": self.harvest_details.get('harvest_date', '')
            })
            self.output['catalog_record']['relationships'].append({
                "relate": "foaf:primaryTopic",
                "object_id": dataset['object_id']
            })

            # point of contact from the root node and this might be an issue
            # in things like the -1/-3 from ngdc so try for an idinfo blob
            poc_elem = extract_elem(id_elem, [
                'identificationInfo',
                'MD_DataIdentification',
                'pointOfContact',
                'CI_ResponsibleParty'])
            # if poc_elem is None:
            #     # and if that fails try for the root-level contact
            #     poc_elem = extract_elem(
            #         self.elem,
            #         ['contact', 'CI_ResponsibleParty'])

            # TODO: point of contact is not necessarily the publisher
            if poc_elem is not None:
                poc = self._parse_responsibleparty(poc_elem)
                location = (
                    ' '.join(
                        [poc['contact'].get('city', ''),
                         poc['contact'].get('country', '')])
                ).strip() if poc.get('contact', {}) else ''

                self.output['publishers'].append(tidy_dict({
                    "object_id": generate_uuid_urn(),
                    "name": poc.get('organization', ''),
                    "location": location
                }))
                dataset['relationships'].append({
                    "relate": "dcterms:publisher",
                    "object_id": self.output['publisher']['object_id']
                })

            dataset['urls'] = []
            dist_elems = extract_elems(self.elem, ['distributionInfo'])
            for dist_elem in dist_elems:
                dists = self._parse_distribution(dist_elem)
                if dists:
                    dataset['urls'] += dists

            for url in dataset['urls']:
                dataset['relationships'].append({
                    "relate": "dcterms:references",
                    "object_id": url['object_id']
                })

            self.output['datasets'].append(dataset)
            self.output['keywords'] += keywords

        # TODO: removing this until we have a definition for SERVICE
        # # check for the service elements
        # service_elems = extract_elems(self.elem,
        #     ['identificationInfo', 'SV_ServiceIdentification'])
        # self.description['services'] = []
        # for service_elem in service_elems:
        #     sv = SrvParser(service_elem)
        #     self.description['services'].append(sv.parse())

        self.description = tidy_dict(self.output)


class SrvParser(object):
    '''
    read a service identification element as
    19119 or the embedded md/mi element
    '''
    def __init__(self, elem, catalog_record):
        self.elem = elem
        self.output = {"catalog_record": catalog_record, "relationships": []}

    def _handle_parameter(self, elem):
        ''' parse an sv_parameter element '''
        param = {}

        param['name'] = extract_item(
            elem, ['name', 'aName', 'CharacterString'])
        param['inputType'] = extract_item(
            elem,
            ['name', 'attributeType', 'TypeName', 'aName', 'CharacterString'])
        param['direction'] = extract_item(
            elem, ['direction', 'SV_ParameterDirection'])
        param['optional'] = extract_item(
            elem, ['optionality', 'CharacterString'])
        param['cardinality'] = extract_item(
            elem, ['repeatability', 'Boolean'])
        param['valueType'] = extract_item(
            elem, ['valueType', 'TypeName', 'aName', 'CharacterString'])

        return param

    def _handle_operations(self):
        elems = extract_elems(
            self.elem,
            ['containsOperations', 'SV_OperationMetadata'])

        ops = []
        for e in elems:
            op = {}
            op['name'] = extract_item(
                e,
                ['operationName', 'CharacterString'])
            op['method'] = extract_attrib(
                e,
                ['DCP', 'DCPList', '@codeListValue'])
            op['url'] = extract_item(
                e,
                ['connectPoint', 'CI_OnlineResource', 'linkage', 'URL'])
            op['parameters'] = [
                self._handle_parameter(pe) for pe in
                extract_elems(e, ['parameters', 'SV_Parameter'])]
            ops.append(op)

        return ops

    def parse(self):
        if self.elem is None:
            self.description = self.output
            return

        self.description = parse_identification_info(self.elem)

        self.description['operations'] = self._handle_operations()

        self.description = tidy_dict(self.description)


class DsParser(object):
    '''
    the parent ds parsing (as an mi/md record itself)
    plus the nested children in composedOf
    '''
    def __init__(self, elem, catalog_record):
        self.elem = elem
        self.output = {"catalog_record": catalog_record}

    # TODO: check on mi vs md here
    def parse(self):
        # get the series
        self.description = {}
        md = extract_elem(self.elem, ['seriesMetadata', 'MD_Metadata'])
        if md is None:
            return

        md_parser = MxParser(md)
        md_parser.parse()
        self.description = md_parser.description
        self.description['children'] = []

        # get the children
        children = extract_elems(
            self.elem, ['composedOf', 'DS_DataSet', 'has', 'MD_Metadata'])
        for child in children:
            child_parser = MxParser(child)
            child_parser.parse()
            if child_parser.description:
                self.description['children'].append(child_parser.description)

        self.description = tidy_dict(self.description)
