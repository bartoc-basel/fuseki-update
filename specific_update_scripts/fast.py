from rdflib import Graph, Namespace, URIRef
import skosify
import os
import zipfile
import logging
from io import BytesIO
from utility.common import *
from utility.fuseki import put_graph
"""
This script downloads all of the FAST vocabularies and makes them Skosmos ready.
"""


fast_urls_graph_names = [
    ('ftp://anonftp.oclc.org/pub/researchdata/fast/FASTEvent.nt.zip', 'http://anonftp.oclc.org/pub/researchdata/fast/FASTEvent'),
    ('ftp://anonftp.oclc.org/pub/researchdata/fast/FASTTitle.nt.zip', 'http://anonftp.oclc.org/pub/researchdata/fast/FASTTitle'),
    ('ftp://anonftp.oclc.org/pub/researchdata/fast/FASTTopical.nt.zip','http://anonftp.oclc.org/pub/researchdata/fast/FASTTopical'),
    ('ftp://anonftp.oclc.org/pub/researchdata/fast/FASTPersonal.nt.zip', 'http://anonftp.oclc.org/pub/researchdata/fast/FASTPersonal'),
    ('ftp://anonftp.oclc.org/pub/researchdata/fast/FASTCorporate.nt.zip', 'http://anonftp.oclc.org/pub/researchdata/fast/FASTCorporate'),
    ('ftp://anonftp.oclc.org/pub/researchdata/fast/FASTChronological.nt.zip', 'http://anonftp.oclc.org/pub/researchdata/fast/FASTChronological'),
    ('ftp://anonftp.oclc.org/pub/researchdata/fast/FASTGeographic.nt.zip', 'http://anonftp.oclc.org/pub/researchdata/fast/FASTGeographic'),
    ('ftp://anonftp.oclc.org/pub/researchdata/fast/FASTFormGenre.nt.zip',  'http://anonftp.oclc.org/pub/researchdata/fast/FASTFormGenre')
]


def update(config):
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
            buffer = BytesIO(file.read())

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

        g = Graph()

        g.bind('schema', SCHEMA)
        g.bind('skos', SKOS)
        g.bind('dct', DCTERMS)
        g.bind('owl', OWL)

        logger.info('Parsing graph from %s.', path + file_name)
        g.parse(path + file_name, format='nt')

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
        add_skos_predicate_variant(g, RDFS.label, SKOS.prefLabel)

        file_name = file_name.replace('.nt', '.ttl')
        logger.info('Saving changed graph to %s.', path + file_name)
        voc = skosify.skosify(g)
        voc.serialize(destination=path + file_name, format='ttl')

        logger.info('Refactored graph with prefLabels & Concepts.')
        put_graph(graph, open(path + file_name).read())
        logger.info('Uploaded graph to Fuseki.')
