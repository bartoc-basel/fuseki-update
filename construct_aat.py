from rdflib import Graph
import argparse
import requests
import logging
import sys
import io
import zipfile
"""


"""

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

ontology = 'http://vocab.getty.edu/ontology.rdf'
ontology_path = 'vocabularies/getty/base_ontology.ttl'
aat_full = 'http://vocab.getty.edu/dataset/aat/full.zip'

g = Graph()

logging.info('Load base ontology for getty!')
g.parse(ontology, format='xml')
logging.info('Finished download and parsing of %s. Begin serialization.', ontology)
g.serialize(ontology_path, format='ttl')
logging.info('Serialized base ontology and saved in %s.', ontology_path)

logging.info('Download full aat zip!')
response = requests.get(aat_full)
if response.ok:
    logging.info('Successfully downloaded aat!')
    files = list()
    buffer = io.BytesIO(response.content)
    z = zipfile.ZipFile(buffer)
    for n, i in zip(z.namelist(), z.infolist()):
        logging.info('Uncompressed %s.', n)
        tmp = z.read(i).decode('utf-8')
        with open('vocabularies/getty/' + str(n), 'w') as file:
            file.write(tmp)
            logging.info('Written %s to vocabularies/getty/.', n)


logging.info('Finished Application')

aat = Graph()
aat.parse('vocabularies/getty/base_ontology.ttl')
aat.parse('vocabularies/getty/AATOut_Full.nt')
aat.parse('vocabularies/getty/AATOut_Sources.nt')
aat.parse('vocabularies/getty/AATOut_Contribs.nt')

aat.serialize('vocabularies/getty/aat_full.ttl', format='ttl')






