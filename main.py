from configparser import ConfigParser, ExtendedInterpolation
from utility.fuseki import *
import utility.skosify_file
import specific_update_scripts.getty_ontology
import specific_update_scripts.skos
import update
import argparse
import logging

parser = argparse.ArgumentParser(description='A command line tool to update & manage the fuseki triple store.')
parser.add_argument('config', action='store', type=str, default='default.cfg',
                    help='Necessary configuration values for this module to run.')
parser.add_argument('--config', action='store', type=str, dest='voc_config', default=None,
                    help='The config file used for this vocabulary in skosify. NYI')
parser.add_argument('-all', action='store_true', dest='run_update')
parser.add_argument('-u', action='store', dest='name', default=None)

parser.add_argument('-d', dest='delete_request', action='store_true')
parser.add_argument('-p', dest='put_request', action='store_true')
parser.add_argument('-g', dest='get_request', action='store_true')
parser.add_argument('-diff', dest='diff', action='store_true')
parser.add_argument('-f', dest='file', action='store', default='output.ttl')
parser.add_argument('--uri', nargs='?', default='')
parser.add_argument('--url', nargs='?', default='')
parser.add_argument('-t', dest='test_skosify', action='store_true')
parser.add_argument('-l', dest='label', action='store')
parser.add_argument('--namespace', action='store', default=None)

args = parser.parse_args()

config = ConfigParser(interpolation=None)
config.read(args.config)

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

if args.run_update:
    update.run(config)


if args.diff:
    credentials = config['data']['credentials']
    c = pygsheets.authorize(outh_file=credentials + 'client_secrets.json',
                            outh_creds_store=credentials,
                            outh_nonlocal=True)
    ss = c.open('update_fuseki')
    wks = ss.sheet1
    create_diff(config['data']['base'], wks)

if args.name is not None:
    if args.name == 'getty-ontology':
        specific_update_scripts.getty_ontology.update(config)
    if args.name == 'skos':
        specific_update_scripts.skos.update(config)

if args.test_skosify:
    utility.skosify_file.run(args.url, config, args.label, args.file, namespace=args.namespace)














