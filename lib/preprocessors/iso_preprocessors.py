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
        "contact": "/*/{http://www.isotc211.org/2005/gmd}",
        "rights": "/*/{http://www.isotc211.org/2005/gmd}identificationInfo/" +
                  "{http://www.isotc211.org/2005/gmd}resourceConstraints/" +
                  "{http://www.isotc211.org/2005/gmd}MD_LegalConstraints/" +
                  "{http://www.isotc211.org/2005/gmd}useLimitation/" +
                  "{http://www.isotc211.org/2005/gco}CharacterString | "
                  "/*/{http://www.isotc211.org/2005/gmd}identificationInfo/" +
                  "{http://www.isotc211.org/2005/gmd}MD_DataIdentification/" +
                  "{http://www.isotc211.org/2005/gmd}resourceConstraints/" +
                  "{http://www.isotc211.org/2005/gmd}MD_Constraints/" +
                  "{http://www.isotc211.org/2005/gmd}useLimitation" +
                  "{http://www.isotc211.org/2005/gco}CharacterString",
        "language": "/*/{http://www.isotc211.org/2005/gmd}language" +
                    "{http://www.isotc211.org/2005/gco}CharacterString",
        "subject": "/*/{http://www.isotc211.org/2005/gmd}identificationInfo/" +
                   "{http://www.isotc211.org/2005/gmd}MD_DataIdentification/" +
                   "{http://www.isotc211.org/2005/gmd}descriptiveKeywords/" +
                   "{http://www.isotc211.org/2005/gmd}MD_Keywords/" +
                   "{http://www.isotc211.org/2005/gmd}keyword/" +
                   "{http://www.isotc211.org/2005/gco}CharacterString",
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
    _to_exclude = {}

    # to handle any of the valid iso distribution structures
    _endpoints = []

    def return_exclude_descriptors(self):
        excluded = self._service_descriptors.values()
        return [e[1:] for e in excluded] + self._to_exclude

    def parse_endpoints(self):
        '''
        pull endpoints from the distribution element

        url, type (as download, etc, from codelist)
        '''
        pass
