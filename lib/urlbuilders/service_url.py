import urlparse
import urllib


class ServiceUrl():
    '''
    from some url and *potentially* other bits of text,
    try to identify a service type (ogc, oai-pmh, opensearch)
    and build the service-level request
    '''
    def __init__(self, source_url, ancillary_texts=[]):
        self.source_url = source_url
        self.ancillary_texts = ancillary_texts

        self.protocol = self.identify()

    def _parse(self):
        self.url_parts = urlparse.urlparse(self.source_url)
        self.query_params = urlparse.parse_qs(self.url_parts.query)
        self.query_params = {k.lower(): v for k, v in self.query_params.iteritems()}

    def identify(self):
        '''
        try to sort out what the url might be
        based on just the url structure
        '''

        if list(set(['service', 'version', 'request']).intersection(set(self.query_params.keys()))):
            return 'OGC'
        if 'verb' in self.query_params.keys():
            return 'OAI-PMH'
        # TODO: opensearch does not have a great pattern

        return ''

    def generate_service_url(self):
        '''
        build the service endpoint
        '''
        if self.protocol == 'OGC':
            # get the version
            version = self.query_params.get('version', '')

            # get the service
            service = self.query_params.get('service', '')

            # rebuild
            query_params = {'Version': version, 'Service': service, 'Request': 'GetCapabilities'}

        if self.protocol == 'OAI-PMH':
            query_params = {'verb': 'Identify'}

        if self.protocol == 'OpenSearch':
            query_params = {}

        return urlparse.urlunparse((
            self.url_parts.scheme,
            self.url_parts.netloc,
            self.url_parts.path,
            None,
            query_params,  # TODO: rebuild the query params
            None
        ))
