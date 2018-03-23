from rdflib.namespace import SKOS, RDF, RDFS, OWL


def add_skos_preflabels(graph, predicate):
    for s, p, o in graph.triples((None, predicate, None)):
        if (s, SKOS.prefLabel, None) not in graph:
            graph.add((s, SKOS.prefLabel, o))
