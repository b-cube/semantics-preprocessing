import re
from lib.parser import BasicParser
from lib.nlp_utils import load_token_list

'''
widgetry for extracting and handling the
extraction of unique identifiers from some
unknown xml blob of text

- add the stopwords (update the utils to run generic stopwords lists instead)
- lowercase identifiers before simhashes
- all the regex widgets
- sort out that url issue
- sort out the non-urn urns
- test the system
- make the task
'''


# use nlp_utils.remove_tokens('namespaces.txt', text)
# TODO: the urn captures http: strings (because of the colon)
_pattern_set = [
    ('url', re.compile(ur"((?:(?:https?|ftp|http)://)(?:\S+(?::\S*)?@)?(?:(?!(?:10|127)(?:.\d{1,3}){3})(?!(?:169.254|192.168)(?:.\d{1,3}){2})(?!172.(?:1[6-9]|2\d|3[0-1])(?:.\d{1,3}){2})(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}(?:.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))|(?:(?:[a-z\\u00a1-\\uffff0-9]-*)*[a-z\\u00a1-\\uffff0-9]+)(?:.(?:[a-z\\u00a1-\\uffff0-9]-*)*[a-z\\u00a1-\\uffff0-9]+)*(?:.(?:[a-z\\u00a1-\\uffff]{2,})))(?::\d{2,5})?(?:/\S*)?)", re.IGNORECASE)),
    ('urn', re.compile(ur"(?![http:])(([a-z0-9.][a-z0-9-.]{0,}\S:\S)+[a-z0-9()+,\-.:=@;$_!*'%/?#]+)", re.IGNORECASE)),
    # ('urn', re.compile(ur"\burn:[a-z0-9][a-z0-9-]{0,31}:[a-z0-9()+,\-.:=@;$_!*'%/?#]+", re.IGNORECASE)),
    ('uuid', re.compile(ur'([a-f\d]{8}(-[a-f\d]{4}){3}-[a-f\d]{12}?)', re.IGNORECASE)),
    ('doi', re.compile(ur"(10[.][0-9]{4,}(?:[/][0-9]+)*/(?:(?![\"&\\'])\S)+)", re.IGNORECASE))
]

_rule_set = [
    ('uri', 'fileIdentifier/CharacterString'),  # ISO
    ('uri', 'identifier/*/code/CharacterString'),
    ('uri', 'dataSetURI/CharacterString'),
    ('uri', 'parentIdentifier/CharacterString'),
    ('uri', 'Entry_ID'),  # DIF
    ('uri', 'dc/identifier'),  # DC
    ('basic', 'Layer/Name'),  # WMS
    ('basic', 'dataset/@ID'),  # THREDDS
    ('uri', '@URI'),  # ddi
    ('uri', '@IDNo')  # ddi
]


def chunk_identifier(identifier):
    '''
    split, sort, rejoin
    '''
    pass


def match(s, p):
    m = re.search(p, s)
    return m.group(0) if m else ''


def extract_by_regex(text):
    '''
    pull identifiers based on the set of regex patterns
    '''
    # to count how many spaces for the url wonkiness
    # it is not a cure-all and is not catching everything
    space_pattern = re.compile(' ')

    for pattern_type, pattern in _pattern_set:
        m = match(text, pattern)
        if m:
            if pattern_type == 'url' and space_pattern.subn(' ', m)[1] > 0:
                m = m.split(' ')[0]

            yield (pattern_type, str(m))


def extract_by_xpath(xml):
    '''
    try to pull identifiers based on some
    common patterns/known patterns
    '''
    def _get_text(e):
        if isinstance(e, str):
            # i suspect this should be basestring
            return e
        try:
            return e.text
        except:
            # TODO: forgotten what this exception is.
            return None

    def _build_xpath(rule):
        # i doubt this is in any way performant
        return '//' + '/'.join(['%s*[local-name()="%s"]' %
                                ('@' if '@' in r else '', r)
                                if r not in ['*', '..', '.']
                                else r for r in rule.split('/')]
                               )

    for pattern_type, rule in _rule_set:
        xp = _build_xpath(rule)
        results = xml.xpath(xp)
        results = results if isinstance(results, list) else [results]

        # go through the result set
        for result in results:
            t = _get_text(result)
            if t is None:
                continue

            # run it against the regex checks
            for match_tuple in extract_by_regex(t):
                yield match_tuple

            # and return the text blob (could be mnemonic, etc)
            yield (pattern_type, str(t))


# TODO: add the logging to capture what & where
def process_xml_identifiers(text, handle_html=False, excludes=[]):
    '''
    run the regex and xpath checks
    starting with the text ? for more
    parsing

    handle_html is mostly for things like RSS

    run a piece of text
    '''
    # TODO: we are starting with the html handling for both options
    #       but that might be not the greatest
    parser = BasicParser(text, handle_html=handle_html, include_html_hrefs=handle_html)

    for tag_blob, text_blob in parser.strip_text():
        for match_tuple in process_string_identifiers(text_blob, excludes):
            yield match_tuple

    for match_type, match_blob in extract_by_xpath(parser.xml):
        if not any(e in match_blob.lower() for e in excludes):
            yield (match_type, match_blob)


def process_string_identifiers(text, excludes=[]):
    for match_type, match_blob in extract_by_regex(text):
        if not any(e in match_blob.lower() for e in excludes):
            yield (match_type, match_blob)


def extract_identifiers(source_url, source_xml_as_string, handle_html=False):
    '''
    run the response object

    return a set of identifiers (pattern type, identifier) and
        a probable object identifier
    '''

    # set up the excludes list
    mimetypes = load_token_list('mimetypes.txt')
    namespaces = load_token_list('namespaces.txt')
    # TODO: add the CONTAINS excludes (these are 1:1 MATCH excludes)
    excludes = list(set(mimetypes).union(set(namespaces)))

    # extract identifiers from the url
    url_identifiers = list(iter(process_string_identifiers(source_url, excludes=excludes)))
    url_identifiers = set(url_identifiers)

    # extract the identifiers from the xml
    xml_identifiers = list(iter(
        process_xml_identifiers(source_xml_as_string, True, excludes=excludes)))
    xml_identifiers = set(xml_identifiers)

    # do a little set intersect to see if we
    # can a match between the two
    possible_object_identifier = url_identifiers.intersection(xml_identifiers)

    return list(url_identifiers.union(xml_identifiers)), list(possible_object_identifier)

'''
urn examples
gov.noaa.ngdc.mgg.geophysics:G01442
urn:ogc:def:crs:EPSG::5715

different hash ids in one iso:
http://catalog.data.gov/harvest/object/5e8cda58-9ea1-4038-9a11-98088f8749fa

'''
