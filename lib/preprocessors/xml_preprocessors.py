from lib.base_preprocessors import BaseReader


class XmlReader(BaseReader):
    '''
    a very basic processor for any valid xml
    response that is not identified (or not identified
        as having a known processor) but should be
    retained in the system, ie. how to model no's
    '''

    def return_exclude_descriptors(self):
        pass

    def parse_service(self):
        '''
        where we have no service info, no endpoints
        and it's basically just the remainders element
        '''
        return {'remainder': self.return_everything_else([])}
