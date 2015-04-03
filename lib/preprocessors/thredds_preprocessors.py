from lib.base_preprocessors import BaseReader
from itertools import chain
from lib.utils import extract_element_tag
from lib.utils import generate_short_uuid
from lib.utils import generate_qualified_xpath
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
            '''

            # as source key: endpoint key
            remaps = {
                "serviceType": "type",
                "href": "url",
                "base": "url",
                "urlPath": "url"
            }

            key = key.split('_')[-1] if '_' in key else key

            if key in remaps:
                return remaps[key]
            return key

        def _generate_xpath(tags):
            return '/'.join(['*[local-name()="%s"]' % t if t not in ['*', '..', '.'] else t
                             for t in tags.split('/') if t])

        def _run_element(elem, service_bases):
            '''
            for a given element, return any text() and any attribute value
            '''
            # run a generated xpath on the given element
            excludes = [generate_qualified_xpath(elem, True)]

            children = elem.xpath('./node()[local-name()!="metadata"' +
                                  'and local-name()!="dataset" and' +
                                  'local-name()!="catalogRef"]')

            element = {extract_element_tag(k): v for k, v in elem.attrib.iteritems()}
            element = self._manage_id(element)

            for child in children:
                value = child.text
                xp = generate_qualified_xpath(child, True)
                tag = _normalize_key(extract_element_tag(child))

                excludes += [xp] + [xp + '/@' + k for k in child.attrib.keys()]

                element[tag] = value
                for k, v in child.attrib.iteritems():
                    element[tag + '_' + _normalize_key(extract_element_tag(k))] = v

            for k, v in element.iteritems():
                sbs = [v for k, v in service_bases if k == element['serviceName']]

            # get the service bases in case
            if [g for g in element.keys() if g.endswith('url') or g.endswith('serviceName')]:
                # generate the url
                sbs = [v for k, v in service_bases if k == element['serviceName']]
            else:
                sbs = service_bases

            element['url'] = intersect_url(value, base_url, sbs)
            element['actionable'] = 2

            return element, excludes

        children = elem.xpath('./node()[local-name()="metadata" or ' +
                              'local-name()="dataset" or local-name()="catalogRef"]')

        element = _run_element(elem, service_bases)
        element['children'] = []
        excludes = []
        for c in children:
            element_desc, element_excludes = _run_element(c)
            excludes += element_excludes
            element['children'] += element_desc

        return element, excludes

    def _handle_elem(self, elem, child_tags, base_url):
        description = self._get_items(extract_element_tag(elem.tag), elem, base_url)
        description['source'] = extract_element_tag(elem.tag)

        endpoints = []

        for child_tag in child_tags:
            elems = elem.xpath('*[local-name()="%s"]' % child_tag)

            if elems:
                endpoints += [
                    dict(
                        chain(
                            self._get_items(extract_element_tag(e.tag), e, base_url).items(),
                            {
                                "childOf": description.get('ID', ''),
                                "source": extract_element_tag(child_tag)
                            }.items()
                        )
                    ) for e in elems
                ]

                self._to_exclude += [generate_qualified_xpath(e, True) for e in elems]

                parents = description.get('parentOf', [])
                parents += [e['ID'] for e in endpoints if 'childOf' in e]
                description['parentOf'] = parents

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
                    self._url
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
                description, child_endpoints = self._handle_elem(metadata, [], self._url)
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
        service_bases = {s.attrib.get('name'): s.attrib.get('base') for s in service_bases}

        services = self.parser.find(svc_xpath)
        # ffs, services can be nested too
        if services:
            self._to_exclude.append(svc_xpath[1:])
            for key in services[0].attrib.keys():
                self._to_exclude.append(svc_xpath[1:] + '/@' + key)

            for service in services:
                description, child_endpoints = self._handle_elem(service, ['service'], self._url)
                endpoints += [description] + child_endpoints

        catrefs = self.parser.find(catref_xpath)
        if catrefs:
            self._to_exclude.append(catref_xpath[1:])
            self._to_exclude.append(catref_xpath[1:] + '/@title')
            self._to_exclude.append(catref_xpath[1:] + '/@href')
            for catref in catrefs:
                description, child_endpoints = self._handle_elem(
                    catref, ['catalogRef', 'metadata'], self._url
                )
                endpoints += [description] + child_endpoints

        return endpoints
