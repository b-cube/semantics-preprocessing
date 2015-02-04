from lxml import etree
import re

class Parser():
    '''
    This class contains helper methods to parse XML documents.


    NOTE: from b-cube/semantics, modified to use in-memory
          xml sources and (I suspect) encoding issues   

          (basically no longer from b-cube/semantics)
    '''

    def __init__(self, string_to_parse, encoding='utf-8'):
        #this is a horror show of nutch and cdata line breaks.
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
        except:
            print "The XML is malformed or truncated"
            self.xml = None

        self._namespaces = self._get_document_namespaces()

    def find_text_nodes(self, exclude_descriptors=[]):
        '''
        pull ANY node with a text() and return the node text() 
        and the xpath trace back up to root

        if exclude_descriptors, then drop any text() node found
            (it is already parsed as part of the basic service 
            description) in the namespaced xpath of the provided list
        
        it's a tuple (text, xpath)

        TODO: it needs some understanding of the relationships
        '''
        text_nodes = []
        for elem in self.xml.iter():
            if elem.text:
                t = elem.text.strip()
                if t:
                    tags = [elem.tag] + [e.tag for e in elem.iterancestors()]
                    tags.reverse()
                    text_nodes.append((t, '/'.join(tags)))

        if exclude_descriptors:
            text_nodes = [t for t in text_nodes if t[1] not in exclude_descriptors]

        return text_nodes

    def find_attributes(self):
        '''
        it's a tuple (text, xpath)
        '''

        #TODO: update to manage the relationships (see wms bounding box)
        attributes = []
        for elem in self.xml.iter():
            if elem.attrib:
                tags = [elem.tag] + [e.tag for e in elem.iterancestors()]
                tags.reverse()

                for k, v in elem.attrib.iteritems():
                    if v.strip():
                        attributes.append((v, '/'.join(tags) + '/@' + k))

        return attributes

    def find(self, xpath):
        '''
        finds any element that matches the xpath
        '''
        return self.doc.findall(xpath)

    def _get_document_namespaces(self):
        '''
        Pull all of the namespaces in the source document
        and generate a list of tuples (prefix, URI) to dict
        '''
        return dict(self.xml.xpath('/*/namespace::*'))

    def _remap_namespaced_xpaths(self, xpath):
        '''
        so we have this:
            {http://www.opengis.net/wms}WMS_Capabilities{.....}.../'
        and we need this:
            wms:WMS_Capabilities, ns={'wms': 'http://www.opengis.net/wms'}

        for the actual querying (replace the '{ns}' with 'prefix:')

        and we don't really care for storage - we care for this path, this query
        '''
        for prefix, ns in self._namespaces.iteritems();
            wrapped_ns = '{%s}' % ns
            xpath = xpath.replace(wrapped_ns, prefix + ':')

        return xpath







