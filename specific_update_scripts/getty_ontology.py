from rdflib import Graph
import skosify
import logging
from utility.common import *
"""
This script downloads the Getty Vocabulary Program Ontology. Then makes some adjustments to it
to make it ready for upload into Skosmos. In a way to allow Skosmos to display it properly.
"""


def update_ontology(config):
    logger = logging.getLogger(__name__)

    ontology = 'http://vocab.getty.edu/ontology.rdf'
    path = config['data']['base'] + config['data']['vocabulary'] + 'getty/base_ontology/'
    file_name = 'getty_vocabulary_program_ontology'

    g = Graph()

    logger.info('Load base ontology for getty!')
    g.parse(ontology, format='xml')
    logger.info('Finished download and parsing of %s. Begin processing.', ontology)

    logger.info('Add skos:prefLabel for rdfs:label.')
    add_skos_preflabels(g, RDFS.label)

    logger.info('Begin serialization.')
    g.serialize(path + file_name + '.rdf', format='xml')
    logger.info('Serialized base ontology and saved in %s.', path + file_name + '.rdf')

    voc = skosify.skosify(path + file_name + '.rdf')
    voc.serialize(path + file_name + '.ttl', format='ttl')