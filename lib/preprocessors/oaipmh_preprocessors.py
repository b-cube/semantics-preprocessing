from lib.base_preprocessors import BaseReader


class OaiPmhReader(BaseReader):
    _service_descriptors = {
        "title": "/{http://www.openarchives.org/OAI/2.0/}OAI-PMH/{http://www.openarchives.org/OAI/2.0/}Identify/{http://www.openarchives.org/OAI/2.0/}repositoryName",
        "source": "/{http://www.openarchives.org/OAI/2.0/}OAI-PMH/{http://www.openarchives.org/OAI/2.0/}Identify/{http://www.openarchives.org/OAI/2.0/}baseURL", 
        "version": "/{http://www.openarchives.org/OAI/2.0/}OAI-PMH/{http://www.openarchives.org/OAI/2.0/}Identify/{http://www.openarchives.org/OAI/2.0/}protocolVersion"
    }

    def return_exclude_descriptors(self):
        excluded = self._service_descriptors.values()
        return [e[1:] for e in excluded]

    def parse_endpoints(self):
        pass
