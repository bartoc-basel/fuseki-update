import logging
import zipfile
import io
import os

import requests
import skosify
from rdflib import Graph, Namespace, URIRef
from rdflib.util import guess_format

from pyfusekiutil.fuseki_utility import put_graph
from pyfusekiutil.rdf_utility import *

"""Various update functions for Thesauri/Ontologies which are not in SKOS or proper SKOS."""


def update_yarn(config, download=False):
    """Download and transform Yet Another RussNet."""

    path = config['data']['base'] + config['data']['vocabulary'] + 'rus/'
    if not os.path.exists(path):
        os.mkdir(path)

    file_name = 'yarn'

    LEMON = Namespace('http://lemon-model.net/lemon#')

    logging.info('Download graph.')
    g = Graph()

    g.bind('lemon', LEMON)
    g.bind('lexinfo', Namespace('http://www.lexinfo.net/ontology/2.0/lexinfo#'))

    g.parse('http://depot.nlpub.ru/rtlod/yarn.ttl', format='ttl')

    add_skos_predicate_variant(g, RDFS.label, SKOS.prefLabel)

    voc = skosify.skosify(g, mark_top_concepts=True,
                          eliminate_redundancy=True, break_cycles=True, keep_related=False,
                          cleanup_classes=True, cleanup_properties=True, cleanup_unreachable=True)
    voc.serialize(path + file_name + '.ttl', format='ttl')

    put_graph('http://depot.nlpub.ru/rtlod/yarn.ttl', open(path + file_name + '.ttl').read())


def update_unldc(config, download=False):
    """Download and transform Universal Dictionary Concepts."""

    path = config['data']['base'] + config['data']['vocabulary'] + 'rus/'
    if not os.path.exists(path):
        os.mkdir(path)

    file_name = 'unldc'

    LEMON = Namespace('http://lemon-model.net/lemon#')

    logging.info('Download graph.')
    g = Graph()

    g.bind('lemon', LEMON)
    g.bind('lexinfo', Namespace('http://www.lexinfo.net/ontology/2.0/lexinfo#'))

    g.parse('http://depot.nlpub.ru/rtlod/unldc.ttl', format='ttl')

    add_skos_predicate_variant(g, RDFS.label, SKOS.prefLabel)

    voc = skosify.skosify(g, mark_top_concepts=True,
                          eliminate_redundancy=True, break_cycles=True, keep_related=False,
                          cleanup_classes=True, cleanup_properties=True, cleanup_unreachable=True)
    voc.serialize(path + file_name + '.ttl', format='ttl')

    put_graph('http://unl.ru/', open(path + file_name + '.ttl').read())


def update_rusthes(config, download=False):
    """Download and transform Тезаурус РуТез."""

    path = config['data']['base'] + config['data']['vocabulary'] + 'rus/'
    if not os.path.exists(path):
        os.mkdir(path)

    file_name = 'ruthes'

    LEMON = Namespace('http://lemon-model.net/lemon#')

    logging.info('Download graph.')
    g = Graph()

    g.bind('lemon', LEMON)
    g.bind('lexinfo', Namespace('http://www.lexinfo.net/ontology/2.0/lexinfo#'))

    g.parse('http://depot.nlpub.ru/rtlod/ruthes-lite.ttl', format='ttl')

    add_skos_predicate_variant(g, RDFS.label, SKOS.prefLabel)

    voc = skosify.skosify(g, mark_top_concepts=True,
                          eliminate_redundancy=True, break_cycles=True, keep_related=False,
                          cleanup_classes=True, cleanup_properties=True, cleanup_unreachable=True)
    voc.serialize(path + file_name + '.ttl', format='ttl')

    put_graph('http://labinform.ru/pub/ruthes/', open(path + file_name + '.ttl').read())


def construct_aat_getty(config, download=False):
    """Download and transform the getty thesaurus AAT."""
    aat_full = 'http://vocab.getty.edu/dataset/aat/full.zip'
    path = config['data']['base'] + config['data']['vocabulary'] + 'aat/'
    if not os.path.exists(path):
        os.mkdir(path)

    file_name = 'aat_full.ttl'

    if download:
        logging.info('Downloading "The Art & Architecture Thesaurus".')
        response = requests.get(aat_full)
        if response.ok:
            logging.info('Download was successful.')
            buffer = io.BytesIO(response.content)
            z = zipfile.ZipFile(buffer)
            for n, i in zip(z.namelist(), z.infolist()):
                logging.info('Extracting archives...', n)
                tmp = z.read(i).decode('utf-8')
                with open(path + str(n), 'w') as file:
                    file.write(tmp)
                    logging.info('Extracted %s to %s', n, path)
        else:
            logging.critical('Was unable to download the file. Exit program.')
            import sys
            sys.exit(1)

    logging.info('Begin parsing of the ontology.')
    aat = Graph()
    aat.parse('http://vocab.getty.edu/ontology.rdf', format=guess_format('rdf'))
    logging.info('Parsed base ontology.')
    aat.parse(path + 'AATOut_Full.nt', format=guess_format('nt'))
    logging.info('Parsed Full AAT file.')
    aat.parse(path + 'AATOut_Sources.nt', format=guess_format('nt'))
    logging.info('Parsed sources file.')
    aat.parse(path + 'AATOut_Contribs.nt', format=guess_format('nt'))
    logging.info('Parsed contributors.')

    aat.serialize(path + file_name, format='nt')

    aat = skosify.skosify(path + file_name)
    aat.serialize(path + file_name, format='ttl')

    put_graph('http://vocab.getty.edu/aat/', open(path + file_name).read())


def update_skos(config, download=False):
    """Download, transform and upload the SKOS vocabulary."""
    uri = 'http://www.w3.org/2004/02/skos/core'
    path = config['data']['base'] + config['data']['vocabulary'] + 'skos/'
    if not os.path.exists(path):
        os.mkdir(path)
    file_name = 'skos-core.ttl'

    logging.info('Load SKOS vocabulary to %s.', path + file_name)
    g = Graph()
    g.parse(uri)
    add_type(g, OWL.Ontology, SKOS.ConceptScheme)
    add_type(g, OWL.Class, SKOS.Concept)
    add_type(g, RDF.Property, SKOS.Concept)

    add_skos_predicate_variant(g, RDFS.label, SKOS.prefLabel)
    add_skos_predicate_variant(g, DC.title, SKOS.prefLabel)
    add_skos_predicate_variant(g, DC.identifier, SKOS.notation)
    add_language_tags(g, 'en')

    add_skos_predicate_variant(g, RDFS.subClassOf, SKOS.broader)
    add_skos_predicate_variant(g, RDFS.subPropertyOf, SKOS.broader)

    voc = skosify.skosify(g)
    voc.serialize(path + file_name, format='ttl')
    logging.info('Upload skos to graph %s.', uri)
    put_graph(uri, open(path + file_name).read())


def update_npg_ontology(config, download=False):
    url = 'https://raw.githubusercontent.com/springernature/public-npg-domain-ontology/master/npg-relations-ontology.ttl'
    uri = 'http://ns.nature.com/relations/'

    path = config['data']['base'] + config['data']['temporary']
    file_name = 'npg_relation_onology.ttl'
    logging.info('Load NPG Relation Ontology to %s.', path + file_name)
    g = Graph()
    g.parse(url, format='ttl')
    add_type(g, OWL.ObjectProperty, SKOS.Concept)

    voc = skosify.skosify(g)
    voc.serialize(destination=path + file_name, format='ttl')
    logging.info('Upload NPG Relation Ontology to graph %s.', uri)
    put_graph(uri, open(path + file_name).read())


fast_urls_graph_names = [
    ('ftp://anonftp.oclc.org/pub/researchdata/fast/FASTTopical.nt.zip',
     'http://anonftp.oclc.org/pub/researchdata/fast/FASTTopical'),
    ('ftp://anonftp.oclc.org/pub/researchdata/fast/FASTPersonal.nt.zip',
     'http://anonftp.oclc.org/pub/researchdata/fast/FASTPersonal'),
    ('ftp://anonftp.oclc.org/pub/researchdata/fast/FASTCorporate.nt.zip',
     'http://anonftp.oclc.org/pub/researchdata/fast/FASTCorporate'),
    ('ftp://anonftp.oclc.org/pub/researchdata/fast/FASTFormGenre.nt.zip',
     'http://anonftp.oclc.org/pub/researchdata/fast/FASTFormGenre'),
    ('ftp://anonftp.oclc.org/pub/researchdata/fast/FASTEvent.nt.zip',
     'http://anonftp.oclc.org/pub/researchdata/fast/FASTEvent'),
    ('ftp://anonftp.oclc.org/pub/researchdata/fast/FASTTitle.nt.zip',
     'http://anonftp.oclc.org/pub/researchdata/fast/FASTTitle'),
    ('ftp://anonftp.oclc.org/pub/researchdata/fast/FASTGeographic.nt.zip',
     'http://anonftp.oclc.org/pub/researchdata/fast/FASTGeographic'),
    ('ftp://anonftp.oclc.org/pub/researchdata/fast/FASTChronological.nt.zip',
     'http://anonftp.oclc.org/pub/researchdata/fast/FASTChronological'),
]


def update_fast(config, download=False):
    logger = logging.getLogger(__name__)
    temp_path = config['data']['base'] + config['data']['temporary']

    for url, graph in fast_urls_graph_names:
        logger.info('Loading %s into %s.', url, graph)
        import urllib.parse
        import ftplib
        parts = urllib.parse.urlparse(url)
        file_name = parts.path.split('/')[-1]
        path = parts.path.replace(file_name, '')
        ftp = ftplib.FTP(parts.netloc)
        ftp.login()
        ftp.cwd(path)
        ftp.retrbinary('RETR ' + file_name, open(temp_path + file_name, 'wb').write)
        ftp.quit()
        with open(temp_path + file_name, 'rb') as file:
            buffer = io.BytesIO(file.read())

        z = zipfile.ZipFile(buffer)
        text = z.read(z.infolist()[0]).decode('utf-8')

        path = config['data']['base'] + config['data']['vocabulary'] + 'fast/'
        if not os.path.exists(path):
            os.makedirs(path)
        file_name = file_name.replace('.zip', '')
        with open(path + file_name, 'w', encoding='utf-8') as file:
            file.write(text)

        logger.info('Downloaded and saved file in %s%s.', path, file_name)

        SCHEMA = Namespace('http://schema.org/')
        PERIOD = Namespace('http://www.productontology.org/id/')

        g = Graph()

        g.bind('schema', SCHEMA)
        g.bind('skos', SKOS)
        g.bind('dct', DCTERMS)
        g.bind('owl', OWL)
        g.bind('period', PERIOD)

        logger.info('Parsing graph from %s.', path + file_name)
        g.parse(path + file_name, format='nt')

        # Concept Scheme Names.
        fast = URIRef('http://id.worldcat.org/fast/ontology/1.0/#fast')
        fast_event = URIRef('http://id.worldcat.org/fast/ontology/1.0/#facet-Event')
        fast_chronological = URIRef('http://id.worldcat.org/fast/ontology/1.0/#facet-Chronological')
        fast_form_genre = URIRef('http://id.worldcat.org/fast/ontology/1.0/#facet-FormGenre')
        fast_geographic = URIRef('http://id.worldcat.org/fast/ontology/1.0/#facet-Geographic')
        fast_title = URIRef('http://id.worldcat.org/fast/ontology/1.0/#facet-Title')
        fast_topical = URIRef('http://id.worldcat.org/fast/ontology/1.0/#facet-Topical')
        fast_corporate = URIRef('http://id.worldcat.org/fast/ontology/1.0/#facet-Corporate')
        fast_personal = URIRef('http://id.worldcat.org/fast/ontology/1.0/#facet-Personal')

        if (fast, RDF.type, SKOS.ConceptScheme) in g:
            g.add((fast, SKOS.prefLabel, Literal('Fast Concept Scheme (overall)')))
        if (fast_event, RDF.type, SKOS.ConceptScheme) in g:
            g.add((fast_event, SKOS.prefLabel, Literal('Fast Concept Scheme (event term)')))
        if (fast_chronological, RDF.type, SKOS.ConceptScheme) in g:
            g.add((fast_chronological, SKOS.prefLabel, Literal('Fast Concept Scheme (chronological term)')))
        if (fast_form_genre, RDF.type, SKOS.ConceptScheme) in g:
            g.add((fast_form_genre, SKOS.prefLabel, Literal('Fast Concept Scheme (form or genre term)')))
        if (fast_geographic, RDF.type, SKOS.ConceptScheme) in g:
            g.add((fast_geographic, SKOS.prefLabel, Literal('Fast Concept Scheme (greographic term)')))
        if (fast_title, RDF.type, SKOS.ConceptScheme) in g:
            g.add((fast_title, SKOS.prefLabel, Literal('Fast Concept Scheme (title term)')))
        if (fast_topical, RDF.type, SKOS.ConceptScheme) in g:
            g.add((fast_topical, SKOS.prefLabel, Literal('Fast Concept Scheme (topical term)')))
        if (fast_corporate, RDF.type, SKOS.ConceptScheme) in g:
            g.add((fast_corporate, SKOS.prefLabel, Literal('Fast Concept Scheme (corporate term)')))
        if (fast_personal, RDF.type, SKOS.ConceptScheme) in g:
            g.add((fast_personal, SKOS.prefLabel, Literal('Fast Concept Scheme (personal term)')))

        add_type(g, SCHEMA.Event, SKOS.Concept)
        add_type(g, SCHEMA.CreativeWork, SKOS.Concept)
        add_type(g, SCHEMA.Intangible, SKOS.Concept)
        add_type(g, PERIOD.Periodization, SKOS.Concept)
        add_type(g, SCHEMA.Person, SKOS.Concept)
        add_type(g, SCHEMA.Place, SKOS.Concept)
        add_type(g, SCHEMA.Organization, SKOS.Concept)
        add_skos_predicate_variant(g, RDFS.label, SKOS.prefLabel)

        add_language_tags(g, 'en')

        file_name = file_name.replace('.nt', '.ttl')
        voc = skosify.skosify(g)
        logger.info('Saving changed graph to %s.', path + file_name)
        voc.serialize(destination=path + file_name, format='ttl')

        logger.info('Refactored graph %s and uploading it now.', graph)
        put_graph(graph, open(path + file_name).read())
        logger.info('Uploaded graph to Fuseki.')


def update_getty_program_ontology(config, download=False):
    """Downloading, transforming and uploadinmg the Getty Program Ontology."""

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

    logging.info('Load base ontology for getty!')
    g.parse(ontology, format='xml')
    logging.info('Finished download and parsing of %s. Begin processing.', ontology)

    logging.info('Add skos:prefLabel for rdfs:label.')

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

    logging.info('Begin serialization.')
    g.serialize(path + file_name + '.ttl', format='ttl')
    logging.info('Serialized base ontology and saved in %s.', path + file_name + '.ttl')

    file_name_skosified = file_name + '-skosified'
    voc = skosify.skosify(path + file_name + '.ttl')
    voc.serialize(path + file_name_skosified + '.ttl', format='ttl')

    put_graph('http://vocab.getty.edu/ontology', open(path + file_name_skosified + '.ttl').read())