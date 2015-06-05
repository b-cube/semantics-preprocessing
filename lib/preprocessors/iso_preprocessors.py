from lib.base_preprocessors import BaseReader
from lib.utils import tidy_dict
# from lib.utils import generate_localname_xpath
from lib.preprocessors.iso_helpers import parse_identification_info
from lib.preprocessors.iso_helpers import parse_distribution
from lib.preprocessors.iso_helpers import parse_responsibleparty


def generate_localname_xpath(tags):
    return '/'.join(['*[local-name()="%s"]' % t if t not in ['*', '..', '.', '//*'] else t
                    for t in tags])


class IsoReader(BaseReader):
    '''
    basic iso reader to handle mi/md metadata
    '''
    _service_descriptors = {
        "title": "/*/{http://www.isotc211.org/2005/gmd}identificationInfo/" +
                 "{http://www.isotc211.org/2005/gmd}MD_DataIdentification/" +
                 "{http://www.isotc211.org/2005/gmd}citation/" +
                 "{http://www.isotc211.org/2005/gmd}CI_Citation/" +
                 "{http://www.isotc211.org/2005/gmd}title/" +
                 "{http://www.isotc211.org/2005/gco}CharacterString",

        "abstract": "/*/{http://www.isotc211.org/2005/gmd}identificationInfo/" +
                    "{http://www.isotc211.org/2005/gmd}MD_DataIdentification/" +
                    "{http://www.isotc211.org/2005/gmd}abstract/" +
                    "{http://www.isotc211.org/2005/gco}CharacterString",

        "contact": "/*/{http://www.isotc211.org/2005/gmd}identificationInfo/" +
                    "{http://www.isotc211.org/2005/gmd}MD_DataIdentification/" +
                    "{http://www.isotc211.org/2005/gmd}pointOfContact/" +
                    "{http://www.isotc211.org/2005/gmd}CI_ResponsibleParty/" +
                    "{http://www.isotc211.org/2005/gmd}organisationName/" +
                    "{http://www.isotc211.org/2005/gco}CharacterString",

        "rights": "/*/{http://www.isotc211.org/2005/gmd}identificationInfo/" +
                  "{http://www.isotc211.org/2005/gmd}resourceConstraints/" +
                  "{http://www.isotc211.org/2005/gmd}MD_LegalConstraints/" +
                  "{http://www.isotc211.org/2005/gmd}useLimitation/" +
                  "{http://www.isotc211.org/2005/gco}CharacterString | "
                  "/*/{http://www.isotc211.org/2005/gmd}identificationInfo/" +
                  "{http://www.isotc211.org/2005/gmd}MD_DataIdentification/" +
                  "{http://www.isotc211.org/2005/gmd}resourceConstraints/" +
                  "{http://www.isotc211.org/2005/gmd}MD_Constraints/" +
                  "{http://www.isotc211.org/2005/gmd}useLimitation/" +
                  "{http://www.isotc211.org/2005/gco}CharacterString",

        "subject": ["/*/{http://www.isotc211.org/2005/gmd}identificationInfo/" +
                    "{http://www.isotc211.org/2005/gmd}MD_DataIdentification/" +
                    "{http://www.isotc211.org/2005/gmd}descriptiveKeywords/" +
                    "{http://www.isotc211.org/2005/gmd}MD_Keywords/" +
                    "{http://www.isotc211.org/2005/gmd}keyword/" +
                    "{http://www.isotc211.org/2005/gco}CharacterString/text()",
                    "/*/{http://www.isotc211.org/2005/gmd}identificationInfo/" +
                    "{http://www.isotc211.org/2005/gmd}MD_DataIdentification/" +
                    "{http://www.isotc211.org/2005/gmd}descriptiveKeywords/" +
                    "{http://www.isotc211.org/2005/gmd}MD_Keywords/" +
                    "{http://www.isotc211.org/2005/gmd}keyword/" +
                    "{http://www.isotc211.org/2005/gmx}Anchor/text()"
                    ],

        "identifier": "(/*/{http://www.isotc211.org/2005/gmd}fileIdentifier/" +
                      "{http://www.isotc211.org/2005/gco}CharacterString | " +
                      "/*/{http://www.isotc211.org/2005/gmd}identificationInfo/" +
                      "{http://www.isotc211.org/2005/gmd}MD_DataIdentification/" +
                      "{http://www.isotc211.org/2005/gmd}citation/" +
                      "{http://www.isotc211.org/2005/gmd}CI_Citation/" +
                      "{http://www.isotc211.org/2005/gmd}identifier/" +
                      "{http://www.isotc211.org/2005/gmd}MD_Identifier/" +
                      "{http://www.isotc211.org/2005/gmd}code/" +
                      "{http://www.isotc211.org/2005/gco}CharacterString | " +
                      "/*/{http://www.isotc211.org/2005/gmd}dataSetURI/" +
                      "{http://www.isotc211.org/2005/gco}CharacterString)[1]"
    }
    _to_exclude = [
        "/*/{http://www.isotc211.org/2005/gmd}language/" +
        "{http://www.isotc211.org/2005/gco}CharacterString"
    ]

    '''
    to handle any of the valid iso distribution structures
    and, it's a tuple (url, role code as proxy for type?)

    to keep everything intact, the xpath is to the distribution
    or distributor parent elements where it should be a reasonable
    assumption to pull the two strings from the same gmd:onLine
    structure after that (and there can be more than one)
    '''
    _endpoints = [
        # for the MD_Distribution
        "/*/{http://www.isotc211.org/2005/gmd}distributionInfo/" +
        "{http://www.isotc211.org/2005/gmd}MD_Distribution/" +
        "{http://www.isotc211.org/2005/gmd}transferOptions/" +
        "{http://www.isotc211.org/2005/gmd}MD_DigitalTransferOptions/" +
        "{http://www.isotc211.org/2005/gmd}onLine",
        # and embedded in a Distributor block
        "/*/{http://www.isotc211.org/2005/gmd}distributionInfo/" +
        "{http://www.isotc211.org/2005/gmd}MD_Distribution/" +
        "{http://www.isotc211.org/2005/gmd}distributor/" +
        "{http://www.isotc211.org/2005/gmd}MD_Distributor/" +
        "{http://www.isotc211.org/2005/gmd}distributorTransferOptions/" +
        "{http://www.isotc211.org/2005/gmd}MD_DigitalTransferOptions/" +
        "{http://www.isotc211.org/2005/gmd}onLine"
    ]

    def _identify_format(self, name, version, description, url):
        '''
        from the set of things that might exist in an iso distribution,
        get a mimetype(s)
        '''
        # TODO: finish this
        return name

    def _extract_format_info(self, format_element):
        '''

        '''
        if format_element is None:
            return '', '', ''

        name_xpath = "{http://www.isotc211.org/2005/gmd}name/" + \
                     "{http://www.isotc211.org/2005/gco}CharacterString/text()"
        version_xpath = "{http://www.isotc211.org/2005/gmd}version/" + \
                        "{http://www.isotc211.org/2005/gco}CharacterString/text()"
        specification_xpath = "{http://www.isotc211.org/2005/gmd}specification/" + \
                              "{http://www.isotc211.org/2005/gco}CharacterString/text()"
        name_xpath = self.parser._remap_namespaced_xpaths(name_xpath)
        version_xpath = self.parser._remap_namespaced_xpaths(version_xpath)
        specification_xpath = self.parser._remap_namespaced_xpaths(specification_xpath)

        name_elem = format_element.xpath(name_xpath, namespaces=self.parser._namespaces)
        version_elem = format_element.xpath(version_xpath, namespaces=self.parser._namespaces)
        specification_elem = format_element.xpath(specification_xpath,
                                                  namespaces=self.parser._namespaces)

        name = next(iter(name_elem), '') if name_elem is not None else ''
        version = next(iter(version_elem), '') if version_elem is not None else ''
        specification = next(iter(specification_elem), '') if specification_elem is not None else ''

        return name, version, specification

    def return_exclude_descriptors(self):
        excluded = self._service_descriptors.values()
        return [e[1:] for e in excluded] + self._to_exclude

    def parse_endpoints(self):
        '''
        pull endpoints from the distribution element

        url, type (as download, etc, from codelist)
        '''
        url_xpath = "{http://www.isotc211.org/2005/gmd}CI_OnlineResource/" + \
                    "{http://www.isotc211.org/2005/gmd}linkage/" + \
                    "{http://www.isotc211.org/2005/gmd}URL"

        code_xpath = "{http://www.isotc211.org/2005/gmd}CI_OnlineResource/" + \
                     "{http://www.isotc211.org/2005/gmd}function/" + \
                     "{http://www.isotc211.org/2005/gmd}CI_OnLineFunctionCode/" + \
                     "@codeListValue"

        # go back up to the distributor or the distribution (don't know which!)
        format_xpath = "../../../*/{http://www.isotc211.org/2005/gmd}MD_Format"

        # we need to remap these - cannot assume that the gmd will
        # be a prefixed namespace. who knew.
        url_xpath = self.parser._remap_namespaced_xpaths(url_xpath)
        code_xpath = self.parser._remap_namespaced_xpaths(code_xpath)
        format_xpath = self.parser._remap_namespaced_xpaths(format_xpath)

        endpoints = []
        for parent_xpath in self._endpoints:
            parents = self.parser.find(parent_xpath)

            for parent in parents:
                urls = parent.xpath(url_xpath, namespaces=self.parser._namespaces)

                if not urls:
                    continue

                url = urls[0].text

                codes = parent.xpath(code_xpath, namespaces=self.parser._namespaces)

                format_elem = next(iter(parent.xpath(format_xpath,
                                        namespaces=self.parser._namespaces)), None)
                format_name, format_version, format_desc = self._extract_format_info(format_elem)
                format = self._identify_format(format_name, format_version, format_desc, url)

                # TODO: sort out if this "type" is the http method or some other thing
                endpoints.append(
                    tidy_dict({
                        "url": url,
                        "type": codes[0] if codes else '',
                        "mimeType": format,
                        "actionable": 1  # we can only assume these are good links in the iso
                    })
                )

        return endpoints


'''
NOTE: for all of the ISO parsers, I am using the local-path "trick". It is a known
      performance hit but the harmonization across -1, -2, -3, INSPIRE, data.gov,
      whatever, is a not insignificant chunk of dev time as well. I am willing to
      make this tradeoff given the ETL workflow.
'''


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

        xp = generate_localname_xpath(['identificationInfo', 'MD_DataIdentification'])
        id_elem = next(iter(self.elem.xpath(xp)), None)
        if id_elem is not None:
            title, abstract, keywords = parse_identification_info(id_elem)
            mx['title'] = title
            mx['abstract'] = abstract
            mx['keywords'] = keywords

        # point of contact from the root node and this might be an issue
        # in things like the -1/-3 from ngdc so try for an idinfo blob
        xp = generate_localname_xpath([
            'identificationInfo', 'MD_DataIdentification', 'pointOfContact', 'CI_ResponsibleParty'])
        poc_elem = next(iter(self.elem.xpath(xp)), None)
        if poc_elem is None:
            # and if that fails try for the root-level contact
            xp = generate_localname_xpath(['contact', 'CI_ResponsibleParty'])
            poc_elem = next(iter(self.elem.xpath(xp)), None)

        if poc_elem is not None:
            ind_name, org_name, position, contact = parse_responsibleparty(poc_elem)
            mx['contact'] = {
                'individual_name': ind_name,
                'organization_name': org_name,
                'position': position,
                'contact': contact
            }

        # check for the service elements
        xp = generate_localname_xpath(['identificationInfo', 'SV_ServiceIdentification'])
        service_elems = self.elem.xpath(xp)
        mx['services'] = []
        for service_elem in service_elems:
            sv = SrvParser(service_elem)
            mx['services'].append(sv.parse())

        xp = generate_localname_xpath(['distributionInfo'])
        dist_elems = self.elem.xpath(xp)
        mx['endpoints'] = []
        for dist_elem in dist_elems:
            mx['distribution'].append(parse_distribution(id_elem))

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

        xp = generate_localname_xpath(['name', 'aName', 'CharacterString'])
        e = next(iter(elem.xpath(xp)), None)
        param['name'] = e.text.strip() if e is not None else ''

        xp = generate_localname_xpath(
            ['name', 'attributeType', 'TypeName', 'aName', 'CharacterString'])
        e = next(iter(elem.xpath(xp)), None)
        param['inputType'] = e.text.strip() if e is not None else ''

        xp = generate_localname_xpath(['direction', 'SV_ParameterDirection'])
        e = next(iter(elem.xpath(xp)), None)
        param['direction'] = e.text.strip() if e is not None else ''

        xp = generate_localname_xpath(['optionality', 'CharacterString'])
        e = next(iter(elem.xpath(xp)), None)
        param['optional'] = e.text.strip() if e is not None else ''

        xp = generate_localname_xpath(['repeatability', 'Boolean'])
        e = next(iter(elem.xpath(xp)), None)
        param['cardinality'] = e.text.strip() if e is not None else ''

        xp = generate_localname_xpath(['valueType', 'TypeName', 'aName', 'CharacterString'])
        e = next(iter(elem.xpath(xp)), None)
        param['valueType'] = e.text.strip() if e is not None else ''

        return param

    def _handle_operations(self):
        xp = generate_localname_xpath(['containsOperations', 'SV_OperationMetadata'])
        elems = self.elem.xpath(xp)

        ops = []
        for e in elems:
            op = {}

            xp = generate_localname_xpath(['operationName', 'CharacterString'])
            x = next(iter(e.xpath(xp)), None)
            op['name'] = x.text.strip() if x is not None else ''

            xp = generate_localname_xpath(['DCP', 'DCPList', '@codeListValue'])
            x = next(iter(e.xpath(xp)), None)
            op['method'] = x.text.strip() if x is not None else ''

            xp = generate_localname_xpath(['connectPoint', 'CI_OnlineResource', 'linkage', 'URL'])
            x = next(iter(e.xpath(xp)), None)
            op['url'] = x.text.strip() if x is not None else ''

            xp = generate_localname_xpath(['parameters', 'SV_Parameter'])
            param_elems = e.xpath(xp)
            op['parameters'] = [self._handle_parameter(pe) for pe in param_elems]

        return ops

    def parse(self):
        xp = generate_localname_xpath(['SV_ServiceIdentification'])
        elem = next(iter(self.elem.xpath(xp)), None)
        if elem is None:
            return None

        service = {}

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
        xp = generate_localname_xpath(['seriesMetadata', 'MD_Metadata'])
        md = next(iter(self.elem.xpath(xp)), None)
        if md is None:
            return None

        md_parser = MxParser(md)
        md_dict = md_parser.parse()
        md_dict['children'] = []

        # get the children
        xp = generate_localname_xpath(['composedOf', 'DS_Dataset', 'has', 'MD_Metadata'])
        children = self.elem.xpath(xp)
        for child in children.iter():
            child_parser = MxParser(child)
            child_dict = child_parser.parse()
            md_dict['children'].append(child_dict)

        return md_dict
