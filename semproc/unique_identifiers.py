import re
from semproc.bag_parser import BagParser
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
    ('url', re.compile(ur"""(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))""", re.IGNORECASE)),
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
    def __init__(
            self,
            tag,
            extraction_type,
            match_type,
            original_text,
            potential_identifier):
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

    def to_json(self):
        return {
            "tag": self.tag,
            "extraction_type": self.extraction_type,
            "match_type": self.match_type,
            "original_text": self.original_text,
            "potential_identifier": self.potential_identifier
        }


class IdentifierExtractor(object):
    def __init__(self, source_url, source_xml_as_str, equality_excludes=[], contains_excludes=[]):
        self.source_url = source_url
        self.source_xml_as_str = source_xml_as_str
        self.identifieds = []
        self.texts = [('', self.source_url)]
        self.seen_texts = []
        self.equality_excludes = equality_excludes
        self.contains_excludes = contains_excludes

        self._parse()

    def _parse(self):
        try:
            parser = BagParser(self.source_xml_as_str, False, False)
        except Exception as ex:
            print ex
            raise ex
        if not parser or parser.parser.xml is None:
            raise Exception('failed to parse')

        for tag, txt in parser.strip_text():
            self.texts.append((tag, txt))

    def _strip_punctuation(self, text):
        terminal_punctuation = '(){}[].,~|":&-'
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

    def _strip_excludes(self, match_type, tag, text):
        # TODO: how to handle the excludes for skipping
        #       by tag and skipping by value and what was
        #       the thinking a few months ago?
        if match_type == 'url':
            if text in self.equality_excludes:
                # equality only
                return ''
            return text

        if any(e.lower() in text.lower() for e in self.contains_excludes):
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
        pttn = re.compile(ur"""(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))""",
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
            self.texts += list(iter(izip([tag] * len(values), values)))

            if url and not self._check(url, self.identifieds) \
                    and not self._check(url, self.seen_texts):
                identify = Identifier(tag, 'regex', 'url', text, url)
                self.identifieds.append(identify)
                self.seen_texts.append(identify)

            # now run the OTHER regex
            for match_type, match_text in self._extract_identifiers(text):
                # clean it up (make sure it's still a good thing)
                # before checking against knowns and appending
                cleaned_text = self._tidy_text(match_text)

                if cleaned_text and not self._check(
                        cleaned_text, self.identifieds):
                    self.identifieds.append(
                        Identifier(
                            tag, 'regex', match_type, text, cleaned_text
                        )
                    )
                if not self._check(cleaned_text, self.seen_texts):
                    self.texts.append((tag, cleaned_text))
                    self.seen_texts.append(
                        Identifier(
                            tag, 'regex', match_type, text, cleaned_text)
                    )


'''
urn examples
gov.noaa.ngdc.mgg.geophysics:G01442
urn:ogc:def:crs:EPSG::5715

different hash ids in one iso:
http://catalog.data.gov/harvest/object/5e8cda58-9ea1-4038-9a11-98088f8749fa

'''
