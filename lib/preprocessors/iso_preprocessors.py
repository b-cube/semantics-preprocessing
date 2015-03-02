from lib.base_preprocessors import BaseReader


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

        "language": "/*/{http://www.isotc211.org/2005/gmd}language/" +
                    "{http://www.isotc211.org/2005/gco}CharacterString",

        "subject": "/*/{http://www.isotc211.org/2005/gmd}identificationInfo/" +
                   "{http://www.isotc211.org/2005/gmd}MD_DataIdentification/" +
                   "{http://www.isotc211.org/2005/gmd}descriptiveKeywords/" +
                   "{http://www.isotc211.org/2005/gmd}MD_Keywords/" +
                   "{http://www.isotc211.org/2005/gmd}keyword/" +
                   "{http://www.isotc211.org/2005/gco}CharacterString/text()",

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
    _to_exclude = []

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
        "{http://www.isotc211.org/2005/gmd}MD_DigitalTransferOptions/" +
        "{http://www.isotc211.org/2005/gmd}onLine"
    ]

    def return_exclude_descriptors(self):
        excluded = self._service_descriptors.values()
        return [e[1:] for e in excluded] + self._to_exclude

    def parse_endpoints(self):
        '''
        pull endpoints from the distribution element

        url, type (as download, etc, from codelist)
        '''
        url_xpath = "gmd:CI_OnlineResource/" + \
                    "gmd:linkage/" + \
                    "gmd:URL"

        code_xpath = "gmd:CI_OnlineResource/" + \
                     "gmd:function/" + \
                     "gmd:CI_OnLineFunctionCode/" + \
                     "@codeListValue"

        endpoints = []
        for parent_xpath in self._endpoints:
            parents = self.parser.find(parent_xpath)

            for parent in parents:
                urls = parent.xpath(url_xpath, namespaces=self.parser._namespaces)

                if not urls:
                    continue

                codes = parent.xpath(code_xpath, namespaces=self.parser._namespaces)

                endpoints.append({"url": urls[0].text, "type": codes[0]})

        return endpoints
