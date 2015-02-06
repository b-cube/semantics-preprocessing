from lxml import etree
import re
from HTMLParser import HTMLParser

class Parser():
    '''
    This class contains helper methods to parse XML documents.


    NOTE: from b-cube/semantics, modified to use in-memory
          xml sources and (I suspect) encoding issues   

          (basically no longer from b-cube/semantics)
    '''

    def __init__(self, string_to_parse, encoding='utf-8'):
        #there is some encoding issue somewhere around solr/nutch 
        #that should be handled better than this
        self._string = string_to_parse.replace('\\n', ' ')
        self._encoding = encoding
        self._parse()

    def _parse(self):
        '''
        parse the xml, optional encoding
        '''
        parser = etree.XMLParser(encoding=self._encoding, remove_blank_text=True)

        try:
            self.xml = etree.fromstring(self._string, parser)
        except Exception as ex:
            print ex
            self.xml = None

        self._namespaces = self._get_document_namespaces()
        self._strip_html()

    def find(self, xpath):
        '''
        finds any element that matches the xpath
        '''
        if self._namespaces:
            xpath = self._remap_namespaced_xpaths(xpath)
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
            atts = self._parse_node_attributes(elem, exclude_descriptors)

            if '/'.join(tags) not in exclude_descriptors and (atts or t):
                nodes.append((t, '/'.join(tags), atts))

        return nodes

    def _parse_node_attributes(self, node, exclude_descriptors=[]):
        '''
        return any attributes for a node
        '''
        if not node.attrib:
            return None

        tags = [node.tag] + [e.tag for e in node.iterancestors()]
        tags.reverse()

        attributes = []
        for k, v in node.attrib.iteritems():
            attr_tag = '/'.join(tags) + '/@' + k
            if v.strip() and attr_tag not in exclude_descriptors:
                attributes.append((v, attr_tag))

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
        namespaces = dict(self.xml.xpath('/*/namespace::*'))
        if None in namespaces:
            namespaces['default'] = namespaces[None]
            del namespaces[None]
        return namespaces

    def _remap_namespaced_xpaths(self, xpath):
        '''
        so we have this:
            {http://www.opengis.net/wms}WMS_Capabilities{.....}.../'
        and we need this:
            wms:WMS_Capabilities, ns={'wms': 'http://www.opengis.net/wms'}

        for the actual querying (replace the '{ns}' with 'prefix:')

        and we don't really care for storage - we care for this path, this query
        '''
        for prefix, ns in self._namespaces.iteritems():
            wrapped_ns = '{%s}' % ns
            xpath = xpath.replace(wrapped_ns, prefix + ':')
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

        print etree.tostring(self.xml, pretty_print=True)

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


