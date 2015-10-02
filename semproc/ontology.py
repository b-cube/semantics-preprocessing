# ontology-related globals

from rdflib.namespace import DC, DCTERMS, FOAF, XSD, OWL

# some namespaces
_ontology_uris = {
    'bcube': 'http://purl.org/BCube/#',
    'vcard': 'http://www.w3.org/TR/vcard-rdf/#',
    'esip': 'http://purl.org/esip/#',
    'vivo': 'http://vivo.ufl.edu/ontology/vivo-ufl/#',
    'bibo': 'http://purl.org/ontology/bibo/#',
    'dcat': 'http://www.w3.org/TR/vocab-dcat/#',
    "prov": "http://purl.org/net/provenance/ns#",
    'dc': str(DC),
    'dct': str(DCTERMS),
    'foaf': str(FOAF),
    'xsd': str(XSD),
    'owl': str(OWL)
}
