import pygsheets

from configparser import ConfigParser
import argparse

from pyfusekiutil.core_fuseki_update import update_fuseki
from pyfusekiutil.fuseki_utility import get_graph
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
    parser.add_argument('-all', action='store_true', dest='run_update',
                        help='Run the main update script to update the tripple store from the google spreadsheet.')
    parser.add_argument('-s', action='store', dest='name', default=None,
                        help='The name of a specific thesaurus to be loaded/updated. Accepts one of the following '
                             'values: {}.'.format(specific_functions.keys()))

    parser.add_argument('-delete', dest='delete_request', action='store_true')
    parser.add_argument('-put', dest='put_request', action='store_true')
    parser.add_argument('-get', dest='get_request', action='store_true')
    parser.add_argument('-diff', dest='diff', action='store_true')
    parser.add_argument('-f', dest='file', action='store', default='output.ttl')
    parser.add_argument('--uri', nargs='?', default='')
    parser.add_argument('--url', nargs='?', default='')
    parser.add_argument('-t', dest='skosify', action='store_true', help='skosfiy(args.url, config, args.label, '
                                                                        'args.file, namespace=args.namespace, '
                                                                        'default_language=args.default_language)')
    parser.add_argument('-l', dest='label', action='store')
    parser.add_argument('-k', dest='download', action='store_true', default=False,
                        help='Download the file and do not just load it from disc.')
    parser.add_argument('--namespace', action='store', default=None)
    parser.add_argument('--default-language', action='store', default=None)

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
            update_fuseki(config)

        if args.get_request:
            get_graph(args.uri, data_path + config['data']['vocabulary'] + args.file)

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












