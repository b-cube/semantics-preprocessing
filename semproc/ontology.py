# ontology-related globals

from rdflib.namespace import DC, DCTERMS, FOAF, XSD, OWL, RDF

# some namespaces
_ontology_uris = {
    'bcube': 'http://purl.org/BCube/#',
    'vcard': 'http://www.w3.org/TR/vcard-rdf/#',
    'esip': 'http://purl.org/esip/#',
    # 'vivo': 'http://vivo.ufl.edu/ontology/vivo-ufl/#',
    'bibo': 'http://purl.org/ontology/bibo/#',
    'dcat': 'http://www.w3.org/TR/vocab-dcat/#',
    'dc': str(DC),
    'dcterms': str(DCTERMS),
    'foaf': str(FOAF),
    'xsd': str(XSD),
    'owl': str(OWL),
    'rdf': str(RDF)
}
