import re
from urlparse import urlparse
from lib.nlp_utils import remove_tokens
from lxml import etree

'''
widgetry for extracting and handling the
extraction of unique identifiers from some
unknown xml blob of text
'''



- add the stopwords (update the utils to run generic stopwords lists instead)
- lowercase identifiers before simhashes
- all the regex widgets
- sort out that url issue
- sort out the non-urn urns
- test the system
- make the task


# use nlp_utils.remove_tokens('namespaces.txt', text)

_pattern_set = [
    ('url', re.compile(ur"((?:(?:https?|ftp|http)://)(?:\S+(?::\S*)?@)?(?:(?!(?:10|127)(?:.\d{1,3}){3})(?!(?:169.254|192.168)(?:.\d{1,3}){2})(?!172.(?:1[6-9]|2\d|3[0-1])(?:.\d{1,3}){2})(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}(?:.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))|(?:(?:[a-z\\u00a1-\\uffff0-9]-*)*[a-z\\u00a1-\\uffff0-9]+)(?:.(?:[a-z\\u00a1-\\uffff0-9]-*)*[a-z\\u00a1-\\uffff0-9]+)*(?:.(?:[a-z\\u00a1-\\uffff]{2,})))(?::\d{2,5})?(?:/\S*)?)", re.IGNORECASE)),
    ('urn', re.compile(ur"(([a-z0-9.][a-z0-9-.]{0,}:)+[a-z0-9()+,\-.:=@;$_!*'%/?#]+)", re.IGNORECASE)),
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


def extract_by_regex(text, excludes=[]):
    '''
    pull identifiers based on the set of regex patterns
    '''
    # to count how many spaces for the url wonkiness
    # it is not a cure-all and is not catching everything
    space_pattern = re.compile(' ')

    for pattern_type, pattern in _pattern_set:
        m = match(s, pattern)
        if m and not any(e in m.lower() for e in excludes):
            if pattern_type == 'url' and space_pattern.subn('', m)[1] > 0:
                m = m.split(' ')[0]

            yield (pattern_type, m)


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
            yield (pattern_type, t)


def process_identifiers(xml):
    '''
    run the regex and xpath checks
    '''
    text = etree.tostring(xml)

    pass



urn examples:
gov.noaa.ngdc.mgg.geophysics:G01442
urn:ogc:def:crs:EPSG::5715

different hash ids in one iso:
http://catalog.data.gov/harvest/object/5e8cda58-9ea1-4038-9a11-98088f8749fa