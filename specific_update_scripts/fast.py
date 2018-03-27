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


fast_urls = {
    'ftp://anonftp.oclc.org/pub/researchdata/fast/FASTEvent.nt.zip',
    'ftp://anonftp.oclc.org/pub/researchdata/fast/FASTTitle.nt.zip',
    'ftp://anonftp.oclc.org/pub/researchdata/fast/FASTTopical.nt.zip',
    'ftp://anonftp.oclc.org/pub/researchdata/fast/FASTPersonal.nt.zip',
    'ftp://anonftp.oclc.org/pub/researchdata/fast/FASTCorporate.nt.zip',
    'ftp://anonftp.oclc.org/pub/researchdata/fast/FASTChronological.nt.zip',
    'ftp://anonftp.oclc.org/pub/researchdata/fast/FASTGeographic.nt.zip',
    'ftp://anonftp.oclc.org/pub/researchdata/fast/FASTFormGenre.nt.zip'
}

fast_sparql_graphs = {
    'http://anonftp.oclc.org/pub/researchdata/fast/FASTEvent',
    'http://anonftp.oclc.org/pub/researchdata/fast/FASTTitle',
    'http://anonftp.oclc.org/pub/researchdata/fast/FASTTopical',
    'http://anonftp.oclc.org/pub/researchdata/fast/FASTPersonal',
    'http://anonftp.oclc.org/pub/researchdata/fast/FASTCorporate',
    'http://anonftp.oclc.org/pub/researchdata/fast/FASTChronological',
    'http://anonftp.oclc.org/pub/researchdata/fast/FASTGeographic',
    'http://anonftp.oclc.org/pub/researchdata/fast/FASTFormGenre'
}


def update(config):
    logger = logging.getLogger(__name__)
    temp_path = config['data']['base'] + config['data']['temporary']

    for url, graph in zip(fast_urls, fast_sparql_graphs):
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

            logger.info('Downloaded and saved file.')

        SCHEMA = Namespace('http://schema.org/')

        g = Graph()

        g.parse(path + file_name, format='n3')
        add_type(g, SCHEMA.Event, SKOS.Concept)
        add_skos_predicate_variant(g, RDFS.label, SKOS.prefLabel)

        file_name = file_name.replace('.n3', '.ttl')
        g.serialize(destination=path + file_name, format='ttl')

        logger.info('Refactored graph with prefLabels & Concepts.')
        put_graph(graph, open(path + file_name))
        logger.info('Uploaded graph to Fuseki.')
