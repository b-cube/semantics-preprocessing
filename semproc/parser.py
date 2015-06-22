from lxml import etree


class Parser():
    '''
    not concerned about namespaces or querying

    note: these could merge at some point
    '''
    def __init__(self, text):
        try:
            self.text = text.encode('unicode_escape')
        except UnicodeDecodeError:
            # TODO: this should be somewhere else and also maybe not this
            self.text = text.decode('utf-8', 'replace').encode('unicode_escape')
        self.parser = etree.XMLParser(
            remove_blank_text=True,
            remove_comments=True,
            recover=True,
            remove_pis=True,
            ns_clean=True
        )
        self._parse()
        self._extract_namespaces()

    def _parse(self):
        try:
            self.xml = etree.fromstring(self.text, parser=self.parser)
        except Exception as ex:
            print ex
            raise ex

    def _extract_namespaces(self):
        '''
        Pull all of the namespaces in the source document
        and generate a list of tuples (prefix, URI) to dict
        '''
        if self.xml is None:
            self.namespaces = {}
            return

        document_namespaces = dict(self.xml.xpath('/*/namespace::*'))
        if None in document_namespaces:
            document_namespaces['default'] = document_namespaces[None]
            del document_namespaces[None]

        # now run through any child namespace issues
        all_namespaces = self.xml.xpath('//namespace::*')
        for i, ns in enumerate(all_namespaces):
            if ns[1] in document_namespaces.values():
                continue
            new_key = ns[0] if ns[0] else 'default%s' % i
            document_namespaces[new_key] = ns[1]

        self.namespaces = document_namespaces
