from lib.base_preprocessors import BaseReader
# from itertools import chain
from lib.utils import extract_element_tag
from lib.utils import generate_short_uuid
from lib.utils import generate_qualified_xpath
# from lib.utils import generate_localname_xpath
from lib.utils import intersect_url


class ThreddsReader(BaseReader):
    _service_descriptors = {
        "title": "@name",
        "version": "@version"
    }
    _to_exclude = []

    def _manage_id(self, obj):
        if 'ID' not in obj:
            obj.update({"ID": generate_short_uuid()})
        return obj

    def _get_items(self, tag, elem, base_url, service_bases):
        '''
        return any structure not part of the
        current element's attributes
        '''

        def _normalize_key(key):
            '''
            standardize the url (or other) xml tags to the desired
            json key

            as source key: endpoint key
            '''
            remaps = {
                "serviceType": "type",
                "href": "url",
                "base": "url",
                "urlPath": "url"
            }

            if key in remaps:
                return remaps[key]
            return key

        def _run_element(elem, service_bases):
            '''
            for a given element, return any text() and any attribute value
            '''
            # run a generated xpath on the given element
            excludes = [generate_qualified_xpath(elem, True)]

            children = elem.xpath('./node()[local-name()!="metadata"' +
                                  'and local-name()!="dataset" and' +
                                  'local-name()!="catalogRef"]')

            element = {_normalize_key(extract_element_tag(k)): v for k, v
                       in elem.attrib.iteritems()}
            element = self._manage_id(element)

            for child in children:
                value = child.text
                xp = generate_qualified_xpath(child, True)
                tag = _normalize_key(extract_element_tag(child.tag))

                excludes += [xp] + [xp + '/@' + k for k in child.attrib.keys()]

                if value:
                    element[tag] = value

                for k, v in child.attrib.iteritems():
                    if v:
                        element[tag + '_' + _normalize_key(extract_element_tag(k))] = v

            # get the service bases in case
            if [g for g in element.keys() if g.endswith('serviceName')]:
                sbs = [v for k, v in service_bases.iteritems() if k == element.get('serviceName')]
            else:
                sbs = service_bases.values()

            # send a unique list of base relative paths
            sbs = list(set(sbs))

            url_key = next(iter([g for g in element.keys() if g.endswith('url')]), '')
            if url_key:
                # for service urls, if catalog.xml isn't appended it will resolve to
                # the html endpoint (not desired). so if the path equals the/a path in
                # the service bases, append catalog.xml to the path
                elem_url = element[url_key]
                if elem_url in sbs or not sbs:
                    elem_url += ('' if elem_url.endswith('/') else '/') + 'catalog.xml'
                element['url'] = intersect_url(base_url, elem_url, sbs)
                element['actionable'] = 2

            return element, excludes

        children = elem.xpath('./node()[local-name()="metadata" or ' +
                              'local-name()="dataset" or local-name()="catalogRef"]')

        element, excludes = _run_element(elem, service_bases)
        element_children = []
        for c in children:
            element_desc, element_excludes = _run_element(c, service_bases)
            excludes += element_excludes
            element_children.append(element_desc)

        if element_children:
            element['children'] = element_children

        return element, excludes

    def _handle_elem(self, elem, child_tags, base_url, service_bases):
        description, excludes = self._get_items(
            extract_element_tag(elem.tag), elem, base_url, service_bases
        )
        description['source'] = extract_element_tag(elem.tag)

        self._to_exclude += excludes

        endpoints = []

        for child_tag in child_tags:
            elems = elem.xpath('*[local-name()="%s"]' % child_tag)

            for e in elems:
                e_desc, e_excludes = self._get_items(
                    extract_element_tag(e.tag), e, base_url, service_bases
                )

                e_desc['childOf'] = description.get('ID', '')
                e_desc["source"] = extract_element_tag(child_tag)
                self._to_exclude += e_excludes

                parents = description.get('parentOf', [])
                parents += [e['ID'] for e in endpoints if 'childOf' in e]
                description['parentOf'] = parents

                endpoints.append(e_desc)

        return description, endpoints

    def return_dataset_descriptors(self):
        dataset_xpath = "/{http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0}catalog/" + \
                        "{http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0}dataset"

        # get the level-one children (catalog->child)
        endpoints = []
        datasets = self.parser.find(dataset_xpath)
        if datasets:
            self._to_exclude.append(dataset_xpath[1:])
            self._to_exclude += [dataset_xpath[1:] + '/@name', dataset_xpath[1:] + '/@ID']

            for dataset in datasets:
                description, child_endpoints = self._handle_elem(
                    dataset, ['dataset', 'metadata', 'catalogRef'],
                    self._url,
                    self.service_bases
                )
                endpoints += [description] + child_endpoints

        return {"endpoints": endpoints}

    def return_metadata_descriptors(self):
        metadata_xpath = "/{http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0}catalog/" + \
                         "{http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0}metadata"

        endpoints = []
        metadatas = self.parser.find(metadata_xpath)
        if metadatas:
            self._to_exclude.append(metadata_xpath[1:])
            for key in metadatas[0].attrib.keys():
                self._to_exclude.append(metadata_xpath[1:] + '/@' + key)

            for metadata in metadatas:
                description, child_endpoints = self._handle_elem(
                    metadata,
                    [],
                    self._url,
                    self.service_bases
                )
                endpoints += [description] + child_endpoints

        return {"endpoints": endpoints}

    def return_exclude_descriptors(self):
        '''
        need to return the fully qualified structure for the root
        attributes for the remainder processing
        '''
        excluded = self._service_descriptors.values()
        return ['{http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0}catalog/' + e
                for e in excluded] + list(set(self._to_exclude))

    def parse_endpoints(self):
        '''
        JUST THE SERVICE ENDPOINTS (service and catalogRef elements
            at the root level)
        if the catalog service contains service elements. or a dataset
        element or catalogRef elements, parse those as endpoints (relative paths
            and all of the tagging issues)
        '''
        svc_xpath = "/{http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0}catalog/" + \
                    "{http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0}service"

        catref_xpath = "/{http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0}catalog/" + \
                       "{http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0}catalogRef"

        endpoints = []

        service_bases = self.parser.find('//*[local-name()="service" and @base != ""]')
        self.service_bases = {s.attrib.get('name'): s.attrib.get('base') for s in service_bases}

        services = self.parser.find(svc_xpath)
        # ffs, services can be nested too
        if services:
            self._to_exclude.append(svc_xpath[1:])
            for key in services[0].attrib.keys():
                self._to_exclude.append(svc_xpath[1:] + '/@' + key)

            for service in services:
                description, child_endpoints = self._handle_elem(
                    service,
                    ['service'],
                    self._url,
                    {}
                )
                endpoints += [description]
                if child_endpoints:
                    endpoints += child_endpoints

        catrefs = self.parser.find(catref_xpath)
        if catrefs:
            self._to_exclude.append(catref_xpath[1:])
            self._to_exclude.append(catref_xpath[1:] + '/@title')
            self._to_exclude.append(catref_xpath[1:] + '/@href')
            for catref in catrefs:
                description, child_endpoints = self._handle_elem(
                    catref,
                    ['catalogRef', 'metadata'],
                    self._url,
                    {}  # TODO: so dap or file base path only? (not the full set, that makes no sense)
                )
                endpoints += [description] + child_endpoints

        return endpoints
