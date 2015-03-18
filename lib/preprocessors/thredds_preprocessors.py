from lib.base_preprocessors import BaseReader
from itertools import chain


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

        def _get_dataset_elements(elem):
            dataset_name = elem.attrib.get('name', '')
            dataset_id = elem.attrib.get('ID', '')

            # access can be just a urlPath attribute on dataset
            url = elem.attrib.get('urlPath', '')

            dataset_description = {
                "name": dataset_name,
                "id": dataset_id
            }

            if url:
                dataset_description['access']['url'] = url
                dataset_description['access']['serviceName'] = ''

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

        def _get_metadata_elements(elem):
            '''
            <metadata xlink:href="http://data.eol.ucar.edu/jedi/catalog/ucar.ncar.eol.project.
                ARCSS.metadata.xml" metadataType="THREDDS" inherited="false"/>

            there is no identifier for the metadata (for the inherited kind)
            '''
            # for any metadata element, and they are differently structured
            # could be nested at the catalogRef or dataset element level
            metadata_description = elem.attrib

            # and then go through for any child element

            return metadata_description

        def _get_catalog_ref(elem):
            '''
            <thredds:catalogRef name="2000" xlink:href="2000/catalog.xml" xlink:title="2000"
                xlink:type="simple" ID="/opendap/hyrax/allData/55/MOD17A3/2000/"/>
            '''
            return elem.attrib

        services = self.parser.find(svc_xpath)
        # ffs, services can be nested too
        if services:
            self._to_exclude.append(svc_xpath[1:])
            for key in services[0].attrib.keys():
                self._to_exclude.append(svc_xpath[1:] + '/@' + key)

            for service in services:
                service_endpoint = service.attrib
                children = service.xpath('*[local-name()="service"]')
                endpoints += [
                    dict(
                        chain(
                            child.attrib.items,
                            {
                                "childOf": service_endpoint['ID']
                            }.items()
                        )
                    ) for child in children
                ]
                if children:
                    service_endpoint['parentOf'] = []
                    service_endpoint['parentOf'] += [
                        child.attrib['ID'] for child in children
                    ]

        # get the level-one children (catalog->child)
        datasets = self.parser.find(dataset_xpath)
        if datasets:
            '''
            from the dataset children of the catalog, we can have
            additional dataset/catalogRef/metadata children or the dataset could have
            dataSize, date, and access elements

            or it could contain anything, we can't assume here.

            if it contains actual children, use the initial dataset description dict
            to define the parent relateionship
            '''
            self._to_exclude.append(dataset_xpath[1:])
            self._to_exclude += [dataset_xpath[1:] + '/@name', dataset_xpath[1:] + '/@ID']

            for dataset in datasets:
                # get the name and ID
                # and dataset description values (it's a singleton)
                d = _get_dataset_elements(dataset)

                dataset_endpoint = {
                    "name": d['name'],
                    "id": d['id']
                }

                if 'datasize' in d.keys():
                    dataset_endpoint["dataset_size"] = d['datasize']['size'],
                    dataset_endpoint["dataset_size_units"] = d['datasize']['units']

                if 'date' in d.keys():
                    dataset_endpoint["date"] = d['date']['date']
                    dataset_endpoint["date_type"] = d['date']['type']

                if 'access' in d.keys():
                    dataset_endpoint["relative_path"] = d['access']['url']
                    dataset_endpoint["relative_path_name"] = d['access']['serviceName']

                dataset_children = []

                # does it contain a metadata child?
                metadata_elem = next(iter(dataset.xpath('*[local-name()="metadata"]')), None)
                if metadata_elem is not None:
                    # get the link and type for a new endpoint.
                    metadata = _get_metadata_elements(metadata_elem)
                    if 'href' in metadata:
                        metadata.update({"childOf": d['id']})
                        endpoints += [metadata]
                    else:
                        # there's no identifiable endpoint
                        dataset_endpoint['metadata'] = metadata

                # does it contain catalogRef children?
                catalog_refs = dataset.xpath('*[local-name()="catalogRef"]')
                endpoints += [
                    dict(
                        chain(
                            _get_catalog_ref(cr).items(),
                            {
                                "childOf": d['id']
                            }.items()
                        )
                    ) for cr in catalog_refs
                ]

                dataset_children += [cr.attrib['ID'] for cr in catalog_refs]

                # does it contain dataset children?
                children = dataset.xpath('*[local-name()="dataset"]')
                endpoints += [
                    dict(
                        chain(
                            _get_dataset_elements(c).items(),
                            {
                                "childOf": d['id']
                            }.items()
                        )
                    ) for c in children
                ]
                dataset_children += [c.attrib['ID'] for c in children]

                if dataset_children:
                    d['parentOf'] = dataset_children

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
