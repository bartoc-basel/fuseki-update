from rdflib import Graph, Namespace, URIRef
import skosify
import logging
from utility.common import *
from utility.fuseki import put_graph
"""
This script downloads the Getty Vocabulary Program Ontology. Then makes some adjustments to it
to make it ready for upload into Skosmos. In a way to allow Skosmos to display it properly.
"""


def update_ontology(config):
    logger = logging.getLogger(__name__)

    ontology = 'http://vocab.getty.edu/ontology.rdf'
    path = config['data']['base'] + config['data']['vocabulary'] + 'getty/base_ontology/'
    file_name = 'getty-vocabulary-program-ontology'

    gvp = Namespace('http://vocab.getty.edu/ontology#')
    schema = Namespace('http://schema.org/')
    aat = Namespace('http://vocab.getty.edu/aat/')

    g = Graph()

    g.bind('gvp', gvp)
    g.bind('schema', schema)
    g.bind('aat', aat)

    logger.info('Load base ontology for getty!')
    g.parse(ontology, format='xml')
    logger.info('Finished download and parsing of %s. Begin processing.', ontology)

    logger.info('Add skos:prefLabel for rdfs:label.')
    add_skos_predicate_variant(g, RDFS.label, SKOS.prefLabel)
    # add_skos_predicate_variant(g, RDFS.comment, SKOS.definition)
    # add_skos_predicate_variant(g, DCTERMS.description, SKOS.scopeNote)
    add_skos_predicate_variant(g, RDFS.subClassOf, SKOS.broader)
    add_skos_predicate_variant(g, DC.title, SKOS.prefLabel)
    add_skos_predicate_variant(g, DC.identifier, SKOS.notation)
    add_skos_predicate_variant(g, RDFS.subPropertyOf, SKOS.broader)
    add_skos_predicate_variant(g, RDFS.isDefinedBy, SKOS.topConceptOf)

    # replace_triple_object(g, SKOS.ConceptScheme, SKOS.Concept)

    add_type(g, OWL.Ontology, SKOS.ConceptScheme)
    add_type(g, OWL.Class, SKOS.Concept)
    add_type(g, OWL.ObjectProperty, SKOS.Concept)
    make_top_concept(g, OWL.ObjectProperty, URIRef('http://vocab.getty.edu/ontology'))

    add_language_tags(g, 'en')

    logger.info('Begin serialization.')
    g.serialize(path + file_name + '.ttl', format='ttl')
    logger.info('Serialized base ontology and saved in %s.', path + file_name + '.ttl')

    file_name_skosified = file_name + '-skosified'
    voc = skosify.skosify(path + file_name + '.ttl')
    voc.serialize(path + file_name_skosified + '.ttl', format='ttl')

    put_graph('http://vocab.getty.edu/ontology', open(path + file_name_skosified + '.ttl'))