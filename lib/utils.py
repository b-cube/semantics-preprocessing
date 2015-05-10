import urlparse
import urllib
import collections
from uuid import uuid4
import hashlib


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


def unquote(url):
    return urllib.unquote(url)


def parse_url(url):
    '''
    strip out the query parameters
    '''
    if not url:
        return ''
    parsed_url = urlparse.urlparse(url)
    return urlparse.parse_qs(parsed_url.query)


def intersect_url(url, path, bases=[]):
    '''
    returns a list of urls

    params:
        url: root path
        path: "test" path, ie path to intersect
        bases: an array of relative intermediate paths (thredds service blobs)
    '''
    if path.startswith('/'):
        path = path[1:]
    parts = urlparse.urlparse(path)
    if parts.scheme and parts.netloc:
        # it's a valid url, do nothing
        return [path]

    parts = urlparse.urlparse(url)
    url_paths = parts.path.split('/')
    paths = path.split('/')

    if bases:
        # it has options at the root of the base path
        return [urlparse.urlunparse((
            parts.scheme,
            parts.netloc,
            '/'.join([b, path]),
            parts.params,
            parts.query,
            parts.fragment
        )) for b in bases]

    match_index = url_paths.index(paths[0]) if paths[0] in url_paths else -1
    if match_index < 0:
        # it does not intersect, just combine
        return [urlparse.urljoin(url.replace('catalog.xml', ''), path)]
    else:
        # there is some overlap, union
        return [
            urlparse.urljoin(
                urlparse.urlunparse(
                    (
                        parts.scheme,
                        parts.netloc,
                        '/'.join(url_paths[0:match_index + 1]),
                        parts.params,
                        parts.query,
                        parts.fragment
                    )
                ),
                path
            )
        ]

'''
general utils
'''


def generate_short_uuid():
    '''
    this is not a proper uuid and should not be used as such
    it is the first chunk of the hash
    '''
    return str(uuid4()).split('-')[0]


def generate_sha(text):
    return hashlib.sha224(text).hexdigest()


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


def generate_localname_xpath(tags):
    '''
    from some tag "list", generate an xpath using local-names only

    note: this is meant for processing and not for the remainder/excludes
          functions

    params:
        tags: list of element names as root/parent/child

    returns:
        *[local-name()="root"]/*[local-name()="parent"]/*[local-name()="child"]
    '''
    return '/'.join(['*[local-name()="%s"]' % t if t not in ['*', '..', '.'] else t
                    for t in tags.split('/') if t])


def tidy_dict(items):
    # cleanup a dict (remove empty elements)
    # but only at the single depth
    to_remove = []
    for k, v in items.iteritems():
        if not v:
            to_remove.append(k)
    for k in to_remove:
        del items[k]

    return items


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
