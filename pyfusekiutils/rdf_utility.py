from rdflib import Literal
from rdflib.namespace import SKOS, RDF, RDFS, OWL, DCTERMS, DC, VOID, FOAF, XSD, XMLNS, DOAP

"""Common utility functions to manipulate RDF Triple Graphs."""


def remove_subject(graph, uri):
    """Remove all triples of a subject.

    :param graph:   The graph from which the triples will be removed.
    :param uri:     The uri of the subject that will be removed. (URIRef)
    :return:
    """
    for (s, p, o) in graph.triples((uri, None, None)):
        graph.remove((s, p, o))


def add_skos_predicate_variant(graph, old, new):
    for s, p, o in graph.triples((None, old, None)):
        if (s, new, o) not in graph:
            graph.add((s, new, o))


def add_type(graph, old, new):
    for s, p, o in graph.triples((None, RDF.type, old)):
        if (s, RDF.type, new) not in graph:
            graph.add((s, RDF.type, new))


def replace_triple_object(graph, old, new):
    for s, p, o in graph.triples((None, None, old)):
        graph.remove((s, p, o))
        if (s, p, new) not in graph:
            graph.add((s, p, new))


def make_top_concept(graph, type, scheme):
    for s, p, o in graph.triples((None, RDF.type, type)):
        if (s, SKOS.topConceptOf, scheme) not in graph:
            if (s, SKOS.broader, None) not in graph:
                graph.add((s, SKOS.topConceptOf, scheme))


def explicit_import(graph):
    for (_, _, o) in graph.triples((None, OWL.imports, None)):
        graph.parse(o.n3().strip('<>'))


def expand_inverse_of_relations(graph, first, second):
    for (s, p, o) in graph.triples((None, first, None)):
        if (o, second, s) not in graph:
            graph.add((o, second, s))


def set_in_scheme(graph, scheme):
    for (s, _, _) in graph.triples((None, RDF.type, SKOS.Concept)):
        if (s, SKOS.inScheme, None) not in graph:
            graph.add((s, SKOS.inScheme, scheme))


def add_language_tags(graph, tag):
    for (subject, predicate, obj) in graph.triples((None, SKOS.prefLabel, None)):
        graph.remove((subject, predicate, obj))
        graph.add((subject, predicate, Literal(obj.value, lang=tag)))

    for (subject, predicate, obj) in graph.triples((None, SKOS.altLabel, None)):
        graph.remove((subject, predicate, obj))
        graph.add((subject, predicate, Literal(obj.value, lang=tag)))

    for (subject, predicate, obj) in graph.triples((None, SKOS.hiddenLabel, None)):
        graph.remove((subject, predicate, obj))
        graph.add((subject, predicate, Literal(obj.value, lang=tag)))

    for (subject, predicate, obj) in graph.triples((None, RDFS.label, None)):
        graph.remove((subject, predicate, obj))
        graph.add((subject, predicate, Literal(obj.value, lang=tag)))

