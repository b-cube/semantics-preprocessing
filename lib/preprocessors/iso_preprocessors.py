from lib.parser import BasicParser
from lib.utils import tidy_dict
from lib.preprocessors.iso_helpers import parse_identification_info
from lib.preprocessors.iso_helpers import parse_distribution
from lib.preprocessors.iso_helpers import parse_responsibleparty
from lib.xml_utils import extract_item, extract_items
from lib.xml_utils import extract_elem, extract_elems
from lib.xml_utils import extract_attrib, extract_attribs


'''
NOTE: for all of the ISO parsers, I am using the local-path "trick". It is a known
      performance hit but the harmonization across -1, -2, -3, INSPIRE, data.gov,
      whatever, is a not insignificant chunk of dev time as well. I am willing to
      make this tradeoff given the ETL workflow.
'''


class IsoParser():
    '''
    this assumes we're reading from a response as the root
    and will iterate over whatever that flavor of iso is:
        data series with some mx (with some sv)
        service identification
        mi/md
    '''
    def __init__(self, text, identity):
        self.text = text
        self.identity = identity

        # parse
        self.parser = BasicParser(text)

    def parse(self):
        '''
        run the routing
        '''

        if not self.identity:
            # we're going to have to sort it out
            self.identity = {}

        protocol = self.identity.get('protocol')
        if protocol == 'Data Series':
            # run the set
            iso = DsParser(self.parser.xml)
        elif protocol == 'ServiceIdentification':
            # run that
            iso = SrvParser(self.parser.xml)
        elif protocol == 'Metadata':
            # it's a mi/md so run that
            iso = MxParser(self.parser.xml)

        return iso.parse()


class MxParser():
    '''
    parse an mi or md element (as whole record or some csw/oai-pmh/ds child)
    '''

    def __init__(self, elem):
        ''' starting at Mx_Metadata
        which can be within a DS composedOf block, within a
        CSW result set, as the series descriptor for a dataseries
        or part of some other catalog service
        '''
        self.elem = elem

    def parse(self):
        '''
        from the root node, parse:
            identification (title, abstract, point of contact, keywords, extent)
            if identificationInfo contains SV_ServiceIdentification, add as child
            distribution info
        '''
        mx = {}

        id_elem = extract_elem(self.elem, ['identificationInfo', 'MD_DataIdentification'])
        if id_elem is not None:
            identification = parse_identification_info(id_elem)
            mx.update(identification)

        # point of contact from the root node and this might be an issue
        # in things like the -1/-3 from ngdc so try for an idinfo blob
        poc_elem = extract_elem(self.elem, [
            'identificationInfo', 'MD_DataIdentification', 'pointOfContact', 'CI_ResponsibleParty'])
        if poc_elem is None:
            # and if that fails try for the root-level contact=
            poc_elem = extract_elem(self.elem, ['contact', 'CI_ResponsibleParty'])

        if poc_elem is not None:
            mx['contact'] = parse_responsibleparty(poc_elem)

        # check for the service elements
        service_elems = extract_elems(self.elem, ['identificationInfo', 'SV_ServiceIdentification'])
        mx['services'] = []
        for service_elem in service_elems:
            sv = SrvParser(service_elem)
            mx['services'].append(sv.parse())

        dist_elems = extract_elems(self.elem, ['distributionInfo'])
        mx['endpoints'] = []
        for dist_elem in dist_elems:
            mx['endpoints'] = parse_distribution(dist_elem)

        mx = tidy_dict(mx)
        return mx


class SrvParser():
    '''
    read a service identification element as
    19119 or the embedded md/mi element
    '''
    def __init__(self, elem):
        self.elem = elem

    def _handle_parameter(self, elem):
        ''' parse an sv_parameter element '''
        param = {}

        param['name'] = extract_item(
            elem, ['name', 'aName', 'CharacterString'])
        param['inputType'] = extract_item(
            elem, ['name', 'attributeType', 'TypeName', 'aName', 'CharacterString'])
        param['direction'] = extract_item(
            elem, ['direction', 'SV_ParameterDirection'])
        param['optional'] = extract_item(
            elem, ['optionality', 'CharacterString'])
        param['cardinality'] = extract_item(
            elem, ['repeatability', 'Boolean'])
        param['valueType'] = extract_item(
            elem, ['valueType', 'TypeName', 'aName', 'CharacterString'])

        return param

    def _handle_operations(self):
        elems = extract_elems(self.elem, ['containsOperations', 'SV_OperationMetadata'])

        ops = []
        for e in elems:
            op = {}
            op['name'] = extract_item(e, ['operationName', 'CharacterString'])
            op['method'] = extract_attrib(e, ['DCP', 'DCPList', '@codeListValue'])
            op['url'] = extract_item(e, ['connectPoint', 'CI_OnlineResource', 'linkage', 'URL'])
            op['parameters'] = [self._handle_parameter(pe) for pe in
                                extract_elems(e, ['parameters', 'SV_Parameter'])]
            ops.append(op)

        return ops

    def parse(self):
        # elem = extract_elem(self.elem, ['SV_ServiceIdentification'])
        if self.elem is None:
            return None

        service = parse_identification_info(self.elem)

        service['operations'] = self._handle_operations()

        return service


class DsParser():
    '''
    the parent ds parsing (as an mi/md record itself)
    plus the nested children in composedOf
    '''
    def __init__(self, elem):
        self.elem = elem

    # TODO: check on mi vs md here
    def parse(self):
        # get the series
        md = extract_elem(self.elem, ['seriesMetadata', 'MD_Metadata'])
        if md is None:
            return None

        md_parser = MxParser(md)
        md_dict = md_parser.parse()
        md_dict['children'] = []

        # get the children
        children = extract_elems(
            self.elem, ['composedOf', 'DS_DataSet', 'has', 'MD_Metadata'])
        for child in children:
            child_parser = MxParser(child)
            child_dict = child_parser.parse()
            md_dict['children'].append(child_dict)

        return md_dict
