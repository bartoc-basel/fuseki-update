from rdflib.namespace import SKOS, RDF, RDFS, OWL, DCTERMS, DC, VOID, FOAF, XSD, XMLNS, DOAP


def add_skos_predicate_variant(graph, skos, predicate):
    for s, p, o in graph.triples((None, predicate, None)):
        if (s, skos, None) not in graph:
            graph.add((s, skos, o))


def add_type(graph, old, new):
    for s, p, o in graph.triples((None, RDF.type, old)):
        if (s, RDF.type, new) not in graph:
            graph.add((s, RDF.type, new))


def replace_triple_object(graph, old, new):
    for s, p, o in graph.triples((None, None, old)):
        if (s, p, new) not in graph:
            graph.remove((s, p, old))
            graph.add((s, p, new))