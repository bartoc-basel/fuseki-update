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

aat_full = 'http://vocab.getty.edu/dataset/aat/full.zip'

g = Graph()
g.parse(ontology, format='xml')

g.serialize('vocabularies/getty/base_ontology.ttl', format='ttl')


response = requests.get(aat_full)

if response.ok:
    files = list()
    buffer = io.BytesIO(response.content)
    z = zipfile.ZipFile(buffer)
    for n, i in zip(z.namelist(), z.infolist()):
        tmp = z.read(i).decode('utf-8')
        with open('vocabularies/getty/' + str(n), 'w') as file:
            file.write(tmp)






