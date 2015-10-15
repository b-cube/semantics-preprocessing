import json
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

    def _identify_prefix(self, predicate):
        # this is, granted, a lesson in technical debt.
        debt = {
            "dc": ["description", "conformsTo", "relation"],
            "dcat": ["publisher"],
            "foaf": ["primaryTopic"],
            "vcard": ["hasUrl"],
            "bcube": [
                "Url",
                "dateCreated",
                "lastUpdated",
                "atTime",
                "statusCodeValue",
                "reasonPhrase",
                "HTTPStatusFamilyCode",
                "HTTPStatusFamilyType",
                "hasUrlSource",
                "hasConfidence",
                "validatedOn"
            ]
        }

        for k, v in debt.iteritems():
            if predicate in v:
                return k
        return ''

    def _stringify(self, text):
        # TODO: this still has encoding issues!
        # return json.dumps(text)
        return text

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

        # our potential hash (this is idiotic) as pred, key
        options = [
            ('dateCreated', 'dateCreated'),
            ('lastUpdated', 'lastUpdated'),
            # ('atTime', 'atTime'),
            # ('statusCodeValue', 'statusCodeValue'),
            # ('reasonPhrase', 'reasonPhrase'),
            # ('HTTPStatusFamilyCode', 'HTTPStatusFamilyCode'),
            # ('HTTPStatusFamilyType', 'HTTPStatusFamilyType'),
            # ('hasUrlSource', 'hasUrlSource'),
            # ('hasConfidence', 'hasConfidence'),
            # ('validatedOn', 'validatedOn')
        ]

        for pred, key in options:
            val = entity.get(key, None)
            if not val:
                continue
            catalog_record.add(
                self._generate_predicate(
                    self._identify_prefix(pred),
                    pred), Literal(val)
            )

        for url in entity.get('urls', []):
            catalog_record.add(
                self._generate_predicate(
                    'bcube', 'has'), url.get('object_id')
            )
            self._handle_url(url)

        for conforms in entity.get('conformsTo', []):
            catalog_record.add(DC.conformsTo, Literal(conforms))

        for relationship in entity['relationships']:
            # so. current object, verb, id of object, existence unknown
            self.relates.append(
                (catalog_record, relationship['relate'],
                    relationship['object_id'])
            )

    def _handle_url(self, url):
        entity = self._create_resource(
            'bcube', 'Url', url.get('object_id')
        )
        for k, v in url.iteritems():
            if k == 'object_id':
                continue

            entity.add(
                self._generate_predicate(
                    self._identify_prefix(k),
                    k), Literal(v)
            )

        # return entity

    def _handle_temporal(self, temporal):
        for option in ['startDate', 'endDate']:
            # NOTE: make these iso 8601 first
            d = temporal.get(option)
            if not d:
                continue

            yield (
                self._generate_predicate('esip', option),
                Literal(d, datatype=XSD.date)
            )

    def _handle_spatial(self, spatial):
        options = [
            ('wkt', DC.spatial),
            ('west', 'esip:westBound'),
            ('east', 'esip:eastBound'),
            ('north', 'esip:northBound'),
            ('south', 'esip:southBound')
        ]

        for key, predicate in options:
            blob = spatial.get(key)
            if not blob:
                continue

            pred = self._generate_predicate(
                predicate.split(':')[0], predicate.split(':')[-1]
            ) if key != 'wkt' else predicate

            literal = Literal(blob) if key == 'wkt' else Literal(
                float(blob), datatype=XSD.float
            )
            yield (pred, literal)

    def _process_service(self, entity):
        service = self._create_resource(
            'prov',
            'DataProvidingService',
            entity['object_id']
        )
        if entity['identifier']:
            service.add(DCTERMS.identifier, Literal(entity['identifier']))
        service.add(
            DCTERMS.title, Literal(self._stringify(entity['title'])))
        service.add(
            DC.description, Literal(self._stringify(entity['abstract'])))
        service.add(
            self._generate_predicate('bcube', 'dateCreated'),
            Literal(entity['dateCreated']))
        service.add(
            self._generate_predicate('bcube', 'lastUpdated'),
            Literal(entity['lastUpdated']))

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
        if entity['identifier']:
            dataset.add(DCTERMS.identifier, Literal(entity['identifier']))
        dataset.add(
            DCTERMS.title, Literal(self._stringify(entity['title'])))
        dataset.add(
            DC.description, Literal(self._stringify(entity['abstract'])))
        dataset.add(
            self._generate_predicate('bcube', 'dateCreated'),
            Literal(entity['dateCreated']))
        dataset.add(
            self._generate_predicate('bcube', 'lastUpdated'),
            Literal(entity['lastUpdated']))

        if 'temporal_extent' in entity:
            for temporal_predicate, temporal_value in self._handle_temporal(
                    entity['temporal_extent']):
                dataset.add(temporal_predicate, temporal_value)

        if 'spatial_extent' in entity:
            for spatial_predicate, spatial_value in self._handle_spatial(
                    entity['spatial_extent']):
                dataset.add(spatial_predicate, spatial_value)

        for relationship in entity['relationships']:
            self.relates.append(
                (dataset, relationship['relate'], relationship['object_id']))

    def _process_keywords(self, entity):
        for keywords in entity:
            keyset = self._create_resource(
                'bcube', 'thesaurusSubset', keywords['object_id'])
            if 'type' in keywords:
                keyset.add(
                    DC.hasType,
                    Literal(self._stringify(keywords['type']))
                )
            if 'thesaurus' in keywords:
                keyset.add(
                    DC.partOf,
                    Literal(self._stringify(keywords['thesaurus']))
                )

            try:
                for term in keywords['terms']:
                    keyset.add(
                        self._generate_predicate('bcube', 'hasValue'),
                        Literal(self._stringify(term))
                    )
            except:
                print keywords

    def _process_publisher(self, entity):
        publisher = self._create_resource(
            'dcat', 'publisher', entity['object_id'])
        if 'location' in entity:
            publisher.add(
                DC.location, Literal(self._stringify(entity['location'])))
        publisher.add(FOAF.name, Literal(self._stringify(entity['name'])))

    def _process_webpages(self, entity):
        for webpage in entity:
            relation = self._create_resource(
                'bibo', 'WebPage', webpage['object_id'])
            relation.add(
                self._generate_predicate('vcard', 'hasURL'),
                Literal(webpage['url'])
            )

    def emit_format(self):
        return self.graph.serialize(format='turtle')

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
            elif entity_type == 'webpages':
                self._process_webpages(entity)
            else:
                continue

        for resource, verb, object_id in self.relates:
            resource.add(
                self._generate_predicate(
                    self._identify_prefix(verb), verb),
                URIRef(object_id)
            )
