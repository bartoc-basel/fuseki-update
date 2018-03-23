from rdflib import Graph
import requests
import logging
import sys
import io
import zipfile
"""


"""

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

aat_full = 'http://vocab.getty.edu/dataset/aat/full.zip'

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






