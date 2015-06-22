# import sys
from semproc.preprocessors import Processor
from semproc.xml_utils import extract_attrib, extract_elem
from semproc.utils import tidy_dict
from semproc.preprocessors.iso_preprocessors import MxParser
from semproc.preprocessors.metadata_preprocessors import FgdcItemReader, DifItemReader


class CswReader(Processor):

    def _parse_results_set_info(self):
        result_elem = extract_elem(self.parser.xml, ['SearchResults'])

        self.total = extract_attrib(result_elem, ['@numberOfRecordsMatched'])
        self.subtotal = extract_attrib(result_elem, ['@numberOfRecordsReturned'])
        self.schema = extract_attrib(result_elem, ['@recordSchema'])

    def parse(self):
        self.description = {}
        self._parse_results_set_info()
        self.description['total'] = self.total
        self.description['subtotal'] = self.subtotal
        self.description['schema'] = self.schema

        if self.parent_url:
            # TODO: consider making this a sha
            self.description['childOf'] = self.parent_url

        if 'resultset' in self.identify:
            self.description['children'] = self._parse_children(self.schema)

        self.description = tidy_dict(self.description)

    def _parse_children(self, dialect):
        children = []
        result_elem = extract_elem(self.parser.xml, ['SearchResults'])
        for child in result_elem.iterchildren():
            item = self._parse_child(child, dialect)
            if item:
                children.append(item)
        return children

    def _parse_child(self, child, dialect):
        if dialect == 'http://www.isotc211.org/2005/gmd':
            reader = MxParser(child)
            return reader.parse()
        elif dialect == 'http://gcmd.gsfc.nasa.gov/Aboutus/xml/dif/':
            reader = DifItemReader(child)
            return reader.parse_item()
        elif dialect == 'http://www.opengis.net/cat/csw/csdgm':
            reader = FgdcItemReader(child)
            return reader.parse_item()
        else:
            return {}
