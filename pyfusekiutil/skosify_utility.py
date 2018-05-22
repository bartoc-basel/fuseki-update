import skosify
import requests

def skosfiy(url, config, name, file_name, default_language=None, namespace=None):
    response = requests.get(url)
    path = config['data']['temporary'] + file_name
    if response.ok:
        with open(path, 'w+') as file:
            file.write(response.text)
        voc = skosify.skosify(path,
                              label=name,
                              namespace=namespace,
                              default_language=default_language,
                              mark_top_concepts=True,
                              eliminate_redundancy=True,
                              break_cycles=True,
                              keep_related=False,
                              cleanup_classes=True,
                              cleanup_properties=True,
                              cleanup_unreachable=True
                              )
        voc.serialize(path.split('.')[0] + '.ttl', format='ttl')
