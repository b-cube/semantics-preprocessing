import re
from semproc.bag_parser import BagParser
from semproc.utils import unquote, break_url, match
import dateutil.parser as dateparser
from datetime import datetime
from itertools import izip
import json
from rfc3987 import parse as uparse


'''
widgetry for extracting and handling the
extraction of unique identifiers from some
unknown xml blob of text
'''


_pattern_set = [
    ('doi', re.compile(ur"((?:https?:\/\/){1}(?:dx\.)?doi\.org\/(10[.][0-9]{4,}(?:[/][0-9]+)*/(?:(?![\"&\\'])\S)+))", re.IGNORECASE)),
    # from a hdl.handle.net registry; don't need this.
    # ('hdl', re.compile(ur'((?:https?:\/\/){1}(?:hdl\.)?handle\.net\/(?:(?:\w)*:#!\/)?(?:[\w\-]*\/)*([\w\-\.]*)/{0,1})', re.IGNORECASE)),
    # we are just checking for urls each string, don't need this (here)
    # ('url', re.compile(ur"""(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))""", re.IGNORECASE)),
    ('urn', re.compile(ur'^([a-z0-9.#]{0,}:([a-z0-9][a-z0-9.-]{0,31}):[a-z0-9A-Z_()+,-.:=@;$!*\'%/?#\[\]]+)', re.IGNORECASE)),
    ('uuid', re.compile(ur'([a-f\d]{8}(-[a-f\d]{4}){3}-[a-f\d]{12}?)', re.IGNORECASE)),
    ('doi', re.compile(ur"((doi:){0,1}10[.][0-9]{4,}(?:[/][0-9]+)*/(?:(?![\"&\\'])\S)+)", re.IGNORECASE)),
    ('md5', re.compile(ur"(\b([A-Fa-f0-9]{32}))\b", re.IGNORECASE))
]

_rule_set = [
    ('uri', 'fileIdentifier/CharacterString'),  # ISO
    ('uri', 'identifier/'),
    ('uri', 'dataSetURI/CharacterString'),
    ('uri', 'parentIdentifier/CharacterString'),
    ('uri', 'Entry_ID'),  # DIF
    ('uri', 'dc/identifier'),  # DC
    ('basic', 'Layer/Name'),  # WMS
    ('basic', 'dataset/ID'),  # THREDDS
    ('uri', '@URI'),  # ddi
    ('uri', '@IDNo'),  # ddi
    ('uri', '@ID')
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
            "original_text": self.original_text.replace(
                '\n', ' ').replace('\r', ' '),
            "potential_identifier": self.potential_identifier
        }


class IdentifierExtractor(object):
    def __init__(
            self,
            source_url,
            source_xml_as_str,
            equality_excludes=[],
            contains_excludes=[],
            tag_excludes=[]):
        self.source_url = source_url
        self.source_xml_as_str = source_xml_as_str
        self.identifieds = []
        self.texts = [('', self.source_url)]
        self.seen_texts = []
        self.equality_excludes = equality_excludes
        self.contains_excludes = contains_excludes
        self.tag_excludes = tag_excludes

        self._parse()

    def _parse(self):
        try:
            parser = BagParser(self.source_xml_as_str, True, False)
        except Exception as ex:
            print ex
            raise ex
        if not parser or parser.parser.xml is None:
            raise Exception('failed to parse')

        for tag, txt in parser.strip_text():
            # if it's from a tag we know we nee to exclude
            if any(t in tag for t in self.tag_excludes):
                continue

            if not txt.strip():
                continue

            # do not split if it comes form an identifier field
            self.texts += (
                (tag, t) for t in txt.split()
            ) if not any(r[1] in tag for r in _rule_set) else [(tag, txt)]

    def _strip_punctuation(self, text):
        terminal_punctuation = '(){}[],~|":&-<>.'
        text = text.strip(terminal_punctuation)
        return text.strip()

    def _strip_dates(self, text):
        # this should still make it an invalid date
        # text = text[3:] if text.startswith('NaN') else text
        def try_format(fmt):
            try:
                d = datetime.strptime(text, fmt)
            except:
                return False
            return True

        try:
            d = dateparser.parse(text)
            return ''
        except ValueError:
            pass

        known_formats = ['%d/%m/%Y [%H:%M:%S:%f]', '%H:%M:%S%f']
        tests = [try_format(kf) for kf in known_formats]
        return '' if sum(tests) > 0 else text

    def _strip_scales(self, text):
        # '1:100:000'
        scale_pttn = ur"(1:[\d]{0,}(,[\d]{3}){1,})"
        m = match(text, scale_pttn)
        if m:
            return ''
        return text

    def _strip_excludes(self, match_type, tag, text):
        # TODO: how to handle the excludes for skipping
        #       by tag and skipping by value and what was
        #       the thinking a few months ago?

        # if it came from any known elem/attrib
        if any([t.lower() in tag.lower() for t in self.tag_excludes]):
            return ''

        # if it's a url, must equal an item
        if match_type == 'url':
            if text in self.equality_excludes:
                # equality only
                return ''
            return text

        # if it's *not* a url and contains any of these patterns
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

    def _verify_urn(self, potential_urn):
        # not much point to this but we're just going to leave it
        pttn = re.compile(
            ur'^([a-z0-9.#]{0,}:([a-z0-9][a-z0-9.-]{0,31}):[a-z0-9A-Z_()+,-.:=@;$!*\'%/?#\[\]]+)',
            re.IGNORECASE
        )
        m = match(potential_urn, pttn)
        return potential_urn if m else ''

    def _verify_cool_uri(self, potential_uri):
        parts = potential_uri.split('/')
        if len(parts) < 2:
            return ''

        # it should start with a slash or end with a filename
        # that's not really an accurate understanding of the things
        # they are route paths, non-unique and are difficult
        # to categorize given how badly we put things in the xml
        starts_with = '/' == potential_uri[0]
        ends_with = len(parts[-1].split('.')) > 1 or '/' == potential_uri[-1]
        if not starts_with or not ends_with:
            return ''
        return potential_uri

    def _verify_url(self, potential_url):
        # ugh
        if 'mailto:' in potential_url:
            return ''

        # is it a urn?
        pttn = re.compile(
            ur'^([a-z0-9]{0,}:[a-z0-9][a-z0-9-]{0,31}:[a-z0-9()+,\-.:=@;$_!*\'%/?#\[\]]+)',
            re.IGNORECASE
        )
        urn_m = match(potential_url, pttn)
        if urn_m:
            return ''

        # does it even have a scheme?
        try:
            u = uparse(potential_url, rule='URI')
            if not u.get('scheme'):
                # will consider the leading blob of a URN
                # a scheme even if we don't so this is not
                # 100% reliable
                return ''

            parts = potential_url.split(':', 1)
            if not parts[1].startswith('/') or len(parts) < 2:
                # so if it's our false urn scheme, we
                # say it has to be :// or it's not a url
                # and it has to have a split
                return ''
        except:
            return ''

        pttn = re.compile(ur"""(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))""", re.IGNORECASE)
        m = match(potential_url, pttn)
        if not m:
            return ''
        return potential_url

    def _extract_url(self, text):
        # but really first, is it a urn?
        text = self._verify_url(text)
        if not text:
            return '', '', []
        url = self._tidy_text(unquote(text))
        base_url, values = break_url(url)
        values = values.split(' ') + [base_url] if base_url else []

        # we're just running with a hack
        if url == 'http://dx.doi.org':
            return '', '', []

        if 'dx.doi.org' in base_url:
            t = 'doi'
        elif 'hdl.handle.net' in base_url:
            t = 'hdl'
        else:
            t = 'url'

        # return the original extracted url, tag, and the values plus
        # the base_url for more extracting
        return url, t, filter(None, [self._tidy_text(v) for v in values])

    def _extract_identifiers(self, text):
        # make sure it's not a date first
        text = self._strip_dates(text)
        if not text:
            yield '', ''
        for pattern_type, pattern in _pattern_set:
            m = match(text, pattern)
            if not m:
                continue

            # if the pattern type doesn't match the
            # verification ie urn is not actually urn
            # bounce (this is mostly for urls)
            urn_verified = self._verify_urn(m)
            is_urn = urn_verified != ''
            if urn_verified:
                yield 'urn', m

            if pattern_type == 'urn' and not is_urn:
                continue

            # NOTE: this should be a bit of dead twig code
            url_verified = self._verify_url(m)
            is_url = url_verified.strip() != ''
            if is_url and not is_urn:
                if 'dx.doi.org' in m:
                    t = 'doi'
                elif 'hdl.handle.net' in m:
                    t = 'hdl'
                else:
                    t = 'url'
                yield t, m

            if pattern_type == 'url' and not is_url:
                continue

            m = self._tidy_text(m)
            if not m:
                continue
            yield pattern_type, m

    def _check(self, comparison_identifier, arr):
        return len([a for a in arr if a.has(comparison_identifier)]) > 0

    def process_text(self):
        def _append(potential_identifier):
            # clean it up (make sure it's still a good thing)
            # before checking against knowns and appending
            cleaned_text = self._tidy_text(potential_identifier.potential_identifier) \
                if potential_identifier.extraction_type != 'rule_set' and \
                potential_identifier.match_type != 'text' else \
                potential_identifier.potential_identifier

            if cleaned_text:
                potential_identifier.potential_identifier = cleaned_text

            if cleaned_text and not self._check(
                    cleaned_text, self.identifieds):
                self.identifieds.append(potential_identifier)

            if not self._check(
                    potential_identifier.original_text, self.seen_texts):
                self.texts.append((potential_identifier.tag, cleaned_text))
                self.seen_texts.append(potential_identifier)

        def _urlify(potential_url):
            url, utype, values = self._extract_url(potential_url)
            values = [v for v in values if not self._check(v, self.seen_texts)]
            self.texts += list(iter(izip([tag] * len(values), values)))

            if url and not self._check(url, self.identifieds) \
                    and not self._check(url, self.seen_texts):
                _append(Identifier(tag, 'extract', utype, text, url))

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

            # check the tag against the rule set
            # we don't need to worry about xpaths
            # just a bit of string matching - we've
            # extracted the tags
            if any(r[1] in tag for r in _rule_set):
                # see if it matches a pattern
                # better to know it's a doi or url

                # the url
                _urlify(text)

                # anything else
                for match_type, match_text in self._extract_identifiers(text):
                    if not match_type and not match_text:
                        continue
                    # add it if it matches any pattern
                    _append(Identifier(
                        tag, 'rule_set', match_type, text, match_text))

                # if nothing else is a match, just add the text, as is
                # it is not tracking the type of the rule, fyi
                _append(Identifier(tag, 'rule_set', 'text', text, text))

            # check if the text is a url
            _urlify(text)

            # check if it's a cool uri
            uri_verified = self._verify_cool_uri(text)
            if uri_verified:
                _append(Identifier(tag, 'extract', 'cooluri', text, text))

            # now run the OTHER regex
            for match_type, match_text in self._extract_identifiers(text):
                if not match_type and not match_text:
                    continue
                _append(Identifier(tag, 'regex', match_type, text, match_text))

        # exclude from here
        for i, j in enumerate(self.identifieds):
            # type tag text
            text = self._strip_excludes(
                j.match_type, j.tag, j.potential_identifier)
            if text:
                yield j


'''
urn examples
gov.noaa.ngdc.mgg.geophysics:G01442
urn:ogc:def:crs:EPSG::5715

different hash ids in one iso:
http://catalog.data.gov/harvest/object/5e8cda58-9ea1-4038-9a11-98088f8749fa

'''
