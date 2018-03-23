from SPARQLWrapper import SPARQLWrapper, JSON
import requests
import logging


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


def get_graph(uri, path):
    url = 'http://localhost:3030/skosmos/data?graph=' + uri
    response = requests.request('GET', url)
    if response.ok:
        with open(path, 'w') as file:
            file.write(response.text)
    else:
        logging.error(response.text)


def create_graph_list():
    sparql = SPARQLWrapper('http://localhost:3030/skosmos/query')
    sparql.setQuery("""SELECT ?g
                        WHERE {
                            GRAPH ?g { }
                        }""")

    sparql.setReturnFormat(JSON)
    logging.info('Send query.')
    response = sparql.query().convert()

    all_graph_uris = list()
    for graph in response['results']['bindings']:
        all_graph_uris.append(graph['g']['value'])
    logging.info('processed query.')
    with open('graph_entries/all_graphs.json', 'w') as file:
        file.write(json.dumps(all_graph_uris, ensure_ascii=False, indent='    '))
    return all_graph_uris


def create_graph_names_list_from_sheet():
    c = pygsheets.authorize()
    ss = c.open('update_fuseki')
    wks = ss.sheet1
    graph_names = list(filter(lambda x: x != '', wks.get_col(5)[1:]))
    logging.info('Read sheet.')
    with open('graph_entries/sheet_graphs.json', 'w') as file:
        file.write(json.dumps(list(graph_names), ensure_ascii=False, indent='    '))
    return graph_names


def create_diff():
    fuseki = create_graph_list()
    sheet = create_graph_names_list_from_sheet()

    sheet_set = set(sheet)
    if len(sheet_set) < len(sheet):
        logging.warning('There are duplicate graph names in sheet. Unique Graphs: %s Total Graphs: %s', len(sheet_set), len(sheet))
        # TODO: Implement something that will name the duplicates.

    fuseki_set = set(fuseki)

    if len(fuseki) != len(sheet_set):
        logging.warning('Fuseki does not have the same amount of graphs stored as are defined in the sheet.!')

        not_in_sheet = fuseki_set - sheet_set
        not_in_store = sheet_set - fuseki_set

        with open('graph_entries/not_in_store.json', 'w') as file:
            file.write(json.dumps(list(not_in_store), ensure_ascii=False, indent='    '))
        with open('graph_entries/not_in_sheet.json', 'w') as file:
            file.write(json.dumps(list(not_in_sheet), ensure_ascii=False, indent='    '))
    else:
        logging.info('There is no difference between the sheet graphs and the graphs in fuseki.')