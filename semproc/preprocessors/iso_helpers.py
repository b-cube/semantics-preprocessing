import dateutil.parser as dateparser
from semproc.xml_utils import extract_item, extract_items, generate_localname_xpath
from semproc.xml_utils import extract_elem, extract_elems, extract_attrib
from semproc.utils import tidy_dict
from semproc.geo_utils import bbox_to_geom, gml_to_geom, reproject, to_wkt
from semproc.utils import generate_sha_urn, generate_uuid_urn


def parse_identifiers(elem):
    # note that this elem is the root iso
    identifiers = []

    xps = [
        ['fileIdentifier', 'CharacterString'],
        ['identificationInfo',
         'MD_DataIdentification',
         'citation',
         'CI_Citation',
         'identifier',
         'MD_Identifier',
         'code',
         'CharacterString'],
        ['dataSetURI', 'CharacterString']  # TODO: this can be multiple items
    ]

    for xp in xps:
        i = extract_item(elem, xp)
        if i:
            identifiers.append(i)

    return identifiers
























