import requests
from rdflib import Graph, URIRef
from rdflib.namespace import RDF, SKOS
from rdflib.util import guess_format
import skosify
import os.path
import gzip
import json
import logging
import sys
from io import BytesIO
import zipfile

from configparser import ConfigParser

from sheet import GoogleSheet

# The MIME Types for the possible rdf file formats. Needed to upload a file on apache jena.
TURTLE_MIME_TYPE = 'application/x-turtle'
N3_MIME_TYPE = 'text/n3; charset=utf-8'
NT_MIME_TYPE = 'application/n-triples'
RDF_MIME_TYPE = 'application/rdf-xml'

# Column value of sheet
TITLE = 0
URL = 1
FILE_TYPE = 2
SHORT_NAME = 3
DEFINED_NAMESPACE = 4
READY = 5
GENERATED_NAMESPACE = 6
TRIPLE_COUNT = 7
ERROR_TYPE = 8
ERROR = 9
SKOSMOS_ENTRY = 10

class InvalidMIMETypeError(Exception): pass
class DownloadError(Exception): pass
class FusekiUploadError(Exception): pass
class SkosifyError(Exception): pass
class NoNamespaceDetectedError(Exception): pass


class SheetUpdate(object):

    def __init__(self):
        self.namespace = ''
        self.triple_count = ''
        self.error_type = ''
        self.error_message = ''
        self.skosmos_entry = ''


class SkosifiedGraph(object):

    def __init__(self, file_name: str, format: str, name: str, namespace: str, temp_path: str, default_language=None,
                 logger=logging.getLogger('bartoc-skosify')):
        self.logger = logger
        self.namespace = namespace
        self.file_name = file_name
        self.temp_path = temp_path
        self.format = format
        self.name = name
        self.default_language = default_language

        self.rdf = Graph()

    def process(self):
        self.rdf.parse(self.file_name, format=guess_format(self.format))
        if self.namespace == '':
            self.detect_namespace()
        try:
            self.rdf = skosify.skosify(self.rdf, label=self.name, namespace=self.namespace,
                                       default_language=self.default_language, mark_top_concepts=True,
                                       eliminate_redundancy=True, break_cycles=True, keep_related=False,
                                       cleanup_classes=True, cleanup_properties=True, cleanup_unreachable=True)
        except SystemExit:
            raise SkosifyError()
        finally:
            # TODO: does this always run?
            self.rdf.serialize(destination=self.temp_path + 'upload.ttl', format='ttl', encoding='utf-8')

    def detect_namespace(self):
        concept = self.rdf.value(None, RDF.type, SKOS.Concept, any=True)
        if concept is None:
            self.logger.critical('Namespace auto-detection failed. Define namespace in sheet.')
            raise NoNamespaceDetectedError()

        local_name = concept.split('/')[-1].split('#')[-1]
        namespace = URIRef(concept.replace(local_name, ''))
        if namespace.strip() == '':
            self.logger.critical('Namespace auto-detection failed. Define namespace in sheet.')
            raise NoNamespaceDetectedError()

        self.logger.info('Namespace detection successful: %s.', namespace)
        self.namespace = namespace


class FusekiUpdate(object):

    def __init__(self, title: str, url: str, file_type: str, short_name: str, defined_namespace: str, temp_path: str,
                 update: SheetUpdate):
        self.title = title.strip()
        self.url = url.strip()
        self.short_name = short_name.strip()
        self.file_end = file_type.strip().lower()
        self.namespace = defined_namespace.strip()
        self.temp_path = temp_path

        self.sheet_updates = update
        if self.namespace == '':
            self.sheet_updates.namespace = self.namespace

        self.graph = None
        self.mime_type = ''

    def process(self):
        self.mime_type = self.check_mime_type(self.file_end)
        file_name = self.download_file(self.url)
        self.graph = SkosifiedGraph(file_name, self.file_end, self.title, self.namespace, self.temp_path)
        try:
            self.graph.process()
            self.sheet_updates.namespace = str(self.graph.namespace)
        except NoNamespaceDetectedError:
            self.sheet_updates.error_type = 'NO NAMESPACE DETECTED'
            self.sheet_updates.error_message = 'Es konnte kein Namespace gefunden werden. Bitte im Feld ' \
                                               '"Definierter Namespace" angeben.'
        except SkosifyError:
            self.sheet_updates.error_type = 'SKOSIFY ERROR'
            self.sheet_updates.error_message = 'Skosify konnte nicht mit diesem Vokabular umgehen. ' \
                                               'Siehe Fehlermeldungen auf dem Server.'

        self.upload_file()
        self.sheet_updates.skosmos_entry = self.create_skosmos_entry()

        # clean up skosify temporary file.
        try:
            os.remove(file_name)
        except FileNotFoundError:
            pass

    def check_mime_type(self, file_type):
        # Set mime type and check if it is a valid value. Otherwise continue.
        # This does not check if it was set correctly in the sheet.
        if file_type == 'rdf':
            return RDF_MIME_TYPE
        elif file_type == 'ttl':
            return TURTLE_MIME_TYPE
        elif file_type == 'n3':
            return N3_MIME_TYPE
        elif file_type == 'nt':
            return NT_MIME_TYPE
        else:
            self.sheet_updates.error_type = "FILE TYPE ERROR"
            self.sheet_updates.error_message = "Invalid MIME Type: expected RDF, TTL, N3 or NT."
            logging.exception('Wrong MIME Type in file.')
            raise InvalidMIMETypeError

    def download_file(self, url: str) -> str:
        download_file_response = requests.get(url)
        if download_file_response.status_code != 200:
            self.sheet_updates.error_type = 'DOWNLOAD ERROR (' + str(download_file_response.status_code) + ')'
            self.sheet_updates.error_message = download_file_response.text
            logging.exception('DownloadError encountered:')
            raise DownloadError('Was unable to download the file from ' + url)

        # save downloaded file locally to ensure that it is unzipped
        #  and does not need to be downloaded again for getting an URI
        file_name = self.temp_path + 'temporary.' + self.file_end.lower()
        buffer = BytesIO(download_file_response.content)
        if url.endswith('.zip'):
            z = zipfile.ZipFile(buffer)
            text = z.read(z.infolist()[0]).decode('utf-8')
        elif url.endswith('.gz'):
            text = gzip.decompress(download_file_response.content).decode('utf-8')
        else:
            text = download_file_response.content.decode('utf-8')

        with open(file_name, 'w', encoding='utf-8') as file:
            file.write(text)
        return file_name

    def upload_file(self):
        with open(self.temp_path + 'upload.ttl', 'r', encoding='utf-8') as file:
            data = {'name': ('upload.ttl', file.read(), self.mime_type)}
            basic_url = 'http://localhost:3030/skosmos/data?graph=' + self.graph.namespace

            # delete the graph if it exists. Otherwise updates to values would get added as additional triples.
            # the deletion is silent if some data has duplicate triples then this probably failed.
            requests.request('DELETE', basic_url)

            # upload graph to server.
            response = requests.request('POST', basic_url, files=data)

            if response.status_code < 200 or response.status_code >= 300:
                self.sheet_updates.error_type = 'UPLOAD ERROR ' + str(response.status_code)
                self.sheet_updates.error_message = 'Could not upload item to fuseki: ' + str(response.text)
                raise FusekiUploadError()

            self.sheet_updates.triple_count = str(json.loads(response.text)['tripleCount'])

    def create_skosmos_entry(self):
        short_name = self.short_name.lower().replace(' ', '_')
        result = ':' + short_name + ' a skosmos:Vocabulary, void:Dataset ;\n'
        result += '\tdc:title "' + self.title + '"@en ;\n'
        result += '\tskosmos:shortName "' + self.short_name + '" ;\n'
        result += '\tdc:subject :cat_general ;\n'
        result += '\tvoid:uriSpace "' + str(self.sheet_updates.namespace) + '" ;\n'
        result += '\tskosmos:language "en" ;\n'
        result += '\tskosmos:defaultLanguage "en" ;\n'
        result += '\tskosmos:showTopConcepts true ;\n'
        result += '\tvoid:sparqlEndpoint <http://localhost:6081/skosmos/sparql> ;\n'
        # LAST LINE NEEDS TO END WITH A DOT IF EXPANDED!!
        result += '\tskosmos:sparqlGraph <' + str(self.sheet_updates.namespace) + '> .\n'
        return result


config = ConfigParser(interpolation=None)
config.read(sys.argv[1])

authorization_options = dict()
for key, val in config.items('authorization'):
    authorization_options[key] = val

sheet_options = dict()
for key, val in config.items('sheet'):
    sheet_options[key] = val

log_options = dict()
for key, val in config.items('logger'):
    log_options[key] = val

if 'level' in log_options:
    if log_options['level'] == 'debug':
        log_options['level'] = logging.DEBUG
    if log_options['level'] == 'info':
        log_options['level'] = logging.INFO
    if log_options['level'] == 'warning':
        log_options['level'] = logging.WARNING
    if log_options['level'] == 'error':
        log_options['level'] = logging.ERROR
    if log_options['level'] == 'critical':
        log_options['level'] = logging.CRITICAL

logging.basicConfig(**log_options)

sheet = GoogleSheet(**authorization_options)
sheet.load_sheet(sheet_options['range'])

count = 1
for val in sheet.values:
    update = SheetUpdate()
    if len(val) == int(sheet_options['sheet_length']):
        try:
            if val[READY] == 'y':
                FusekiUpdate(val[TITLE], val[URL], val[FILE_TYPE], val[SHORT_NAME], val[DEFINED_NAMESPACE],
                             sheet_options['temp'], update).process()
        except Exception as error:
            update.error_type = 'UNKNOWN ERROR (' + str(type(error)) + ')'
            update.error_message = str(error)
            logging.exception('Got an unknown exception: ')
            raise
        finally:
            count += 1

    else:
        update.error_type = 'Missing Input'
        update.error_message = 'Der Input ist zu kurz. Ev. ist die End-of-Line Markierung nicht vorhanden. ' \
                               'Länge des Inputs: ' + str(len(val))

    sheet.values[count][GENERATED_NAMESPACE] = update.namespace
    sheet.values[count][TRIPLE_COUNT] = update.triple_count
    sheet.values[count][ERROR_TYPE] = update.error_type
    sheet.values[count][ERROR] = update.error_message
    sheet.values[count][SKOSMOS_ENTRY] = update.skosmos_entry
    try:
        os.remove(sheet_options['temp'] + 'temporary.ttl')
    except FileNotFoundError:
        pass

sheet.store_sheet(sheet_options['range'])
