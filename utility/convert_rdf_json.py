from rdflib import Graph, URIRef, Namespace, Literal
from rdflib.namespace import FOAF, SKOS, DCTERMS

import requests
import json

links = ['http://onomy.org/published/73/skos',
            'http://onomy.org/published/74/skos',
            'https://onomy.org/published/83/skos',
            'http://onomy.org/published/78/skos',
            'http://onomy.org/published/81/skos',
            'https://onomy.org/published/84/skos',
            'http://onomy.org/published/75/skos',
            'http://onomy.org/published/79/skos',
            'http://onomy.org/published/72/skos'
]

if __name__ == '__main__':

    for i, link in enumerate(links):
        response = requests.get(link)
        content = json.loads(response.text)

        NOM = Namespace('http://onomy.org/onomy-ns#')

        g = Graph()

        g.bind('foaf', FOAF)
        g.bind('onomy', NOM)
        g.bind('dcterms', DCTERMS)
        g.bind('skos', SKOS)

        for subject in content:
            s = URIRef(subject)
            for predicate in content[subject]:
                p = URIRef(predicate)
                if isinstance(content[subject][predicate], list):
                    for obj in content[subject][predicate]:
                        if obj['type'] == 'uri':
                            o = URIRef(obj['value'])
                        elif obj['type'] == 'literal':
                            if 'lang' in obj:
                                o = Literal(obj['value'],
                                            lang=obj['lang'])
                            else:
                                o = Literal(obj['value'])
                        else:
                            o = Literal(obj['value'],
                                        datatype=obj['type'])
                        g.add((s, p, o))
                elif isinstance(content[subject][predicate], dict):
                    if content[subject][predicate]['type'] == 'uri':
                        o = URIRef(content[subject][predicate]['value'])
                    elif content[subject][predicate]['type'] == 'literal':
                        if 'lang' in content[subject][predicate]:
                            o = Literal(content[subject][predicate]['value'], lang=content[subject][predicate]['lang'])
                        else:
                            o = Literal(content[subject][predicate]['value'])
                    else:
                        o = Literal(content[subject][predicate]['value'], datatype=content[subject][predicate]['type'])

                    g.add((s, p, o))

        for s, p, o in g.triples((None, None, SKOS.ConceptScheme)):
            for _, _, title in g.triples((s, DCTERMS.title, None)):
                title = title.toPython()

        g.serialize('output/' + title + '.ttl', format='ttl')