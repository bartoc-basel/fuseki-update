import pygsheets

from configparser import ConfigParser
import argparse

from pyfusekiutil.core_fuseki_update import update_fuseki
from pyfusekiutil.fuseki_utility import get_graph, delete_graph
from pyfusekiutil.fuseki_utility import create_diff
from pyfusekiutil.skosify_utility import skosfiy
from pyfusekiutil.updates import *


def main():
    specific_functions = {
        'getty-ontology': update_getty_program_ontology,
        'skos': update_skos,
        'fast': update_fast,
        'npg-ontology': update_npg_ontology,
        'aat': construct_aat_getty,
        'rusthes': update_rusthes,
        'unldc': update_unldc,
        'yarn': update_yarn
    }

    parser = argparse.ArgumentParser(description='A command line tool to update & manage the fuseki triple store.')
    parser.add_argument('config', action='store', type=str, default='default.cfg',
                        help='Necessary configuration values for this module to run.')
    parser.add_argument('--config', action='store', type=str, dest='voc_config', default=None,
                        help='The config file used for this vocabulary in skosify. NYI')
    parser.add_argument('-a', action='store_true', dest='run_update',
                        help='Run the main update script to update the triple store from the google spreadsheet.')
    parser.add_argument('-n', action='store', type=int, dest='number_of_lines', default=-1,
                        help='Number of lines the update should run through in the google sheets.')
    parser.add_argument('-s', action='store', dest='name', default=None,
                        help='The name of a specific thesaurus to be loaded/updated. Accepts one of the following '
                             'values: {}.'.format(specific_functions.keys()))
    parser.add_argument('-f', dest='file', action='store', default='output.ttl', help='Define a file path or file name.'
                                                                                      'Used for skosify, put requests '
                                                                                      'and get requests. The default'
                                                                                      ' is "output.ttl"')
    parser.add_argument('-delete', dest='delete_request', action='store_true',
                        help='Delete a specific graph from the Fuseki store. Requires a --uri to be specified.')
    parser.add_argument('-put', dest='put_request', action='store_true',
                        help='Create or replace a specific graph on the Fuseki store. '
                             'Requires a [--uri URI] to be specified and the [-f FILE_PATH] full path to the file '
                             'containing the RDF data (in turtle (.ttl) format).')
    parser.add_argument('-get', dest='get_request', action='store_true',
                        help='Get a specific graph from the Fuseki store and store it in a local file '
                             '(in turtle (.ttl) format).')
    parser.add_argument('--uri', nargs='?', default='', help='Define a graph URI for Fuseki operations.')
    parser.add_argument('-diff', dest='diff', action='store_true',
                        help='Generate json-files which show the differences between the Fuseki triple store and the '
                             'Google Spreadsheet. In terms of what graphs are or should be defined.')
    parser.add_argument('-t', dest='skosify', action='store_true',
                        help='Can be used to skosify a vocabulary the same way the main update loop does. This should '
                             ' help with debugging when Skosify creates a result which Skosmos cannot understand. '
                             'skosfiy(args.url, config, args.label, args.file, namespace=args.namespace, '
                             'default_language=args.default_language)')
    parser.add_argument('--url', nargs='?', default='', help='Add a url. Used to skosify a vocabulary.')
    parser.add_argument('-l', dest='label', action='store', help='Add a label for skosify.')
    parser.add_argument('--namespace', action='store', default=None, help='The namespace for skosify.')
    parser.add_argument('--default-language', action='store', default=None, help='The default language for skosify.')
    parser.add_argument('-d', dest='debug', action='store_true', help='Ignore default logging configuration and simply '
                                                                      'log to stdout.')

    args = parser.parse_args()

    config = ConfigParser(interpolation=None)
    config.read(args.config)

    if args.debug:
        import sys
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    else:
        # options for what should be logged.
        logging_options = dict()
        for key, val in config.items('logger'):
            logging_options[key] = val

        logging_options['filename'] = config['data']['base'] + config['data']['output'] + logging_options['filename']

        debug_levels = {
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'warning': logging.WARNING,
            'error': logging.ERROR,
            'critical': logging.CRITICAL
        }

        # tanslate logging level.
        if 'level' in logging_options:
            logging_options['level'] = debug_levels[logging_options['level']]
        else:
            logging_options['level'] = logging.CRITICAL

        logging.basicConfig(**logging_options)

    data_path = config['data']['base']
    logging.debug('Base path: ' + data_path)
    try:
        if args.run_update:
            update_fuseki(config, args.number_of_lines)

        if args.get_request:
            get_graph(args.uri, data_path + config['data']['vocabulary'] + args.file)

        if args.put_request:
            put_graph(args.uri, args.file)

        if args.delete_request:
            delete_graph(args.uri)

        if args.diff:
            credentials = config['data']['base'] + config['data']['credentials']
            c = pygsheets.authorize(outh_file=credentials + 'client_secrets.json',
                                    outh_creds_store=credentials,
                                    outh_nonlocal=True)
            ss = c.open('update_fuseki')
            wks = ss.sheet1
            create_diff(config['data']['base'], wks)

        if args.name is not None:
            if args.name in specific_functions.keys():
                specific_functions[args.name](config, download=args.download)

        if args.skosify:
            skosfiy(args.url, config, args.label, args.file, namespace=args.namespace,
                    default_language=args.default_language)
    except Exception:
        logging.exception('An error occured:')












