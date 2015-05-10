from lib.base_preprocessors import BaseReader
from lib.utils import tidy_dict


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
