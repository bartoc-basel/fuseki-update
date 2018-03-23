from rdflib import Graph, Namespace
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
    file_name = 'getty_vocabulary_program_ontology'

    gvp = Namespace('http://vocab.getty.edu/ontology#')
    schema = Namespace('http://schema.org/')

    g = Graph()

    g.bind('gvp', gvp)
    g.bind('schema', schema)

    logger.info('Load base ontology for getty!')
    g.parse(ontology, format='xml')
    logger.info('Finished download and parsing of %s. Begin processing.', ontology)

    logger.info('Add skos:prefLabel for rdfs:label.')
    add_skos_predicate_variant(g, SKOS.prefLabel, RDFS.label)
    add_skos_predicate_variant(g, SKOS.definition, RDFS.comment)
    add_skos_predicate_variant(g, SKOS.scopeNote, DCTERMS.description)
    add_skos_predicate_variant(g, SKOS.broader, RDFS.subClassOf)
    add_skos_predicate_variant(g, SKOS.ConceptScheme, OWL.Ontology)
    add_skos_predicate_variant(g, SKOS.Concept, OWL.Class)

    add_type(g, OWL.Ontology, SKOS.ConceptScheme)
    add_type(g, OWL.Class, SKOS.Concept)
    add_type(g, OWL.ObjectProperty, SKOS.Concept)

    replace_triple_object(g, SKOS.ConceptScheme, SKOS.Concept)



    logger.info('Begin serialization.')
    g.serialize(path + file_name + '.rdf', format='xml')
    logger.info('Serialized base ontology and saved in %s.', path + file_name + '.rdf')

    voc = skosify.skosify(path + file_name + '.rdf')
    voc.serialize(path + file_name + '.ttl', format='ttl')

    put_graph('http://vocab.getty.edu/ontology', open(path + file_name + '.ttl'))