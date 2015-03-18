from lib.base_preprocessors import BaseReader
from itertools import chain
from lib.utils import extract_element_tag, generate_short_uuid


class ThreddsReader(BaseReader):
    _service_descriptors = {
        "title": "@name",
        "version": "@version"
    }
    _to_exclude = []

    def return_exclude_descriptors(self):
        '''
        need to return the fully qualified structure for the root
        attributes for the remainder processing
        '''
        excluded = self._service_descriptors.values()
        return ['{http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0}catalog/' + e
                for e in excluded] + self._to_exclude

    def parse_endpoints(self):
        '''
        if the catalog service contains service elements. or a dataset
        element or catalogRef elements, parse those as endpoints (relative paths
            and all of the tagging issues)
        '''
        svc_xpath = "/{http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0}catalog/" + \
                    "{http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0}service"
        dataset_xpath = "/{http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0}catalog/" + \
                        "{http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0}dataset"
        catref_xpath = "/{http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0}catalog/" + \
                       "{http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0}catalogRef"
        metadata_xpath = "/{http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0}catalog/" + \
                         "{http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0}metadata"

        def _get_items(tag, elem):
            '''
            return any structure not part of the
            current element's attributes
            '''
            if tag == 'catalogRef':
                return {}
            elif tag == 'metadata':
                metadata_description = {"ID": generate_short_uuid()}
                service_elem = next(iter(elem.xpath('*[local-name()="serviceName"]')), None)
                if service_elem is not None:
                    metadata_description['service'] = service_elem.text.strip()

                publisher_elem = next(iter(elem.xpath('*[local-name()="publisher"]')), None)
                if publisher_elem is not None:
                    name_elem = next(iter(publisher_elem.xpath('*[local-name()="name"]')), None)
                    contact_elem = next(iter(publisher_elem.xpath('*[local-name()="contact"]')),
                                        None)

                    if name_elem is not None:
                        metadata_description['publisher']['name'] = name_elem.text.strip()
                        metadata_description['publisher']['name_vocabulary'] = name_elem.attrib.get('vocabulary', '')

                    if contact_elem is not None:
                        metadata_description['publisher']['contact'] = contact_elem.attrib

                return metadata_description
            elif tag == 'dataset':
                dataset_description = {}
                datasize_elem = next(iter(elem.xpath('*[local-name()="dataSize"]')), None)
                if datasize_elem is not None:
                    datasize = {
                        "units": datasize_elem.attrib.get('units', ''),
                        "size": datasize_elem.text.strip()
                    }
                    dataset_description['datasize'] = datasize

                date_elem = next(iter(elem.xpath('*[local-name()="date"]')), None)
                if date_elem is not None:
                    date = {
                        "type": date_elem.attrib.get('type', ''),
                        "date": date_elem.text.strip()
                    }
                    dataset_description['date'] = date

                access_elem = next(iter(elem.xpath('*[local-name()="access"]')), None)
                if access_elem is not None:
                    access = {
                        "serviceName": access_elem.attrib.get('serviceName', ''),
                        "url": access_elem.attrib.get('urlPath', '')
                    }
                    dataset_description['access'] = access

                return dataset_description
            else:
                return {}

        def _handle_elem(elem, child_tags):
            description = dict(elem.attrib.items())
            description['source'] = extract_element_tag(elem.tag)

            endpoints = []

            for child_tag in child_tags:
                elems = elem.xpath('*[local-name()="%s"]' % child_tag)

                if elems:
                    endpoints += [
                        dict(
                            chain(
                                e.attrib.items(),
                                _get_items(extract_element_tag(e.tag), e).items(),
                                {
                                    "childOf": description.get('ID', ''),
                                    "source": extract_element_tag(child_tag)
                                }.items()
                            )
                        ) for e in elems
                    ]

                    parents = description.get('parentOf', [])
                    parents += [e.attrib.get('ID', '-9999') for e in elems]
                    description['parentOf'] = parents

            return description, endpoints

        endpoints = []

        services = self.parser.find(svc_xpath)
        # ffs, services can be nested too
        if services:
            self._to_exclude.append(svc_xpath[1:])
            for key in services[0].attrib.keys():
                self._to_exclude.append(svc_xpath[1:] + '/@' + key)

            for service in services:
                description, child_endpoints = _handle_elem(service, ['service'])
                endpoints += [description] + child_endpoints

        # get the level-one children (catalog->child)
        datasets = self.parser.find(dataset_xpath)
        if datasets:
            self._to_exclude.append(dataset_xpath[1:])
            self._to_exclude += [dataset_xpath[1:] + '/@name', dataset_xpath[1:] + '/@ID']

            for dataset in datasets:
                description, child_endpoints = _handle_elem(dataset,
                                                            ['dataset', 'metadata', 'catalogRef'])
                endpoints += [description] + child_endpoints

        catrefs = self.parser.find(catref_xpath)
        if catrefs:
            self._to_exclude.append(catref_xpath[1:])
            self._to_exclude.append(catref_xpath[1:] + '/@title')
            self._to_exclude.append(catref_xpath[1:] + '/@href')
            for catref in catrefs:
                description, child_endpoints = _handle_elem(catref, ['catalogRef', 'metadata'])
                endpoints += [description] + child_endpoints

        metadatas = self.parser.find(metadata_xpath)
        if metadatas:
            self._to_exclude.append(metadata_xpath[1:])
            for key in metadatas[0].attrib.keys():
                self._to_exclude.append(metadata_xpath[1:] + '/@' + key)

            for metadata in metadatas:
                description, child_endpoints = _handle_elem(metadata, [])
                endpoints += [description] + child_endpoints

        return endpoints
