from lxml import etree
import urllib
import urlparse
from semproc.utils import extract_element_tag


class ThreddsLinkBuilder(object):
    '''
    for a catalog.xml file and a source url, convert the
    relative paths for catalogRefs and datasets to full paths
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

    def generate_urls(self):
        '''
        run the xml
        '''
        if self.xml is None:
            return []

        services = self.xml.xpath(
            '//*[local-name()="service" and @base != ""]/@*[local-name()="base"]')
        services = [s[:-1] if s.endswith('/') else s for s in services]

        elements = self.xml.xpath('//*[local-name()="catalogRef" or local-name()="dataset"]')

        # return the urls as id: new url(s) (based on the services)
        generated_urls = {}
        for element in elements:
            # track the ID or the name is that's not provided
            elem_id = element.attrib.get('ID', '')
            if not elem_id:
                elem_id = element.attrib.get('name', '')

            if not elem_id:
                continue
            tl = ThreddsLink(element, self.source_url, services)

            generated_urls[elem_id] = tl.urls

        return generated_urls


class ThreddsLink():
    def __init__(self, elem, source_url, services=[]):
        self.elem = elem
        self.services = services
        self.source_url = source_url
        self.source_parts = urlparse.urlparse(source_url)

    def _generate(self):
        tag = extract_element_tag(self.elem.tag)

        # find the href or urlPath
        if tag == 'dataset':
            href = self.elem.attrib.get('urlPath', None)
            if href is None:
                href = next(
                    iter(self.elem.xpath('*[local-name()="access"]/@*[local-name()="urlPath"]')),
                    None)

            # if there's a urlPath (anywhere), it *should* be the
            # terminal file path
            hrefs = [
                self._generate_url('/'.join(service, href), self._get_ogc_params(service))
                for service in self.services]

        elif tag == 'catalogRef':
            href = self.elem.attrib.get('{http://www.w3.org/1999/xlink}href', '')
            hrefs = [self._generate_url(href)]

        self.urls = hrefs

    def _generate_url(self, rel_path, query_params={}):
        if urlparse.urlparse(rel_path).scheme:
            return rel_path

        rel_path = rel_path[1:] if rel_path.startswith('/') else rel_path
        rel_paths = rel_path.split('/')
        url_paths = self.source_parts.path.split('/')
        match_index = url_paths.index(rel_paths[0]) if rel_paths[0] in url_paths else -1

        query = urllib.urlencode(query_params) if query_params else None

        if match_index < 0:
            # it does not intersect, just combine
            new_url = urlparse.urljoin(self.source_url.replace('catalog.xml', ''), rel_path)
        else:
            new_url = urlparse.urljoin(urlparse.urlunparse((
                self.source_parts.scheme,
                self.source_parts.netloc,
                '/'.join(url_paths[0:match_index + 1]),
                None,
                None,
                None
            )), rel_path)

        new_url += '?' + query if query else ''
        return new_url

    def _get_ogc_params(self, service):
        if 'wms' in service.lower():
            return {'service': 'wms', 'request': 'getcapabilities', 'version': '1.3.0'}
        elif 'wfs' in service.lower():
            return {'service': 'wfs', 'request': 'getcapabilities', 'version': '1.1.0'}
        elif 'wcs' in service.lower():
            return {'service': 'wcs', 'request': 'getcapabilities', 'version': '1.1.2'}
        else:
            return None
