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

        add_type(g, SCHEMA.Event, SKOS.Concept)
        add_skos_predicate_variant(g, RDFS.label, SKOS.prefLabel)

        file_name = file_name.replace('.nt', '.ttl')
        logger.info('Saving changed graph to %s.', path + file_name)
        voc = skosify.skosify(g)
        voc.serialize(destination=path + file_name, format='ttl')

        logger.info('Refactored graph with prefLabels & Concepts.')
        put_graph(graph, open(path + file_name).read())
        logger.info('Uploaded graph to Fuseki.')
