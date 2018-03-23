from SPARQLWrapper import SPARQLWrapper, JSON
import requests
import pygsheets
import argparse
import logging
import json
import sys

logging.basicConfig(stream=sys.stdout, level=logging.INFO)








if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Various utility functions to interact with the fuseki triple store.')
    parser.add_argument('-d', dest='delete_request', action='store_true')
    parser.add_argument('-p', dest='put_request', action='store_true')
    parser.add_argument('-g', dest='get_request', action='store_true')
    parser.add_argument('-all', dest='graphs', action='store_true')
    parser.add_argument('-diff', dest='diff', action='store_true')
    parser.add_argument('-f', dest='file', action='store', default='output.ttl')
    parser.add_argument('uri', nargs='?', default='')

    args = parser.parse_args()

    if args.graphs:
        create_graph_list()

    if args.diff:
        create_diff()

    if args.get_request:
        get_graph(args.uri, args.file)

    if args.delete_request:
        delete_graph(args.uri)
    if args.put_request:
        put_graph(args.uri, None)



