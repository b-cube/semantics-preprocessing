import urlparse
import collections
from uuid import uuid4


'''
spatial handling:
    wcs envelopes
'''


def parse_gml_envelope(envelope, namespaces):
    '''
    from a wcs lonLatEnvelope node, extract a bbox as
    [min, miny, maxx, maxy] with crs understanding

    note: no reprojection here so if not epsg:4326? and what to
    do about invalid srsName values/versions?
    '''
    # srs = envelope.attrib['srsName'] if 'srsName' in envelope.attrib
    # if srs != 'EPSG:4326':
    # if srs != 'urn:ogc:def:crs:OGC:1.3:CRS84'
    #   return []

    # two nodes required, first as lower left, second as upper right
    lower_left = envelope.xpath('gml:pos[1]', namespaces=namespaces)
    assert lower_left
    mins = map(float, lower_left[0].text.split(' '))

    upper_right = envelope.xpath('gml:pos[2]', namespaces=namespaces)
    assert upper_right
    maxes = map(float, upper_right[0].text.split(' '))

    return mins + maxes


'''
url handling:
    query parameter parsing
'''


def parse_url(url):
    '''
    strip out the query parameters
    '''
    if not url:
        return ''
    parsed_url = urlparse.urlparse(url)
    return urlparse.parse_qs(parsed_url.query)


'''
general utils
'''


def generate_short_uuid():
    '''
    this is not a proper uuid and should not be used as such
    it is the first chunk of the hash
    '''
    return str(uuid4()).split('-')[0]


def extract_element_tag(tag):
    '''
    drop the fully qualified namespace
    '''
    if not tag:
        return

    return tag.split('}')[-1]


def generate_qualified_xpath(elem, do_join=True):
    '''
    from some element, iterate through the parents
    and generate the xpath back to it (without specific
        text values, ie no [text()= "thing"])
    '''
    tags = [elem.tag] + [e.tag for e in elem.iterancestors()]
    tags.reverse()

    # TODO: handle the comments
    # check for an assumed comment object
    # if sum([isinstance(a, str) for a in tags]) != len(tags):
    #     continue

    return '/'.join(tags) if do_join else tags


def flatten(items, excluded_keys=[]):
    '''
    flatten a list of irregular lists/singletons
    or some dict of singletons, lists, dicts

    basically just get a list of terminal strings
    '''

    def _flatten(item):
        if isinstance(item, dict):
            for k, v in item.iteritems():
                if k in excluded_keys:
                    continue
                # TODO: this introduces nested lists again!
                yield list(_flatten(v))
        elif isinstance(item, list):
            for i in item:
                if isinstance(i, collections.Iterable) and not isinstance(i, basestring):
                    for subitem in _flatten(i):
                        yield subitem
                else:
                    yield i
        elif isinstance(item, str):
            yield item

    arr = list(_flatten(items))
    if len([isinstance(a, collections.Iterable) and
            not isinstance(a, basestring) for a in arr]) > 0:
        # ick, flatten the dict issue again.
        return list(_flatten(arr))

    return arr
