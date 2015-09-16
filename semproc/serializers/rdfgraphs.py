import rdflib
import hashlib
import json
from uuid import uuid4
from rdflib import Graph, Literal, RDF, RDFS, Namespace, URIRef
from rdflib.namespace import DC, DCTERMS, FOAF, XSD, OWL

'''
json serializer?
'''


class RdfGrapher():
    '''
    take our json output from a preprocessor and
    generate an rdf graph to serialize as json-ld or turtle?

    to be decided...
    '''

    # some namespaces
    _ontology_uris = {
        'bcube': 'http://purl.org/BCube/#',
        'vcard': 'http://www.w3.org/TR/vcard-rdf/#',
        'esip': 'http://purl.org/esip/#',
        'vivo': 'http://vivo.ufl.edu/ontology/vivo-ufl/#',
        'bibo': 'http://purl.org/ontology/bibo/#',
        'dcat': 'http://www.w3.org/TR/vocab-dcat/#',
        'dc': str(DC),
        'dct': str(DCTERMS),
        'foaf': str(FOAF),
        'xsd': str(XSD),
        'owl': str(OWL)
    }

    def __init__(self, data):
        self.graph = Graph()
        self._bind_namespaces()
        self.data = data

    def _bind_namespaces(self):
        # bind our lovely namespaces
        for prefix, uri in self._ontology_uris.iteritems():
            self.graph.bind(prefix, uri)

    def _generate_predicate(self, prefix, name):
        return Namespace(self._ontology_uris[prefix])[name]

    def _identify_prefix(self, predicate):
        # this is, granted, a lesson in technical debt.
        debt = {
            "dc": ["description", "conformsTo", "relation"],
            "dcat": ["publisher"],
            "foaf": ["primaryTopic"]
        }

        for k, v in debt.iteritems():
            if predicate in v:
                return k
        return ''

    def _stringify(self, text):
        # TODO: this still has encoding issues!
        return json.dumps(text)

    def _create_resource(self, resource_prefix, resource_type, identifier=''):
        # make a thing with a uuid as a urn
        # and just assign it to type if it's not overridden
        identifier = identifier if identifier else uuid4().urn
        resource = self.graph.resource(identifier)
        ref = Namespace(self._ontology_uris[resource_prefix])[resource_type]
        resource.add(OWL.a, URIRef(ref))
        return resource

    def _process_catalog(self, entity):
        catalog_record = self._create_resource('dcat', 'CatalogRecord', entity['object_id'])
        catalog_record.add(self._generate_predicate('vcard', 'hasURL'), Literal(entity['url']))
        catalog_record.add(self._generate_predicate('vivo', 'harvestDate'), Literal(entity['harvestDate']))
        if entity['conformsTo']:
            catalog_record.add(DC.conformsTo, Literal(entity['conformsTo']))

        for relationship in entity['relationships']:
            # so. current object, verb, id of object, existence unknown
            self.relates.append((catalog_record, relationship['relate'], relationship['object_id']))

    def _process_dataset(self, entity):
        dataset = self._create_resource('dcat', 'Dataset', entity['object_id'])
        if entity['identifier']:
            dataset.add(DCTERMS.identifier, Literal(entity['identifier']))
        dataset.add(DCTERMS.title, Literal(self._stringify(entity['title'])))
        dataset.add(DC.description, Literal(self._stringify(entity['abstract'])))

        if 'temporal_extent' in entity:
            # NOTE: make these iso 8601 first
            begdate = entity['temporal_extent'].get('startDate')
            enddate = entity['temporal_extent'].get('endDate')

            dataset.add(self._generate_predicate('esip', 'startDate'), Literal(begdate, datatype=XSD.date))
            dataset.add(self._generate_predicate('esip', 'endDate'), Literal(enddate, datatype=XSD.date))

        if 'spatial_extent' in entity:
            dataset.add(DC.spatial, Literal(entity['spatial_extent']['wkt']))

            # a small not good thing.
            dataset.add(self._generate_predicate('esip', 'westBound'),
                        Literal(float(entity['spatial_extent']['west']), datatype=XSD.float))

            dataset.add(self._generate_predicate('esip', 'eastBound'),
                        Literal(float(entity['spatial_extent']['east']), datatype=XSD.float))

            dataset.add(self._generate_predicate('esip', 'southBound'),
                        Literal(float(entity['spatial_extent']['south']), datatype=XSD.float))

            dataset.add(self._generate_predicate('esip', 'northBound'),
                        Literal(float(entity['spatial_extent']['north']), datatype=XSD.float))
        
        for relationship in entity['relationships']:
            self.relates.append((dataset, relationship['relate'], relationship['object_id']))
        
    def _process_keywords(self, entity):
        for keywords in entity:
            keyset = self._create_resource('bcube', 'thesaurusSubset', keywords['object_id'])
            if 'type' in keywords:
                keyset.add(DC.hasType, Literal(self._stringify(keywords['type'])))
            if 'thesaurus' in keywords:
                keyset.add(DC.partOf, Literal(self._stringify(keywords['thesaurus'])))

            try:
                for term in keywords['terms']:
                    keyset.add(self._generate_predicate('bcube', 'hasValue'), Literal(self._stringify(term)))
            except:
                print keywords

    def _process_publisher(self, entity):
        publisher = self._create_resource('dcat', 'publisher', entity['object_id'])
        if 'location' in entity:
            publisher.add(DC.location, Literal(self._stringify(entity['location'])))
        publisher.add(FOAF.name, Literal(self._stringify(entity['name'])))

    def _process_webpages(self, entity):
        for webpage in entity:
            relation = self._create_resource('bibo', 'WebPage', webpage['object_id'])
            relation.add(self._generate_predicate('vcard', 'hasURL'), Literal(webpage['url']))

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
            elif entity_type == 'dataset':
                self._process_dataset(entity)
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
