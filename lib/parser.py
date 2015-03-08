from lxml import etree
from HTMLParser import HTMLParser
import traceback
import sys


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
        parser = etree.XMLParser(encoding=self._encoding)

        try:
            self.xml = etree.fromstring(self._string, parser)
        except Exception as ex:
            # print self._string[0:50]
            print ex
            # traceback.print_exc(file=sys.stdout)
            self.xml = None

        self._namespaces = self._get_document_namespaces()
        self._strip_html()

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
                nodes.append({
                    "text": t,
                    "xpath": '/'.join(tags),
                    "attributes": atts
                })

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
