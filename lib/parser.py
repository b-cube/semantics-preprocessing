from lxml import etree
import urllib2
import urlparse

class Parser():
    '''
    This class contains helper methods to parse XML documents.
    '''

    def __init__(self, url):
        try:
            if url.startswith('http') or url.startswith('ftp'):
                self.data = urllib2.urlopen(url).read()
            else:
                self.data = open(url).read()
        except:
            print "The url could not be openned"
            return None
        self._parse()
        self.url = url

    def _parse(self):
        '''
        This method parses the xml document and stores all the namespaces
        found in self.ns, not to be confused with the namespaces used by
        the ontology. This namespaces are used later to match elements
        in the document.
        '''
        try:
            self.doc = etree.fromstring(self.data)
        except:
            print "The XML is malformed or truncated"
            self.doc = None
        ns = []
        match = re.findall("xmlns.*\"(.*?)\"", self.data)
        for namespace in match:
            if namespace.startswith("http"):
                ns.append("{" + namespace + "}")
        self.ns = set()
        self.default_ns = ns[0]
        self.ns.update(ns)
        self.data = None  # No longer needed.

    def find_node(self, nanmespaces, element, tag):
        '''
        Finds elements from the root documents. Namespaces can vary therefore
        an array of their possible forms is used in the matching function.
        '''
        if element is None:
            element = self.doc
        for ns in nanmespaces:
            if ns.startswith("http"):
                ns = '{' + ns + '}'
            found = element.findall(ns+tag)
            if found is not None:
                return found
            else:
                continue
        return None

    def find(self, tag):
        '''
        Finds elements based on the default namespace set and the document root
        '''
        found = self.doc.findall(self.default_ns+tag)
        if found is not None:
            return found
        else:
            return None

    def get_namespaces(self):
        '''
        returns a list with the document's namespaces
        '''
        doc_ns = []
        for ns in self.ns:
            doc_ns.append(ns[1:-1])
        return doc_ns

    def get_document_namespaces(self):
        '''
        Pull all of the namespaces in the source document
        and generate a list of tuples (prefix, URI) to dict
        '''

        return dict(self.doc.xpath('/*/namespace::*'))