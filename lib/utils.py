import re
import urlparse
import HTMLParser

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
nlp prep methods
'''


def normalize_keyword_text(keyword_string):
    '''
    this is the very basic regex-based normalization. we
    know that keywords are handled in a variety of ways even
    in standards that support multiple term elements. we also
    know that the nlp tokenizers, etc, won't parse strings
    correctly using certain delimiters (they are not standard
    punctuation in those ways).

    unescape any html bits (thanks gcmd!)

    delimiters: , ; > | + -
        (ignore space-delimited strings - let the tokenizers
            manage that)
        (we are also going to actually just ignore the commas as well)
    '''
    hp = HTMLParser.HTMLParser()
    keyword_string = hp.unescape(keyword_string)

    simple_pattern = r'[;|>+-]'
    return re.sub(simple_pattern, ',', keyword_string)
