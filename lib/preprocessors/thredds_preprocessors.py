from lib.base_preprocessors import BaseReader


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

        endpoints = []

        services = self.parser.find(svc_xpath)
        if services:
            self._to_exclude.append(svc_xpath[1:])
            self._to_exclude.append(svc_xpath[1:] + '/@name')
            self._to_exclude.append(svc_xpath[1:] + '/@serviceType')
            self._to_exclude.append(svc_xpath[1:] + '/@base')
            for service in services:
                endpoints.append({
                    "name": service.attrib.get('name', ''),
                    "type": service.attrib.get('serviceType', ''),
                    "relative_path": service.attrib.get('base', '')
                })

        datasets = self.parser.find(dataset_xpath)
        if datasets:
            self._to_exclude.append(dataset_xpath[1:])

        catrefs = self.parser.find(catref_xpath)
        if catrefs:
            self._to_exclude.append(catref_xpath[1:])
            self._to_exclude.append(catref_xpath[1:] + '/@title')
            self._to_exclude.append(catref_xpath[1:] + '/@href')
            for catref in catrefs:
                endpoints.append({
                    "name": catref.attrib.get('title', ''),
                    "relative_path": catref.attrib.get('href', '')
                })

        metadatas = self.parser.find(metadata_xpath)
        if metadatas:
            self._to_exclude.append(metadata_xpath[1:])
            self._to_exclude.append(metadata_xpath[1:] + '/@title')
            self._to_exclude.append(metadata_xpath[1:] + '/@href')
            self._to_exclude.append(metadata_xpath[1:] + '/@metadataType')
            for metadata in metadatas:
                endpoints.append({
                    "name": metadata.attrib.get('title', ''),
                    "relative_path": metadata.attrib.get('href', ''),
                    "type": metadata.attrib.get('metadataType', '')
                })

        return endpoints
