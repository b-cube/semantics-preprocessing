from lib.base_preprocessors import BaseReader


class OaiPmhReader(BaseReader):
    _service_descriptors = {
        "title": "/{http://www.openarchives.org/OAI/2.0/}OAI-PMH/" +
                 "{http://www.openarchives.org/OAI/2.0/}Identify/" +
                 "{http://www.openarchives.org/OAI/2.0/}repositoryName",
        "version": "/{http://www.openarchives.org/OAI/2.0/}OAI-PMH/" +
                   "{http://www.openarchives.org/OAI/2.0/}Identify/" +
                   "{http://www.openarchives.org/OAI/2.0/}protocolVersion"
    }

    def return_exclude_descriptors(self):
        excluded = self._service_descriptors.values()
        return [e[1:] for e in excluded]

    def parse_endpoints(self):
        '''
        return the baseUrl (should match the base of the identify
            request anyway, but let's make it explicit)
        '''
        url_xpath = "/{http://www.openarchives.org/OAI/2.0/}OAI-PMH/" + \
                    "{http://www.openarchives.org/OAI/2.0/}Identify/" + \
                    "{http://www.openarchives.org/OAI/2.0/}baseURL"

        urls = self.parser.find(url_xpath)

        return [
            {
                "url": url.text
            } for url in urls
        ]
