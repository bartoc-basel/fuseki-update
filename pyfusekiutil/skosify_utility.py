import skosify
import requests


def skosfiy(url, config, name, file_name, default_language=None, namespace=None):
    response = requests.get(url)
    if response.ok:
        with open(config['data']['temporary'] + file_name, 'w') as file:
            file.write(response.text)
        voc = skosify.skosify(config['data']['temporary'] + file_name,
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
        voc.serialize(config['data']['vocabulary'] + file_name + '.ttl', format='ttl')
