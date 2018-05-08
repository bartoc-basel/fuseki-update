import skosify
from rdflib import Graph, Namespace, RDF
from rdflib.namespace import SKOS

if __name__ == '__main__':
    p = Graph()
    p.parse('http://bartoc.org/sites/default/files/skos_files/UTU.rdf', format='json-ld')

    concept_scheme = list(p.subjects(RDF.type, SKOS.ConceptScheme))[0]
    print(list(p.objects(concept_scheme, None)))

    p.serialize('test2.ttl', format='ttl')

    voc = skosify.skosify(source='test2.ttl',
                          infer=True,
                          # namespace='http://msc2010.org/resources/MSC/2010/',
                          # label='Mathematics Subject Classification 2010',
                          )
    voc.serialize('test.ttl', format='ttl')



