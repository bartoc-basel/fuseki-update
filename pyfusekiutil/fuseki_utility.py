from SPARQLWrapper import SPARQLWrapper, JSON
import requests

import logging
import json
import os


class FusekiError(Exception):
    """Fuseki has returned an error message!"""


def delete_graph(uri):
    url = 'http://localhost:3030/skosmos/data?graph=' + uri
    response = requests.request('DELETE', url)
    if response.ok:
        logging.info(response.text)
    else:
        logging.error(response.text)


def put_graph(uri, data):
    url = 'http://localhost:3030/skosmos/data?graph=' + uri
    data = {'name': ('upload.ttl', data, 'application/x-turtle')}
    response = requests.request('PUT', url, files=data)
    if response.ok:
        logging.info(response.text)
    else:
        logging.error(response.text)
        raise FusekiError('Could not upload file.')


def get_graph(uri, path):
    url = 'http://localhost:3030/skosmos/data?graph=' + uri
    response = requests.request('GET', url)
    if response.ok:
        with open(path, 'w') as file:
            file.write(response.text)
    else:
        logging.error(response.text)


def fuseki_graph_list(path):
    sparql = SPARQLWrapper('http://localhost:3030/skosmos/query')
    sparql.setQuery("""SELECT ?g
                        WHERE {
                            GRAPH ?g { }
                        }""")

    sparql.setReturnFormat(JSON)
    logging.info('Query Fuseki endpoint for all graphs found in the skosmos dataset.')
    response = sparql.query().convert()

    all_graph_uris = list()
    for graph in response['results']['bindings']:
        all_graph_uris.append(graph['g']['value'])

    file_name = 'fuseki_graph_list.json'
    with open(path + file_name, 'w') as file:
        file.write(json.dumps(all_graph_uris, ensure_ascii=False, indent='    '))
    logging.info('Fetched all graph uris and written them to {}{}.'.format(path, file_name))
    return all_graph_uris


def sheet_graph_names_list(path, wks):
    graph_names = list(filter(lambda x: x != '', wks.get_col(5)[1:]))
    with open(path + 'sheet_graphs.json', 'w') as file:
        file.write(json.dumps(list(graph_names), ensure_ascii=False, indent='    '))
    logging.info('Stored all graph names defined in the spreadsheet in {}{}.'.format(path, 'sheet_graphs.json'))
    return graph_names


def create_diff(path, wks):
    path = path + '/graphs/'
    if not os.path.exists(path):
        os.mkdir(path)

    fuseki = fuseki_graph_list(path)
    sheet = sheet_graph_names_list(path, wks)

    sheet_set = set(sheet)
    if len(sheet_set) < len(sheet):
        logging.warning('There are duplicate graph names in sheet. Unique Graphs: %s Total Graphs: %s', len(sheet_set),
                        len(sheet))

    fuseki_set = set(fuseki)

    if len(fuseki) != len(sheet_set):
        logging.warning('Fuseki does not have the same amount of graphs stored as are defined in the sheet!')

        not_in_sheet = fuseki_set - sheet_set
        not_in_store = sheet_set - fuseki_set

        with open(path + 'not_in_store.json', 'w') as file:
            file.write(json.dumps(list(not_in_store), ensure_ascii=False, indent='    '))
        with open(path + 'not_in_sheet.json', 'w') as file:
            file.write(json.dumps(list(not_in_sheet), ensure_ascii=False, indent='    '))
    else:
        logging.info('There is no difference between the sheet graphs and the graphs in fuseki.')