from lib.base_preprocessors import BaseReader


class RdfReader(BaseReader):
    '''
    rdf parser (if dataset)
    '''

    def parse_service(self):
        return {}