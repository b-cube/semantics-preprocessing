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

    def _get_items(self, tag, elem):
        '''
        return any structure not part of the
        current element's attributes
        '''
        description = {extract_element_tag(k): v for k, v in elem.attrib.iteritems()}

        # get the service bases in case
        services = self.parser.find('//*[local-name()="service" and @base != ""]')
        service_bases = {s.attrib.get('name'): s.attrib.get('base') for s in services}

        

        if 'ID' not in description:
            description.update({"ID": generate_short_uuid()})

        return description

    def _handle_elem(self, elem, child_tags):
        description = self._get_items(extract_element_tag(elem.tag), elem)
        description['source'] = extract_element_tag(elem.tag)

        endpoints = []

        for child_tag in child_tags:
            elems = elem.xpath('*[local-name()="%s"]' % child_tag)

            if elems:
                endpoints += [
                    dict(
                        chain(
                            self._get_items(extract_element_tag(e.tag), e).items(),
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

    def _normalize_endpoints(self, endpoints):
        '''
        the extraction takes any attribute/element tag as is
        but that is less than ideal for the triples (we want
            to minimize the special flower handling at that
            end as much as possible)

        minor flattening
        '''

        # as source key: endpoint key
        remaps = {
            "serviceType": "type",
            "href": "url",
            "base": "url",
            "urlPath": "url",
            "serviceName": "type"
        }

        new_endpoints = []
        for endpoint in endpoints:
            # remap things
            new_endpoints.append({remaps[k] if k in remaps else k: v
                                  for k, v in endpoint.iteritems()})

        return new_endpoints

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
                    dataset, ['dataset', 'metadata', 'catalogRef']
                )
                endpoints += [description] + child_endpoints

        return {"endpoints": self._normalize_endpoints(endpoints)}

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
                description, child_endpoints = self._handle_elem(metadata, [])
                endpoints += [description] + child_endpoints

        return {"endpoints": self._normalize_endpoints(endpoints)}

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

        services = self.parser.find(svc_xpath)
        # ffs, services can be nested too
        if services:
            self._to_exclude.append(svc_xpath[1:])
            for key in services[0].attrib.keys():
                self._to_exclude.append(svc_xpath[1:] + '/@' + key)

            for service in services:
                description, child_endpoints = self._handle_elem(service, ['service'])
                endpoints += [description] + child_endpoints

        catrefs = self.parser.find(catref_xpath)
        if catrefs:
            self._to_exclude.append(catref_xpath[1:])
            self._to_exclude.append(catref_xpath[1:] + '/@title')
            self._to_exclude.append(catref_xpath[1:] + '/@href')
            for catref in catrefs:
                description, child_endpoints = self._handle_elem(catref, ['catalogRef', 'metadata'])
                endpoints += [description] + child_endpoints

        return self._normalize_endpoints(endpoints)
