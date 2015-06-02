# from lxml import etree
from lib.utils import generate_localname_xpath
import dateutil as dateparser


def parse_identification_info(self, elem):
    xp = generate_localname_xpath(['citation', 'CI_Citation', 'title', 'CharacterString'])
    title_elem = next(iter(elem.xpath(xp), None))
    title = '' if title_elem is None else title_elem.text

    xp = generate_localname_xpath(['abstract', 'CharacterString'])
    abstract_elem = next(iter(elem.xpath(xp), None))
    abstract = '' if abstract_elem is None else abstract_elem.text

    return title, abstract


def parse_keywords(self, elem):
    '''
    for each descriptiveKeywords block
    in an identification block
    '''
    keywords = []

    xp = generate_localname_xpath(
        ['descriptiveKeywords', 'MD_Keywords', 'keyword', 'CharacterString'])
    keyword_elems = elem.xpath(xp)
    keywords += [keyword_elem.text for keyword_elem in keyword_elems
                 if keyword_elem is not None and keyword_elem.text]

    # grab the iso topic categories as well
    xp = generate_localname_xpath(['topicCategory', 'MD_TopicCategoryCode'])
    topic_elems = elem.xpath(xp)
    keywords += [topic_elem.text for topic_elem in topic_elems
                 if topic_elem is not None and topic_elem.text]

    return keywords


def parse_responsibleparty(self, elem):
    '''
    parse any CI_ResponsibleParty
    '''
    xp = generate_localname_xpath(['individualName'])
    e = next(iter(elem.xpath(xp)), None)
    if e is not None:
        individual_name = e.text

    xp = generate_localname_xpath(['organizationName'])
    e = next(iter(elem.xpath(xp)), None)
    if e is not None:
        organization_name = e.text

    xp = generate_localname_xpath(['contactInfo', 'CI_Contact'])
    e = next(iter(elem.xpath(xp)), None)
    if e is not None:
        contact = self._parse_contact(e)

    return individual_name, organization_name, contact


def parse_contact(self, elem):
    '''
    parse any CI_Contact
    '''
    xp = generate_localname_xpath(['phone', 'CI_Telephone', 'voice', 'CharacterString'])

    xp = generate_localname_xpath(['address', 'CI_Address', 'deliveryPoint', 'CharacterString'])

    xp = generate_localname_xpath(['address', 'CI_Address', 'city', 'CharacterString'])

    xp = generate_localname_xpath(['address', 'CI_Address', 'administrativeArea', 'CharacterString'])

    xp = generate_localname_xpath(['address', 'CI_Address', 'postalCode', 'CharacterString'])

    xp = generate_localname_xpath(['address', 'CI_Address', 'country', 'CharacterString'])

    xp = generate_localname_xpath(['address', 'CI_Address', 'electronicMailAddress', 'CharacterString'])

    pass


def parse_distribution(self, elem):
    ''' from the distributionInfo element '''
    xp = generate_localname_xpath([])


def handle_bbox(self, bounding_box_elem):
    xp = generate_localname_xpath(['westBoundLongitude', 'Decimal'])
    west = next(iter(bounding_box_elem.xpath(xp)), None)
    west = west.text if west is not None else ''

    xp = generate_localname_xpath(['eastBoundLongitude', 'Decimal'])
    east = next(iter(bounding_box_elem.xpath(xp)), None)
    east = east.text if east is not None else ''

    xp = generate_localname_xpath(['southBoundLatitude', 'Decimal'])
    south = next(iter(bounding_box_elem.xpath(xp)), None)
    south = south.text if south is not None else ''

    xp = generate_localname_xpath(['northBoundLatitude', 'Decimal'])
    north = next(iter(bounding_box_elem.xpath(xp)), None)
    north = north.text if north is not None else ''

    return [west, south, east, north]


def handle_polygon(self, polygon_elem):
    pass


def handle_points(self, point_elem):
    # this may not exist in the -2?
    pass


def parse_extent(self, elem):
    '''
    handle the spatial and/or temporal extent
    starting from the *:extent element
    '''
    xp = generate_localname_xpath(['EX_Extent', 'geographicElement'])
    geo_elem = next(iter(elem.xpath(xp), None))
    if geo_elem is not None:
        # we need to sort out what kind of thing it is bbox, polygon, list of points
        bbox_elem = next(iter(
            geo_elem.xpath(generate_localname_xpath(['EX_GeographicBoundingBox'])), None))
        if bbox_elem is not None:
            yield self._handle_bbox(bbox_elem)

        poly_elem = next(iter(
            geo_elem.xpath(generate_localname_xpath(['EX_BoundingPolygon'])), None))
        if poly_elem is not None:
            yield self._handle_polygon(poly_elem)

    xp = generate_localname_xpath(['EX_Extent', 'temporalElement', 'extent', 'TimePeriod'])
    time_elem = next(iter(elem.xpath(xp), None))
    if time_elem is not None:
        begin_position = next(iter(
            time_elem.xpath(generate_localname_xpath(['beginPosition'])), None))
        end_position = next(iter(
            time_elem.xpath(generate_localname_xpath(['endPosition'])), None))

        if begin_position is not None and 'indeterminatePosition' not in begin_position.attrib:
            begin_position = self._parse_timestamp(begin_position.text)
        if end_position is not None and 'indeterminatePosition' not in end_position.attrib:
            end_position = self._parse_timestamp(end_position.text)

        yield begin_position, end_position


def parse_timestamp(self, text):
    '''
    generic handler for any iso date/datetime/time/whatever element
    '''
    try:
        # TODO: deal with timezones if this doesn't
        return dateparser.parse(text)
    except ValueError:
        return None
