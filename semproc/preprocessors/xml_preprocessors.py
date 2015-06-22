from semproc.base_preprocessors import BaseReader
from semproc.utils import generate_qualified_xpath


class XmlReader(BaseReader):
    '''
    a very basic processor for any valid xml
    response that is not identified (or not identified
        as having a known processor) but should be
    retained in the system, ie. how to model no's
    '''

    def _parse_attributes(self, elem, tags, ignore_root=True):
        if not elem.attrib:
            return []

        atts = []
        for k, v in elem.attrib.iteritems():
            att_tags = tags + ['@' + k]
            if v.strip():
                atts.append({
                    "xpath": '/'.join(att_tags),
                    "value": v.strip()
                })

        return atts

    def parse(self):
        '''
        where we have no service info, no endpoints
        and it's basically just the text and attribute bits
        '''
        # run through the nodes
        # making sure we also pull the attribute information
        self.description = {}
        nodes = []
        for elem in self.parser.xml.iter():
            t = elem.text.strip() if elem.text else ''
            tags = generate_qualified_xpath(elem, False)

            atts = self._parse_attributes(elem, tags)
            if atts:
                nodes += atts

            if t:
                nodes.append({
                    "xpath": '/'.join(tags),
                    "value": t
                })

        self.description['nodes'] = nodes
