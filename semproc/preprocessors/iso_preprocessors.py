from semproc.parser import Parser
from semproc.utils import tidy_dict
from semproc.preprocessors.iso_helpers import parse_identification_info
from semproc.preprocessors.iso_helpers import parse_distribution
from semproc.preprocessors.iso_helpers import parse_responsibleparty
from semproc.xml_utils import extract_item
from semproc.xml_utils import extract_elem, extract_elems
from semproc.xml_utils import extract_attrib
from semproc.utils import generate_sha_urn, generate_uuid_urn
from rdflib.namespace import DC, DCTERMS, FOAF, XSD, OWL
from itertools import chain


'''
NOTE: for all of the ISO parsers, I am using the local-path "trick". It is a known
      performance hit but the harmonization across -1, -2, -3, INSPIRE, data.gov,
      whatever, is a not insignificant chunk of dev time as well. I am willing to
      make this tradeoff given the ETL workflow.
'''


class IsoReader():
    '''
    this assumes we're reading from a response as the root
    and will iterate over whatever that flavor of iso is:
        data series with some mx (with some sv)
        service identification
        mi/md
    '''
    _technical_debt = {
        'bcube': 'http://purl.org/BCube/#',
        'vcard': 'http://www.w3.org/TR/vcard-rdf/#',
        'esip': 'http://purl.org/esip/#',
        'vivo': 'http://vivo.ufl.edu/ontology/vivo-ufl/#',
        'bibo': 'http://purl.org/ontology/bibo/#',
        'dcat': 'http://www.w3.org/TR/vocab-dcat/#',
        'dc': str(DC),
        'dct': str(DCTERMS),
        'foaf': str(FOAF),
        'xsd': str(XSD),
        'owl': str(OWL)
    }

    def __init__(self, identity, text, url, harvest_date):
        self.text = text
        self.identity = identity
        self.url = url
        self.harvest_date = harvest_date

        # parse
        self.parser = Parser(text)
        self.parse()

    def parse(self):
        '''
        run the routing
        '''

        if not self.identity:
            # we're going to have to sort it out
            self.identity = {}

        metadata = self.identity.get('metadata', {})
        if not metadata:
            return {}

        metadata_type = metadata.get('name', '')
        if not metadata_type:
            return {}

        # TODO: this is unlikely to be correct, given the ds record
        #       but we're not going there just yet
        # TODO: deal with conformsTo (multiple schemaLocations, etc)
        catalog_record = {
            "object_id": generate_sha_urn(self.url),
            "url": self.url,
            "harvestDate": self.harvest_date,
            "conformsTo": extract_attrib(self.parser.xml, ['@schemaLocation'])
        }

        if metadata_type == 'Data Series':
            # run the set
            self.reader = DsParser(self.parser.xml, catalog_record)
        elif metadata_type == '19119':
            # run that
            self.reader = SrvParser(self.parser.xml, catalog_record)
        elif metadata_type == '19115':
            # it's a mi/md so run that
            self.reader = MxParser(self.parser.xml, catalog_record)

        self.reader.parse()
        # pass it back up the chain a bit
        self.description = self.reader.description


class MxParser(object):
    '''
    parse an mi or md element (as whole record or some csw/oai-pmh/ds child)
    '''

    def __init__(self, elem, catalog_record):
        ''' starting at Mx_Metadata
        which can be within a DS composedOf block, within a
        CSW result set, as the series descriptor for a dataseries
        or part of some other catalog service
        '''
        self.elem = elem
        self.output = {"catalog_record": catalog_record, "relationships": []}

    def parse(self):
        '''
        from the root node, parse:
            identification (title, abstract, point of contact, keywords, extent)
            if identificationInfo contains SV_ServiceIdentification, add as child
            distribution info
        '''
        id_elem = extract_elem(self.elem, ['identificationInfo', 'MD_DataIdentification'])
        if id_elem is not None:
            identification = parse_identification_info(id_elem)
            identification['dataset']['relationships'].append({
                "relate": "description",
                "object_id": self.output['catalog_record']['object_id']
            })
            self.output.update(identification)
            self.output['relationships'].append({
                "relate": "primaryTopic",
                "object_id": identification['dataset']['object_id']
            })

        # point of contact from the root node and this might be an issue
        # in things like the -1/-3 from ngdc so try for an idinfo blob
        poc_elem = extract_elem(self.elem, [
            'identificationInfo', 'MD_DataIdentification', 'pointOfContact', 'CI_ResponsibleParty'])
        if poc_elem is None:
            # and if that fails try for the root-level contact
            poc_elem = extract_elem(self.elem, ['contact', 'CI_ResponsibleParty'])

        # TODO: point of contact is not necessarily the publisher
        if poc_elem is not None:
            poc = parse_responsibleparty(poc_elem)
            self.output['publisher'] = {
                "object_id": generate_uuid_urn(),
                "name": poc.get('organization_name', ''),
                "location": ', '.join([poc['contact'].get('city', ''), poc['contact'].get('country', '')]) if 'contact' in poc else ''
            }
            self.output['dataset']['relationships'].append({
                "relate": "publisher",
                "object_id": self.output['publisher']['object_id']
            })

        # TODO: removing this until we have a definition for SERVICE
        # # check for the service elements
        # service_elems = extract_elems(self.elem, ['identificationInfo', 'SV_ServiceIdentification'])
        # self.description['services'] = []
        # for service_elem in service_elems:
        #     sv = SrvParser(service_elem)
        #     self.description['services'].append(sv.parse())

        dist_elems = extract_elems(self.elem, ['distributionInfo'])
        self.output['webpages'] = []
        for dist_elem in dist_elems:
            self.output['webpages'] = list(chain(self.output['webpages'], parse_distribution(dist_elem)))
        for webpage in self.output['webpages']:
            self.output['dataset']['relationships'].append({
                "relate": "relation",
                "object_id": webpage['object_id']
            })

        self.description = tidy_dict(self.output)


class SrvParser(object):
    '''
    read a service identification element as
    19119 or the embedded md/mi element
    '''
    def __init__(self, elem, catalog_record):
        self.elem = elem
        self.output = {"catalog_record": catalog_record}

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
            self.description = {}
            return

        self.description = parse_identification_info(self.elem)

        self.description['operations'] = self._handle_operations()

        self.description = tidy_dict(self.description)


class DsParser(object):
    '''
    the parent ds parsing (as an mi/md record itself)
    plus the nested children in composedOf
    '''
    def __init__(self, elem, catalog_record):
        self.elem = elem
        self.output = {"catalog_record": catalog_record}

    # TODO: check on mi vs md here
    def parse(self):
        # get the series
        self.description = {}
        md = extract_elem(self.elem, ['seriesMetadata', 'MD_Metadata'])
        if md is None:
            return

        md_parser = MxParser(md)
        md_parser.parse()
        self.description = md_parser.description
        self.description['children'] = []

        # get the children
        children = extract_elems(
            self.elem, ['composedOf', 'DS_DataSet', 'has', 'MD_Metadata'])
        for child in children:
            child_parser = MxParser(child)
            child_parser.parse()
            if child_parser.description:
                self.description['children'].append(child_parser.description)

        self.description = tidy_dict(self.description)
