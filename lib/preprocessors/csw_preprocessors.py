import sys
from lib.base_preprocessors import BaseReader
from lib.xml_utils import extract_attrib, extract_elem
from lib.utils import tidy_dict
from lib.preprocessors.iso_preprocessors import IsoParser, MxParser
from lib.preprocessors.metadata_preprocessors import FgdcReader, DcReader, DifReader


class CswReader(BaseReader):
    def __init__(self, response, url, version='2.0.2'):
        self._response = response
        self._url = url
        self._load_xml()

    def parse_results_set_info(self):
        result_elem = extract_elem(self.parser.xml, ['SearchResults'])

        self.total = extract_attrib(result_elem, ['@numberOfRecordsMatched'])
        self.subtotal = extract_attrib(result_elem, ['@numberOfRecordsReturned'])
        self.schema = extract_attrib(result_elem, ['@recordSchema'])

    def parse(self):
        self.parse_results_set_info()
        return self.parse_result_set()

    def parse_result_set(self):
        # make sure the info call is made first
        results = []
        if self.parser.xml is None:
            return results

        result_elem = extract_elem(self.parser.xml, ['SearchResults'])
        for child in result_elem.iter():
            # let's parse based on the recordSchema value
            if self.schema == 'http://www.isotc211.org/2005/gmd':
                reader = MxParser(child)
                results.append(reader.parse())
            elif self.schema == 'http://gcmd.gsfc.nasa.gov/Aboutus/xml/dif/':
                reader = DifReader()
                results.append(reader.parse_item(child))
            elif self.schema == 'http://www.opengis.net/cat/csw/csdgm':
                reader = FgdcReader(child)
                results.append(reader.parse_item())

        return results
