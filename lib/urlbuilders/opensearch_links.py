from lxml import etree
import urlparse
import urllib
from itertools import chain


class OpenSearchLinkBuilder(object):
    '''
    for an OSDD URL/@template url, create a generic
    search url, ie the link to return all results (if supported)
    '''

    def __init__(self, source_url, source_content):
        self.source_url = source_url
        self.source_content = source_content
        self._parse()

    def _parse(self):
        try:
            parser = etree.XMLParser(
                remove_blank_text=True,
                remove_comments=True,
                recover=True,
                remove_pis=True
            )
            self.xml = etree.fromstring(self.source_content, parser=parser)
        except:
            self.xml = None

    def _extract_urls(self, mimetype='atom+xml'):
        return self.xml.xpath('//*[local-name()="Url" and (@*[local-name()="type"]="application/%(mimetype)s" or @*[local-name()="type"]="text/%(mimetype)s")]' % {'mimetype': mimetype})

    def _extract_parameter_key(self, value, params):
        # sort out the query parameter name for a parameter
        # and don't send curly bracketed things, please
        return {k: v.split(':')[-1].replace('?', '') for k, v
                in params.iteritems()
                if value in v}

    def _extract_template(self, template_url, append_limit):
        parts = urlparse.urlparse(template_url)
        if not parts.scheme:
            return '', '', {}

        base_url = urlparse.urlunparse((
            parts.scheme,
            parts.netloc,
            parts.path,
            None,
            None,
            None
        ))

        qp = {k: v[0] for k, v in urlparse.parse_qs(parts.query).iteritems()}

        # get the hard-coded params
        defaults = {k: v for k, v in qp.iteritems()
                    if not v.startswith('{')
                    and not v.endswith('}')}

        # get the rest (and ignore the optional/namespaces)
        parameters = {k: v[1:-1] for k, v in qp.iteritems()
                      if v.startswith('{')
                      and v.endswith('}')}

        if append_limit:
            terms = self._extract_parameter_key('count', parameters)
            if terms:
                defaults = dict(
                    chain(defaults.items(), {k: 5 for k in terms.keys()}.items())
                )

        # note: not everyone manages url-encoded query parameter delimiters
        #       and not everyone manages non-url-encoded values so yeah. we are
        #       ignoring the non-url-encoded group.
        return base_url, defaults, parameters

    def generate_urls(self):
        template_urls = self._extract_urls('atom+xml') + self._extract_urls('rss+xml')
        template_urls = list(set(template_urls))

        urls = []

        if not template_urls:
            return urls

        for template_url in template_urls:
            url_base, defaults, params = self._extract_template(template_url.attrib.get('template'))
            if not url_base:
                continue
            search_terms = self._extract_parameter_key('searchTerms', params)
            if search_terms:
                qps = dict(
                    chain(
                        defaults.items(),
                        {search_terms.keys()[0]: ''}.items()
                    )
                )

                urls.append(url_base + '?' + urllib.urlencode(qps.items()))

        return urls
