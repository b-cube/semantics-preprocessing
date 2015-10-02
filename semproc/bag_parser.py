from semproc.parser import Parser
from bs4 import BeautifulSoup
import re
from semproc.utils import unquote


# TODO: finish this


class BagParser():
    def __init__(self, text, handle_html=False, include_html_hrefs=False):
        self.text = text
        self.parser = Parser(text)

        self.handle_html = handle_html
        self.include_html_hrefs = include_html_hrefs

    def _un_htmlify(self, text):
        def _handle_bad_html(s):
            pttn = re.compile('<|>')
            return pttn.sub(' ', s)

        try:
            soup = BeautifulSoup(text.strip())
        except UserWarning:
            return ''

        # get all of the text and any a/@href values
        texts = [_handle_bad_html(t.strip('"'))
                 for t in soup.find_all(text=True)]
        if self.include_html_hrefs:
            texts += [unquote(a['href'])
                      for a in soup.find_all('a') if 'href' in a.attrs]

        try:
            text = ' '.join(texts)
        except:
            raise
        return text

    def strip_text(self, exclude_tags=[]):
        # exclude_patterns = list of element tag strings
        # to ignore (ie schemaLocation, etc)

        def _extract_tag(t):
            if not t:
                return
            return t.split('}')[-1]

        def _taggify(e):
            tags = [e.tag] + [m.tag for m in e.iterancestors()]
            tags.reverse()

            try:
                return [_extract_tag(t) for t in tags]
            except:
                return []

        for elem in self.parser.xml.iter():
            t = elem.text.strip() if elem.text else ''
            tags = _taggify(elem)

            if [e for e in exclude_tags if e in tags]:
                continue

            if t:
                if self.handle_html and (
                        (t.startswith('<') and t.endswith('>'))
                        or ('<' in t or '>' in t)):
                    t = self._un_htmlify(t)
                if t:
                    yield ('/'.join(tags), t)

            for k, v in elem.attrib.iteritems():
                if v.strip():
                    v = BeautifulSoup(v.strip())
                    yield ('/'.join(tags + ['@' + _extract_tag(k)]), v.text)
