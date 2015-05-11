from lxml import etree
from HTMLParser import HTMLParser
from bs4 import BeautifulSoup
import re
from lib.utils import unquote


class BasicParser():
    '''
    not concerned about namespaces or querying

    note: these could merge at some point
    '''
    def __init__(self, text, handle_html=False):
        self.text = text.encode('unicode_escape')
        self.parser = etree.XMLParser(
            remove_blank_text=True,
            remove_comments=True,
            recover=True,
            remove_pis=True
        )
        self.handle_html = handle_html

        self._parse_node_attributes

    def _parse(self):
        try:
            self.xml = etree.fromstring(self.text, parser=self.parser)
        except:
            raise

    def _un_htmlify(self, text):
        def _handle_bad_html(s):
            pttn = re.compile('<|>')
            return pttn.sub(' ', s)

        soup = BeautifulSoup(text.strip())

        # get all of the text and any a/@href values
        texts = [_handle_bad_html(t) for t in soup.find_all(text=True)] + \
            [unquote(a['href']) for a in soup.find_all('a') if 'href' in a.attrs]

        try:
            text = ' '.join(texts)
        except:
            raise
        return text

    def strip_text(self, exclude_tags=[]):
        # pull any text() and attribute. again.
        # bag of words BUT we care about where in
        # the tree it was found (just for thinking)
        # except do not care about namespace prefixed
        # why am i not stripping out the prefixes? no idea.
        # just don't want to install pparse/saxonb really
        #
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

        blobs = []
        for elem in self.xml.iter():
            t = elem.text.strip() if elem.text else ''
            tags = _taggify(elem)

            if [e for e in exclude_tags if e in tags]:
                continue

            if t:
                if self.handle_html and (
                        (t.startswith('<') and t.endswith('>'))
                        or ('<' in t or '>' in t)):
                    t = self._un_htmlify(self, t)
                blobs.append(('/'.join(tags), t))

            for k, v in elem.attrib.iteritems():
                if v.strip():
                    blobs.append(('/'.join(tags + ['@' + _extract_tag(k)]), v.strip()))

        return blobs


class Parser():
    '''
    This class contains helper methods to parse XML documents.


    NOTE: from b-cube/semantics, modified to use in-memory
          xml sources and (I suspect) encoding issues

          (basically no longer from b-cube/semantics)
    '''

    def __init__(self, string_to_parse, encoding='utf-8'):
        self._string = string_to_parse
        self._encoding = encoding
        self._parse()

    def _parse(self):
        '''
        parse the xml, optional encoding
        '''
        parser = etree.XMLParser(
            encoding=self._encoding,
            remove_blank_text=True,
            remove_comments=True,
            recover=True
        )

        try:
            self.xml = etree.fromstring(self._string, parser)
        except Exception as ex:
            print ex
            self.xml = None

        if self.xml is None:
            # try something else and wtf
            try:
                self.xml = etree.fromstring(
                    self._string,
                    parser=etree.XMLParser(encoding=self._encoding)
                )
            except Exception as ex:
                print ex
                self.xml = None
                return

        self._namespaces = self._get_document_namespaces()
        try:
            self._strip_html()
            self._strip_whitespace()
        except AttributeError:
            print 'text not writable? ', self._string[:100]

    def to_string(self):
        return etree.tostring(self.xml)

    def find(self, xpath):
        '''
        finds any element that matches the xpath
        '''
        if self._namespaces:
            xpath = self._remap_namespaced_xpaths(xpath)
            if not xpath:
                return ''
            return self.xml.xpath(xpath, namespaces=self._namespaces)
        return self.xml.xpath(xpath)

    def find_nodes(self, exclude_descriptors=[]):
        '''
        pull ANY node with a text() and/or attributes and return the node text()
        and the xpath trace back up to root

        if exclude_descriptors, then drop any text() node found
            (it is already parsed as part of the basic service
            description) in the namespaced xpath of the provided list

        it's a tuple (text, xpath, attributes)
        '''
        nodes = []
        for elem in self.xml.iter():
            t = elem.text.strip() if elem.text else ''
            tags = [elem.tag] + [e.tag for e in elem.iterancestors()]
            tags.reverse()

            # check for an assumed comment object
            if sum([isinstance(a, str) for a in tags]) != len(tags):
                continue

            atts = self._parse_node_attributes(elem, exclude_descriptors)

            if '/'.join(tags) not in exclude_descriptors and (atts or t):
                to_append = {}
                if t:
                    to_append.update({"text": t})
                if atts:
                    to_append.update({"attributes": atts})

                if not to_append:
                    # skip if no text or no attributes
                    continue

                to_append.update({"xpath": '/'.join(tags)})
                nodes.append(to_append)

        return nodes

    def _parse_node_attributes(self, node, exclude_descriptors=[], ignore_root_defs=True):
        '''
        return any attributes for a node

        if ignore_root_defs, skip any schema definitions, other
            xml-specific definitions
        '''
        if not node.attrib:
            return None

        tags = [node.tag] + [e.tag for e in node.iterancestors()]
        tags.reverse()

        attributes = []
        for k, v in node.attrib.iteritems():
            attr_tag = '/'.join(tags) + '/@' + k
            if v.strip() and attr_tag not in exclude_descriptors:
                attributes.append({"text": v, "xpath": attr_tag})

        return attributes

    def _find_attributes(self):
        '''
        it's a tuple (text, xpath)
        '''
        attributes = []
        for elem in self.xml.iter():
            attributes += self._parse_node_attributes(elem)

        return attributes

    def _get_document_namespaces(self):
        '''
        Pull all of the namespaces in the source document
        and generate a list of tuples (prefix, URI) to dict
        '''
        if self.xml is None:
            return {}

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

        return document_namespaces

    def _remap_namespaced_xpaths(self, xpath):
        '''
        so we have this:
            {http://www.opengis.net/wms}WMS_Capabilities{.....}.../'
        and we need this:
            wms:WMS_Capabilities, ns={'wms': 'http://www.opengis.net/wms'}

        for the actual querying (replace the '{ns}' with 'prefix:')

        we do care about whether the provided xpath contains
        namespaces that aren't in the namespace list! (wcs 1.0.0 & ows)

        and we don't really care for storage -
            we care for this path, this query
        '''
        # remap the fully qualified namespace to the prefix
        for prefix, ns in self._namespaces.iteritems():
            wrapped_ns = '{%s}' % ns
            xpath = xpath.replace(wrapped_ns, prefix + ':')

        # if the xpath still contains {ns} then we have a problem
        # with the xpath not being valid for the xml and we shouldn't
        # try to use it (it will just raise an invalidpath exception)
        if '{' in xpath and '}' in xpath:
            return ''

        return xpath

    def _strip_html(self):
        '''
        remove any html tags from any text chunk

        note:
            when this strips out a tags, it drops the href. not worried
            about that in this context
        '''
        for elem in self.xml.iter():
            t = elem.text.strip() if elem.text else ''
            if not t:
                continue

            hparser = TextParser()
            hparser.feed(t)
            elem.text = hparser.get_data()

    def _strip_whitespace(self):
        for elem in self.xml.iter():
            t = elem.text.strip() if elem.text else ''
            if not t:
                continue
            elem.text = ' '.join(t.split())


class TextParser(HTMLParser):
    '''
    basic html parsing for text with html-encoded tags
    '''
    def __init__(self):
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)
