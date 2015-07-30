import re
from semproc.parser import Parser
from semproc.nlp_utils import load_token_list
from semproc.utils import unquote, break_url, match
import dateutil.parser as dateparser
from itertools import chain, izip
import json


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


_pattern_set = [
     ('url', re.compile(ur"((?:(?:https?|ftp|http)://)(?:\S+(?::\S*)?@)?(?:(?!(?:10|127)(?:.\d{1,3}){3})(?!(?:169.254|192.168)(?:.\d{1,3}){2})(?!172.(?:1[6-9]|2\d|3[0-1])(?:.\d{1,3}){2})(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}(?:.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))|(?:(?:[a-z\\u00a1-\\uffff0-9]-*)*[a-z\\u00a1-\\uffff0-9]+)(?:.(?:[a-z\\u00a1-\\uffff0-9]-*)*[a-z\\u00a1-\\uffff0-9]+)*(?:.(?:[a-z\\u00a1-\\uffff]{2,})))(?::\d{2,5})?(?:/\S*)?)", re.IGNORECASE)),
    # a urn that isn't a url
    ('urn', re.compile(ur"(?![http://])(?![https://])(?![ftp://])(([a-z0-9.\S][a-z0-9-.\S]{0,}\S:{1,2}\S)+[a-z0-9()+,\-.=@;$_!*'%/?#]+)", re.IGNORECASE)),
    # ('urn', re.compile(ur"\burn:[a-z0-9][a-z0-9-]{0,31}:[a-z0-9()+,\-.:=@;$_!*'%/?#]+", re.IGNORECASE)),
    ('uuid', re.compile(ur'([a-f\d]{8}(-[a-f\d]{4}){3}-[a-f\d]{12}?)', re.IGNORECASE)),
    ('doi', re.compile(ur"(10[.][0-9]{4,}(?:[/][0-9]+)*/(?:(?![\"&\\'])\S)+)", re.IGNORECASE)),
    ('md5', re.compile(ur"([a-f0-9]{32})", re.IGNORECASE))
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


class Identifier(object):
    def __init__(self, tag, extraction_type, match_type, original_text, potential_identifier):
        self.tag = tag
        self.extraction_type = extraction_type
        self.match_type = match_type
        self.original_text = original_text
        self.potential_identifier = potential_identifier
    
    def __eq__(self, other):
        return (isinstance(other, self.__class__)
            and self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self.__eq__(other)
    
    def has(self, comparison_identifier):
        return self.potential_identifier == comparison_identifier

    def __repr__(self):
        return '<Identifier %s>' % json.dumps(self.__dict__)
    
    
class IdentifierExtractor(object):
    def __init__(self, source_url, source_xml_as_str):
        self.source_url = source_url
        self.source_xml_as_str = source_xml_as_str
        
        self.identifieds = []
        self.texts = []
        self.seen_texts = []
        
        self._parse()
    
    def _parse(self):
        try:
            parser = BasicParser(self.source_xml_as_str, True, True)
        except Exception as ex:
            print ex
        if not parser or parser.xml is None:
            raise Exception('failed to parse')
        
        for tag, txt in parser.strip_text():
            self.texts.append((tag, txt))
            
    def _strip_punctuation(self, text):
        terminal_punctuation = '(){}[].,~|":'
        text = text.strip(terminal_punctuation)
        return text.strip()

    def _strip_dates(self, text):
        # this should still make it an invalid date
        # text = text[3:] if text.startswith('NaN') else text
        try:
            d = dateparser.parse(text)
            return ''
        except ValueError:
            return text
                
    def _strip_scales(self, text):
        scale_pttn = ur"(1:[\d]{0,}(,[\d]{3}){1,})"
        m = match(text, scale_pttn)
        if m:
            return ''
        return text

    def _strip_excludes(self, text):
        if any(e.lower() in text.lower() for e in excludes):
            return ''
        return text

    def _strip_whitespace(self, text):
        space_pattern = re.compile(' ')
        if space_pattern.subn(' ', text)[1] > 0:
            # i actually don't know if this is the right index. huh.
            return text.split(' ')[0]
        return text
        
    def _tidy_text(self, text):
        text = self._strip_punctuation(text)
        if not text:
            return ''
        
        text = self._strip_scales(text)
        if not text:
            return ''
    
        text = self._strip_dates(text)
        if not text:
            return ''
    
        text = self._strip_whitespace(text)
        if not text:
            return ''
        
        return text
        
    def _extract_url(self, text):
        pttn = re.compile(ur"((?:(?:https?|ftp|http)://)(?:\S+(?::\S*)?@)?(?:(?!(?:10|127)(?:.\d{1,3}){3})(?!(?:169.254|192.168)(?:.\d{1,3}){2})(?!172.(?:1[6-9]|2\d|3[0-1])(?:.\d{1,3}){2})(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}(?:.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))|(?:(?:[a-z\\u00a1-\\uffff0-9]-*)*[a-z\\u00a1-\\uffff0-9]+)(?:.(?:[a-z\\u00a1-\\uffff0-9]-*)*[a-z\\u00a1-\\uffff0-9]+)*(?:.(?:[a-z\\u00a1-\\uffff]{2,})))(?::\d{2,5})?(?:/\S*)?)",
                          re.IGNORECASE)
        m = match(text, pttn)
        if not m:
            return '', []

        url = self._tidy_text(unquote(m))
        base_url, values = break_url(url)
        values = values.split(' ') + [base_url]
        
        # return the original extracted url, and the values plus 
        # the base_url for more extracting
        return url, filter(None, [self._tidy_text(v) for v in values])

    def _extract_identifiers(self, text):
        for pattern_type, pattern in _pattern_set:
            m = match(text, pattern)
            if not m:
                continue
            yield pattern_type, m
    
    def _check(self, comparison_identifier, arr):
        return len([a for a in arr if a.has(comparison_identifier)]) > 0
    
    def process_text(self):
        while self.texts:
            tag, text = self.texts.pop()
            if self._check(text, self.seen_texts) or not text.strip():
                continue
                
            try:
                j = json.loads(text)
                j.keys()  # it will decode a quoted string without error
                continue
            except:
                pass
            
            url, values = self._extract_url(text)            
            values = [v for v in values if not self._check(v, self.seen_texts)]
            self.texts += list(iter(izip([tag]* len(values), values)))
            
            if url and not self._check(url, self.identifieds) and not self._check(url, self.seen_texts):
                identify = Identifier(tag, 'regex', 'url', text, url)
                self.identifieds.append(identify)
                self.seen_texts.append(identify)
            
            # now run the OTHER regex
            for match_type, match_text in self._extract_identifiers(text):
                # clean it up (make sure it's still a good thing)
                # before checking against knowns and appending
                cleaned_text = self._tidy_text(match_text)
                
                if cleaned_text and not self._check(cleaned_text, self.identifieds):
                    self.identifieds.append(Identifier(tag, 'regex', match_type, text, cleaned_text))
                if not self._check(cleaned_text, self.seen_texts):
                    self.texts.append((tag, cleaned_text))
                    self.seen_texts.append(Identifier(tag, 'regex', match_type, text, cleaned_text))


'''
urn examples
gov.noaa.ngdc.mgg.geophysics:G01442
urn:ogc:def:crs:EPSG::5715

different hash ids in one iso:
http://catalog.data.gov/harvest/object/5e8cda58-9ea1-4038-9a11-98088f8749fa

'''
