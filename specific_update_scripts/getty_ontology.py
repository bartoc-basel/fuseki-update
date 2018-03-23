from rdflib import Graph, Namespace, URIRef
import skosify
import logging
from utility.common import *
from utility.fuseki import put_graph
"""
This script downloads the Getty Vocabulary Program Ontology. Then makes some adjustments to it
to make it ready for upload into Skosmos. In a way to allow Skosmos to display it properly.
"""


def update(config):
    logger = logging.getLogger(__name__)

    ontology = 'http://vocab.getty.edu/ontology.rdf'
    path = config['data']['base'] + config['data']['vocabulary'] + 'getty/base_ontology/'
    file_name = 'getty-vocabulary-program-ontology'

    GVP = Namespace('http://vocab.getty.edu/ontology#')
    SCHEMA = Namespace('http://schema.org/')
    AAT = Namespace('http://vocab.getty.edu/aat/')
    ULAN = Namespace('http://vocab.getty.edu/ulan/')
    TGN = Namespace('http://vocab.getty.edu/tgn/')


    g = Graph()

    g.bind('gvp', GVP)
    g.bind('schema', SCHEMA)
    # g.bind('aat', AAT)

    logger.info('Load base ontology for getty!')
    g.parse(ontology, format='xml')
    logger.info('Finished download and parsing of %s. Begin processing.', ontology)

    logger.info('Add skos:prefLabel for rdfs:label.')

    g.add((SKOS.related, RDF.type, RDF.Property))
    g.add((SKOS.related, RDF.type, OWL.ObjectProperty))
    g.add((SKOS.related, RDF.type, OWL.SymmetricProperty))
    g.add((SKOS.related, RDFS.label, Literal('has related', lang='en')))
    g.add((SKOS.related, RDFS.comment, Literal('skos:related is disjoint with skos:broaderTransitive', lang='en')))
    g.add((SKOS.related, RDFS.isDefinedBy, URIRef('http://www.w3.org/2004/02/skos/core')))
    g.add((SKOS.related, RDFS.subPropertyOf, SKOS.semanticRelation))
    g.add((SKOS.related, SKOS.inScheme, URIRef('http://www.w3.org/2004/02/skos/core')))

    # remove_subject(g, URIRef('http://vocab.getty.edu/aat/'))
    # remove_subject(g, URIRef('http://vocab.getty.edu/ulan/'))
    # remove_subject(g, URIRef('http://vocab.getty.edu/tgn/'))

    add_type(g, OWL.Ontology, SKOS.ConceptScheme)
    add_type(g, OWL.Class, SKOS.Concept)
    add_type(g, OWL.ObjectProperty, SKOS.Concept)

   # set_in_scheme(g, URIRef('http://vocab.getty.edu/ontology'))

    add_skos_predicate_variant(g, RDFS.isDefinedBy, SKOS.inScheme)

    # label transformations
    # add_skos_predicate_variant(g, RDFS.label, SKOS.prefLabel)
    # add_skos_predicate_variant(g, DC.title, SKOS.prefLabel)
    add_skos_predicate_variant(g, DC.identifier, SKOS.notation)
    add_language_tags(g, 'en')

    # add_skos_predicate_variant(g, RDFS.comment, SKOS.definition)
    # add_skos_predicate_variant(g, DCTERMS.description, SKOS.scopeNote)

    # relations transformations
    add_skos_predicate_variant(g, RDFS.subClassOf, SKOS.broader)
    add_skos_predicate_variant(g, RDFS.subPropertyOf, SKOS.broader)
    # add_skos_predicate_variant(g, RDFS.isDefinedBy, SKOS.topConceptOf)

    # replace_triple_object(g, SKOS.ConceptScheme, SKOS.Concept)

    logger.info('Begin serialization.')
    g.serialize(path + file_name + '.ttl', format='ttl')
    logger.info('Serialized base ontology and saved in %s.', path + file_name + '.ttl')

    file_name_skosified = file_name + '-skosified'
    voc = skosify.skosify(path + file_name + '.ttl')
    voc.serialize(path + file_name_skosified + '.ttl', format='ttl')

    put_graph('http://vocab.getty.edu/ontology', open(path + file_name_skosified + '.ttl'))