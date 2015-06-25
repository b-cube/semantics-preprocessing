from semproc.processor import Processor


class RdfReader(Processor):
    '''
    rdf parser (if dataset)
    '''

    def parse(self):
        self.description = {}
