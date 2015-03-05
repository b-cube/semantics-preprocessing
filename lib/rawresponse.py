import re


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

    def _extract_from_cdata(self):
        pttn = u'^<!\[CDATA\[(.*?)\]\]>$'

        # unicode escape for solr (cdata pattern matching fails without)
        raw_content = self.response.encode('unicode_escape')

        m = re.search(pttn, raw_content)

        assert m, 'Failed to extract from CDATA'

        self.content = m.group(1)

    def _strip_invalid_start(self):
        '''
        execute after CDATA extract
        '''
        self.content = self.content[self.content.index('<'):]

    def _strip_whitespace(self):
        self.content = self.content.replace('\\n', ' ').replace('\\t', ' ')

    def clean_raw_content(self):
        '''
        other than _extract_from_cdata, execute
        the clean-up methods (remove html, remove
            newline, remove unicode cruft)
        '''
        self._extract_from_cdata()
        self._strip_invalid_start()
        self._strip_whitespace()

        return self.content
