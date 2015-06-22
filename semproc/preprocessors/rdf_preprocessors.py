from semproc.base_preprocessors import BaseReader


class RdfReader(BaseReader):
    '''
    rdf parser (if dataset)
    '''

    def parse(self):
        self.description = {}
