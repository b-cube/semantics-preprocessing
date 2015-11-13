from uuid import uuid4
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DC, DCTERMS, FOAF, XSD, OWL
from semproc.ontology import _ontology_uris


class RdfGrapher(object):
    '''
    take our json output from a preprocessor and
    generate an rdf graph to serialize as json-ld or turtle?

    to be decided...
    '''

    def __init__(self, data):
        self.graph = Graph()
        self._bind_namespaces()
        self.data = data

    def _bind_namespaces(self):
        # bind our lovely namespaces
        for prefix, uri in _ontology_uris.iteritems():
            self.graph.bind(prefix, uri)

    def _generate_predicate(self, prefix, name):
        return Namespace(_ontology_uris[prefix])[name]

    def _create_resource(self, resource_prefix, resource_type, identifier=''):
        # make a thing with a uuid as a urn
        # and just assign it to type if it's not overridden
        identifier = identifier if identifier else uuid4().urn
        resource = self.graph.resource(identifier)
        ref = Namespace(_ontology_uris[resource_prefix])[resource_type]
        resource.add(OWL.a, URIRef(ref))
        return resource

    def _process_catalog(self, entity):
        catalog_record = self._create_resource(
            'dcat', 'CatalogRecord', entity['object_id'])

        for pred, val in entity.iteritems():
            if pred in ['object_id', 'urls', 'relationships', 'datasets', 'webpages']:
                continue
            if not val:
                continue
            prefix, name = pred.split(':')
            val = [val] if not isinstance(val, list) else val

            for v in val:
                catalog_record.add(
                    self._generate_predicate(
                        prefix, name),
                    Literal(v)
                )

        for url in entity.get('urls', []):
            self._handle_url(url)
            # catalog_record.add(
            #     self._generate_predicate(
            #         'bcube', 'hasUrl'), URIRef(url.get('object_id'))
            # )

        for webpage in entity.get('webpages', []):
            self._hande_webpage(webpage)

        for relationship in entity['relationships']:
            # so. current object, verb, id of object, existence unknown
            self.relates.append(
                (catalog_record, relationship['relate'],
                    relationship['object_id'])
            )

    def _handle_webpage(self, webpage):
        entity = self._create_resource(
            'bibo', 'WebPage', webpage.get('object_id')
        )
        for relationship in webpage['relationships']:
            self.relates.append(
                (entity, relationship['relate'],
                    relationship['object_id'])
            )

    def _handle_url(self, url):
        entity = self._create_resource(
            'bcube', 'Url', url.get('object_id')
        )
        for k, v in url.iteritems():
            if k == 'object_id':
                continue
            prefix, name = k.split(':')

            entity.add(
                self._generate_predicate(
                    prefix, name), Literal(v)
            )

    def _handle_temporal(self, temporal):
        for option in ['startDate', 'endDate']:
            # NOTE: make these iso 8601 first
            d = temporal.get('esip:' + option)
            if not d:
                continue

            yield (
                self._generate_predicate('esip', option),
                Literal(d, datatype=XSD.date)
            )

    def _handle_spatial(self, spatial):
        for key, val in spatial.iteritems():
            if not val:
                continue

            literal = Literal(val) if key == 'dc:spatial' else Literal(
                float(val), datatype=XSD.float
            )
            pred = self._generate_predicate(
                key.split(':')[0], key.split(':')[-1]
            )
            yield (pred, literal)

    def _process_service(self, entity):
        service = self._create_resource(
            'bcube',
            'service',
            entity['object_id']
        )

        for pred, val in entity.iteritems():
            if pred in ['object_id', 'relationships']:
                continue
            if not val:
                continue
            prefix, name = pred.split(':')
            val = [val] if not isinstance(val, list) else val

            for v in val:
                service.add(
                    self._generate_predicate(
                        prefix, name),
                    Literal(v)
                )

        # TODO: at some point, this might have operations, params, etc

        if 'temporal_extent' in entity:
            for temporal_predicate, temporal_value in self._handle_temporal(
                    entity['temporal_extent']):
                service.add(temporal_predicate, temporal_value)

        if 'spatial_extent' in entity:
            for spatial_predicate, spatial_value in self._handle_spatial(
                    entity['spatial_extent']):
                service.add(spatial_predicate, spatial_value)

        for relationship in entity['relationships']:
            self.relates.append(
                (service, relationship['relate'], relationship['object_id']))

    def _process_dataset(self, entity):
        dataset = self._create_resource('dcat', 'Dataset', entity['object_id'])
        for pred, val in entity.iteritems():
            if pred in ['object_id', 'relationships', 'temporal_extent', 'spatial_extent', 'urls']:
                continue
            if not val:
                continue
            prefix, name = pred.split(':')
            val = [val] if not isinstance(val, list) else val

            for v in val:
                dataset.add(
                    self._generate_predicate(
                        prefix, name),
                    Literal(v)
                )

        if 'temporal_extent' in entity:
            for temporal_predicate, temporal_value in self._handle_temporal(
                    entity['temporal_extent']):
                dataset.add(temporal_predicate, temporal_value)

        if 'spatial_extent' in entity:
            for spatial_predicate, spatial_value in self._handle_spatial(
                    entity['spatial_extent']):
                dataset.add(spatial_predicate, spatial_value)

        for url in entity.get('urls', []):
            self._handle_url(url)

        for relationship in entity['relationships']:
            self.relates.append(
                (dataset, relationship['relate'], relationship['object_id']))

    def _process_keywords(self, entity):
        for keywords in entity:
            keyset = self._create_resource(
                'bcube', 'thesaurusSubset', keywords['object_id'])
            for pred, val in keywords.iteritems():
                if pred in ['object_id']:
                    continue
                if not val:
                    continue
                prefix, name = pred.split(':')
                val = [val] if not isinstance(val, list) else val

                for v in val:
                    keyset.add(
                        self._generate_predicate(
                            prefix, name),
                        Literal(v)
                    )

    def _process_publisher(self, entity):
        publisher = self._create_resource(
            'dcat', 'publisher', entity['object_id'])
        if 'location' in entity:
            publisher.add(
                DC.location, Literal(entity['location']))
        publisher.add(FOAF.name, Literal(entity['name']))

    def emit_format(self):
        return self.graph.serialize(format='turtle', encoding='utf-8')

    def serialize(self):
        '''
        not a word
        so from our json.

        this. is. idk. an ordering thing. i suspect the graph borks
        when you try to add a triple for a non-existent object.
        years of experience. also, i am wrong - it will add anything.

        grapher = RdfGrapher(data)
        grapher.serialize()
        grapher.emit_format()  # to turtle here
        '''
        self.relates = []
        for entity_type, entity in self.data.iteritems():
            if entity_type == 'catalog_record':
                self._process_catalog(entity)
            elif entity_type == 'datasets':
                for dataset in entity:
                    self._process_dataset(dataset)
            elif entity_type == 'services':
                for service in entity:
                    self._process_service(service)
            elif entity_type == 'publisher':
                self._process_publisher(entity)
            elif entity_type == 'keywords':
                self._process_keywords(entity)
            # elif entity_type == 'webpages':
            #     self._process_webpages(entity)
            else:
                continue

        for resource, verb, object_id in self.relates:
            prefix, name = verb.split(':')
            resource.add(
                self._generate_predicate(prefix, name),
                URIRef(object_id)
            )
