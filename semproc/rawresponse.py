import re
import codecs


class RawResponse():
    '''
    container for the Solr document, unmodified

    required:
        source url
        raw_content (this should be straight from Solr,
            no modifications, encodings, etc)
        digest hash
    '''

    def __init__(self, source_url, source_content, identifier, **options):
        '''
        options:
            strip whitespace: boolean
            strip unicode escaped text: boolean
        '''
        self.identifier = identifier
        self.response = source_content
        self.url = source_url
        self.options = options

        self.content = ''

    def _strip_bom(self):
        """ return the raw (assumed) xml response without the BOM
        """
        boms = [
            codecs.BOM,
            codecs.BOM_BE,
            codecs.BOM_LE,
            codecs.BOM_UTF8,
            codecs.BOM_UTF16,
            codecs.BOM_UTF16_LE,
            codecs.BOM_UTF16_BE,
            codecs.BOM_UTF32,
            codecs.BOM_UTF32_LE,
            codecs.BOM_UTF32_BE
        ]
        content = self.content
        if not isinstance(content, unicode):
            for bom in boms:
                if content.startswith(bom):
                    content = content.replace(bom, '')
                    break

        self.content = content

    def _extract_from_cdata(self):
        pttn = u'^<!\[CDATA\[(.*?)\]\]>$'

        # unicode escape for solr (cdata pattern matching fails without)
        if not self.response.startswith('<![CDATA['):
            # and encode it for the xml parser (xml encode set, must be
            # encoded to match)
            self.content = self.response.encode('unicode_escape')
            return

        raw_content = self.response.encode('unicode_escape')

        m = re.search(pttn, raw_content)

        assert m, 'Failed to extract from CDATA (%s)' % self.identifier

        self.content = m.group(1)

    def _strip_invalid_start(self):
        '''
        execute after CDATA extract
        '''
        self.content = self.content[self.content.index('<'):]

    def _strip_whitespace(self):
        self.content = self.content.replace('\\n', ' ').replace('\\t', ' ')

        # and do any chunks of spaces
        self.content = ' '.join(self.content.split())

    def _strip_unicode_replace(self):
        '''
        remove the unicode replacement char and replace with a space
        if this generates multiple spaces, we should be okay with
        the parser.
        '''
        # remove anything that looks like \\ufffd
        # pttn = ur'[\\{2,}ufffd]'
        # self.content = re.sub(pttn, ' ', self.content)

        self.content = self.content.replace('\\\\ufffd', ' ').replace('\\ufffd', ' ')

    def _strip_greedy_encoding(self):
        '''
        enthusiastic encoding with backslashes everywhere.

        this also is behaving badly
        '''
        pttn = ur'[\\{3,}]'
        self.content = re.sub(pttn, ' ', self.content)

    def clean_raw_content(self):
        '''
        other than _extract_from_cdata, execute
        the clean-up methods (remove html, remove
            newline, remove unicode cruft)
        '''
        self._extract_from_cdata()
        self._strip_invalid_start()
        self._strip_unicode_replace()
        self._strip_whitespace()
        # self._strip_greedy_encoding()

        return self.content
