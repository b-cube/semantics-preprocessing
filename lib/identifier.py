import logging

LOGGER = logging.getLogger(__name__)

# TODO: put together a configuration widget for
#       to map protocol to some search filters
#       and some service description filters,
#       and some dataset filters so that we can
#       have one thing to map the priority set
#       vs the IDENTIFY ALL THE THINGS! set. oh,
#       and wind up with reasonable line lengths
#       for beto. :) so basically elasticsearch all
#       the things.
#
# _ors: [content filters] + [url filters] (ANY match)
# _ands [content filter + url filter (or other combo)]
# where an _ands can be a filter in an _ors
#
# add the bit about is it valid xml?
# add the bit about version extraction?
# add the bit about it's valid xml but a error response


def identify_response(source_content, source_url):
    '''
    from a url and some response content, try:
        to identify what kind of service, version
        of the service (this is very tricky without
            parsing the xml - namespaces and urls
            cannot be trusted), type of response (catalog,
            dataset, visualization, whatever)
    '''

    def _in_url(url, filters):
        '''
        check for some string in a url
        (not concerned so much about where)
        '''
        url = url.strip()
        return len([f for f in filters if f.strip() in url]) > 0

    def _in_content(content, filters):
        '''
        check for some string in a text blob
        (not concerned so much about where)
        '''
        return len([f for f in filters if f in content]) > 0

    def identify_protocol():
        '''
        basic identification

        note:
            currently starting with high priority service types
        '''
        if _in_content(source_content, ['http://www.isotc211.org/2005/gmi',
                                        'http://www.isotc211.org/2005/gmd']):
            # note: not differentiating between versions here
            return 'ISO-19115'
        elif _in_content(source_content, ['http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0']):
            return 'UNIDATA:Catalog'
        elif _in_content(source_content, ['http://a9.com/-/spec/opensearch/1.1/']):
            return 'OpenSearch1.1'
        elif _in_content(source_content, ['http://wadl.dev.java.net']):
            return 'WWW:WADL'
        elif _in_content(source_content, ['http://www.opengis.net/wms']) \
                or _in_url(source_url.upper(), ['SERVICE=WMS']) \
                or (_in_content(source_content, ['http://mapserver.gis.umn.edu/mapserver'])
                    and _in_url(source_url.upper(), ['SERVICE=WMS'])):
            return 'OGC:WMS'
        elif _in_content(source_content, ['http://www.opengis.net/wfs']) \
                or _in_url(source_url.upper(), ['SERVICE=WFS']) \
                or (_in_content(source_content, ['http://mapserver.gis.umn.edu/mapserver'])
                    and _in_url(source_url.upper(), ['SERVICE=WFS'])):
            return 'OGC:WFS'
        elif _in_content(source_content, ['http://www.opengis.net/wcs']) \
                or _in_url(source_url.upper(), ['SERVICE=WCS']) \
                or (_in_content(source_content, ['http://mapserver.gis.umn.edu/mapserver'])
                    and _in_url(source_url.upper(), ['SERVICE=WCS'])):
            return 'OGC:WCS'
        elif _in_content(source_content, ['http://www.openarchives.org/OAI/']):
            return 'OAI-PMH'

        LOGGER.info('Unable to identify: %s' % source_url)

        return ''

    def identify_as_service(protocol):
        '''
        based on the protocol and source information, identify whether
        a response/service is an actual service description document or
        some other thing
        '''
        if protocol in ['OGC:WMS', 'OGC:WFS', 'OGC:WCS'] and \
                _in_url(source_url.upper(), ['REQUEST=GETCAPABILITIES']):
            return True
        elif protocol in ['OAI-PMH'] and (_in_url(source_url.upper(),
                ['VERB=IDENTIFY']) or _in_content(source_content, ['<Identify>'])):
            return True
        elif protocol in ['OpenSearch'] and _in_content(source_content,
                ['OpenSearchDescription']):
            return True
        elif protocol in ['THREDDS Catalog']:
            return True

        return False

    def identify_as_dataset(protocol):
        return ''

    def generate_urn(protocol, service, dataset, version):
        return ':'.join([protocol, service, dataset, version])

    # identify protocol
    # identify service type
    # ignore the version?
    # identify response type

    protocol = identify_protocol(source_content, source_url)
    service = identify_as_service(protocol, source_content, source_url)
    dataset = identify_as_dataset(protocol, source_content, source_url)
    version = ''

    return generate_urn(protocol, service, dataset, version)
