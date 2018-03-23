from rdflib import Graph, Namespace, URIRef
import skosify
import logging
from utility.common import *
from utility.fuseki import put_graph
"""
This scripts imports SKOS into Skosmos.
"""

def update(config):
    logger = logging.getLogger(__name__)

    ontology = 'http://www.w3.org/2004/02/skos/core'
    path = config['data']['base'] + config['data']['vocabulary'] + 'skos/'
    file_name = 'skos-core'

    g = Graph()

    g.parse(ontology)

    add_type(g, OWL.Ontology, SKOS.ConceptScheme)
    add_type(g, OWL.Class, SKOS.Concept)
    add_type(g, OWL.ObjectProperty, SKOS.Concept)
    add_type(g, OWL.AnnotationProperty, SKOS.Concept)
    add_type(g, OWL.DatatypeProperty, SKOS.Concept)
    add_type(g, RDF.Property, SKOS.Concept)

    add_skos_predicate_variant(g, RDFS.label, SKOS.prefLabel)
    add_skos_predicate_variant(g, DC.title, SKOS.prefLabel)
    add_skos_predicate_variant(g, DC.identifier, SKOS.notation)
    add_language_tags(g, 'en')

    add_skos_predicate_variant(g, RDFS.subClassOf, SKOS.broader)
    add_skos_predicate_variant(g, RDFS.subPropertyOf, SKOS.broader)

    g.serialize(path + file_name + '.ttl', format='ttl')

    file_name_skosified = file_name + '-skosified'
    voc = skosify.skosify(path + file_name + '.ttl')
    voc.serialize(path + file_name_skosified + '.ttl', format='ttl')

    put_graph(ontology, open(path + file_name_skosified + '.ttl'))