from uuid import uuid4
from rdflib import Graph, Literal, Namespace, URIRef
# from rdflib.namespace import DC, DCTERMS, FOAF, XSD, OWL
from rdflib.namespace import XSD, OWL, FOAF
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

        self._handle_triples(
            entity,
            catalog_record,
            [
                'object_id',
                'urls',
                'relationships',
                'datasets',
                'webpages',
                'services'
            ]
        )

        for url in entity.get('urls', []):
            self._handle_url(url)

        for webpage in entity.get('webpages', []):
            self._handle_webpage(webpage)

        for relationship in entity.get('relationships', []):
            # so. current object, verb, id of object, existence unknown
            self.relates.append(
                (catalog_record, relationship['relate'],
                    relationship['object_id'])
            )

    def _handle_webpage(self, webpage):
        entity = self._create_resource(
            'bibo', 'WebPage', webpage.get('object_id')
        )
        for relationship in webpage.get('relationships', []):
            self.relates.append(
                (entity, relationship['relate'],
                    relationship['object_id'])
            )

    def _handle_url(self, url):
        entity = self._create_resource(
            'bcube', 'Url', url.get('object_id')
        )
        self._handle_triples(url, entity, ['object_id'])

    def _handle_layer(self, layer):
        entity = self._create_resource(
            "bcube", 'Layer', layer.get('object_id')
        )
        self._handle_triples(layer, entity, ['object_id', 'relationships'])

        for relationship in layer.get('relationships', []):
            self.relates.append(
                (entity, relationship['relate'], relationship['object_id']))

    def _handle_triples(self, entity, thing, excludes):
        # today in badly named things, entity is the
        # json blob, thing is the parent rdf object
        for pred, val in entity.iteritems():
            if pred in excludes:
                continue
            if not val:
                continue
            prefix, name = pred.split(':')
            val = [val] if not isinstance(val, list) else val

            for v in val:
                if name in [
                        'westBound', 'eastBound', 'northBound', 'southBound']:
                    literal = Literal(float(v), datatype=XSD.float)
                elif name in ['startDate', 'endDate']:
                    literal = Literal(v, datatype=XSD.date)
                else:
                    literal = Literal(v)

                thing.add(
                    self._generate_predicate(
                        prefix, name),
                    literal
                )

    def _process_service(self, entity):
        service = self._create_resource(
            'bcube',
            'service',
            entity['object_id']
        )

        self._handle_triples(
            entity,
            service,
            ['object_id', 'urls', 'relationships', 'webpages', 'layers']
        )

        for layer in entity.get('layers', []):
            self._handle_layer(layer)

        for url in entity.get('urls', []):
            self._handle_url(url)

        for wp in entity.get('webpages', []):
            self._handle_webpage(wp)

        for relationship in entity.get('relationships', []):
            self.relates.append(
                (service, relationship['relate'], relationship['object_id']))

    def _process_dataset(self, entity):
        dataset = self._create_resource('dcat', 'Dataset', entity['object_id'])
        self._handle_triples(
            entity, dataset, ['object_id', 'relationships', 'urls'])

        for url in entity.get('urls', []):
            self._handle_url(url)

        for relationship in entity.get('relationships', []):
            self.relates.append(
                (dataset, relationship['relate'], relationship['object_id']))

    def _process_keywords(self, entity):
        for keywords in entity:
            keyset = self._create_resource(
                'bcube', 'thesaurusSubset', keywords['object_id'])

            self._handle_triples(keywords, keyset, ['object_id'])

    def _process_publisher(self, entity):
        publisher = self._create_resource(
            'foaf', 'Organization', entity['object_id'])
        # if 'location' in entity:
        #     publisher.add(
        #         DC.location, Literal(entity['location']))
        publisher.add(FOAF.name, Literal(entity['name']))

    def emit_format(self):
        return self.graph.serialize(format='turtle', encoding='utf-8')

    def serialize(self):
        '''
        grapher = RdfGrapher(data)
        grapher.serialize()
        grapher.emit_format()  # to turtle here
        '''
        self.relates = []
        for entity_type, entity in self.data.iteritems():
            if entity_type == 'catalog_records':
                for catalog_record in entity:
                    self._process_catalog(catalog_record)
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
