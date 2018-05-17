import requests
from rdflib import Graph, URIRef
from rdflib.namespace import RDF, SKOS
from rdflib.util import guess_format
from rdflib.exceptions import ParserError
from rdflib.plugins.parsers.notation3 import BadSyntax
import skosify
import os
import gzip
import json
import logging
from io import BytesIO
import zipfile

import time
import pygsheets
import googleapiclient.errors

# The MIME Types for the possible rdf file formats. Needed to upload a file on apache jena.
TURTLE_MIME_TYPE = 'application/x-turtle'
N3_MIME_TYPE = 'text/n3; charset=utf-8'
NT_MIME_TYPE = 'application/n-triples'
RDF_MIME_TYPE = 'application/rdf-xml'
JSON_LD_MIME_TYPE = 'application/json'

# Column value of sheet
TITLE = 0
URL = 1
FILE_TYPE = 2
SHORT_NAME = 3
SPARQL_GRAPH_NAME = 4
DEFAULT_LANGUAGE = 5
READY = 6
NAMESPACE = 7
TRIPLE_COUNT = 8
ERROR_TYPE = 9
ERROR = 10
SKOSMOS_ENTRY = 11

class InvalidMIMETypeError(Exception): pass
class DownloadError(Exception): pass
class FusekiUploadError(Exception): pass
class NoNamespaceDetectedError(Exception): pass


class SheetUpdate(object):
    """Holds the changes made across the classes."""

    def __init__(self):
        self.namespace = ''
        self.triple_count = ''
        self.error_type = ''
        self.error_message = ''
        self.skosmos_entry = ''


class SkosifiedGraph(object):
    """
    Loads the graph and makes adjustements to it. These adjustments should help Skosmos to display the vocabularies.
    """

    def __init__(self, file_name: str, format: str, name: str, namespace: str, temp_path: str, default_language,
                 update: SheetUpdate, logger=logging.getLogger('bartoc-skosify')):
        """

        :param file_name:           Name of the file where the vocabulary was saved after download.
        :param format:              What format the vocabulary is stored in (rdf+xml, turtle, n-triples, n3
        :param name:                The title/name of the vocabulary. Comes from the sheet and not the vocabulary.
        :param namespace:           If the namespace inside of the sheet is defined this is it. Otherwise None.
        :param temp_path:           Path to the storage for temporary files. Configured in default.cfg
        :param default_language:    (NIY) When defined skosify will add this language to all labels within the vocabulary.
        :param update:              The current sheet update object.
        :param logger:              The logger used.
        """
        self.logger = logger
        self.namespace = namespace
        self.file_name = file_name
        self.temp_path = temp_path
        self.format = format
        self.name = name
        self.default_language = default_language
        self.update = update

        self.rdf = Graph()

    def process(self):
        """
        This processes the vocabulary with Skosify.

        Will first parse it and attempt to detect the namespace if not defined.
        Then will load it with skosfiy with various options enabled.

        :raises Various errors when the file can't be parsed or serialized.
        """
        try:
            self.rdf.parse(self.file_name, format='json-ld' if self.format == 'json' else guess_format(self.format))
        except (ParserError, BadSyntax) as error:
            self.update.error_type = 'PARSER ERROR'
            self.update.error_message = str(error)
            self.logger.exception('Could not parse vocabulary %s:', self.name)
            return
            # if parser was not successful there is no point in continuing.

        # if no namespace has been defined try to find one.
        if self.namespace == '':
            self.detect_namespace()
        try:
            self.rdf.serialize(destination='test.ttl', format='ttl')
            # Does some magic to the vocabulary.
            # Documentation is somewhat sparse but can be found here: https://github.com/NatLibFi/Skosify
            self.rdf = skosify.skosify(self.rdf, label=self.name, namespace=self.namespace,
                                       default_language=self.default_language, mark_top_concepts=True,
                                       eliminate_redundancy=True, break_cycles=True, keep_related=False,
                                       cleanup_classes=True, cleanup_properties=True, cleanup_unreachable=True)
        except SystemExit:
            # Whenever skosify encounters a fatal/critical error it calls sys.exit(1). This is caught here.
            self.logger.critical('Was unable to skosify %s', self.name)
            self.update.error_type = 'Skosify Critical Error'
            self.update.error_message = 'Skosify was unable to deal with this vocabulary. ' \
                                        'Check out the log why this is.'
            pass
        finally:
            # Writes the graph to disk. independent of whether skosify was successful or not.
            self.rdf.serialize(destination=self.temp_path + 'upload.ttl', format='ttl', encoding='utf-8')
            self.file_name = 'upload.ttl'
            self.format = 'ttl'

    def detect_namespace(self):
        """
        Attempts to extract a base namespace from the vocabulary graph.

        Will first find a random concept or concept scheme and then extract the base name space from it.

        :raises NoNamespaceDetectedError: If no namespace can be found.
        """
        concept = self.rdf.value(None, RDF.type, SKOS.Concept, any=True)
        if concept is None:
            concept = self.rdf.value(None, RDF.type, SKOS.ConceptScheme, any=True)
            if concept is None:
                raise NoNamespaceDetectedError('Could not detect a namespace for ' + self.name +
                                               ', because there are no SKOS Concepts or SKOS Concept Schemes defined.')

        local_name = concept.split('/')[-1].split('#')[-1]
        namespace = URIRef(concept.replace(local_name, '').strip('#'))
        if namespace.strip() == '':
            raise NoNamespaceDetectedError('Could not detect a namespace for ' + self.name +
                                           ', because the URI is not valid.')

        self.logger.info('Namespace detection successful: %s.', namespace)
        self.namespace = namespace


class FusekiUpdate(object):
    """This class handles the download and upload of each vocabulary."""

    def __init__(self, title: str, url: str, file_type: str, short_name: str,
                 sparql_graph: str, namespace: str, default_language: str, temp_path: str,
                 update: SheetUpdate, logger=logging.getLogger('fuseki-update')):
        """
        :param title:               Name/Title of the vocabulary. Input from sheet.
        :param url:                 Url to where the vocabulary can be downloaded. Input from sheet.
        :param file_type:           MIME Type of the downloaded file. Input from sheet.
        :param short_name:          Short name of the vocabulary. Input from sheet.
        :param sparql_graph:        Required to name the sparql graph in fuseki.
        :param namespace:           Namespace to fill in void:uriSpace in Skosmos entry file.
        :param temp_path:           File path to temporary folders. Input from default.cfg.
        :param update:              The SheetUpdate object for this vocabulary.
        :param logger:              The logger...
        """
        self.logger = logger
        self.title = title.strip()
        self.url = url.strip()
        self.short_name = short_name.strip()
        self.file_end = file_type.strip().lower()
        self.sparql_graph = sparql_graph.strip()
        self.namespace = namespace.strip()
        self.temp_path = temp_path
        self.local_file_name = ''
        if default_language.strip() != '':
            self.default_language = default_language.strip()
        else:
            self.default_language = None

        self.sheet_updates = update
        if self.namespace == '':
            self.sheet_updates.namespace = self.namespace

        self.graph = None
        self.mime_type = ''

    def process(self):
        """Goes through the various steps to process the vocabuarly.

        1. Check if the mime type given is valid.
        2. Download the file from the given url.
        3. Skosify the vocabulary.
        4. Upload the file to Fuseki.
        5. Clean up temporary files.
        """
        self.mime_type = self.check_mime_type(self.file_end)
        self.download_file(self.url)
        self.graph = SkosifiedGraph(self.local_file_name, self.file_end, self.title, self.namespace, self.temp_path,
                                    self.default_language, self.sheet_updates)
        try:
            self.graph.process()
        except NoNamespaceDetectedError as error:
            self.logger.exception(str(error))
            self.sheet_updates.error_type = 'NO NAMESPACE DETECTED'
            self.sheet_updates.error_message = str(error)

        self.sheet_updates.namespace = str(self.graph.namespace)

        if self.graph.namespace == '':
            raise NoNamespaceDetectedError('Could not determine a namespace. Please provide one.')

        # See if the file type has changed. This happens if skosify is successful.
        self.mime_type = self.check_mime_type(self.graph.format)
        self.local_file_name = self.graph.file_name

        self.upload_file()
        self.sheet_updates.skosmos_entry = self.create_skosmos_entry()

    def check_mime_type(self, file_type):
        """
        Set mime type and check if it is a valid value. Otherwise continue.
        IMPORTANT: THIS DOES NOT CHECK IF THE PROVIDED FILE ACTUALLY HAS THIS MIME TYPE!
        """
        if file_type == 'rdf':
            return RDF_MIME_TYPE
        elif file_type == 'ttl':
            return TURTLE_MIME_TYPE
        elif file_type == 'n3':
            return N3_MIME_TYPE
        elif file_type == 'nt':
            return NT_MIME_TYPE
        elif file_type == 'json':
            return JSON_LD_MIME_TYPE
        else:
            self.sheet_updates.error_type = "FILE TYPE ERROR"
            self.sheet_updates.error_message = 'Invalid MIME Type: expected RDF, TTL, N3, NT or JSON, found ' + \
                                               file_type + '.'
            raise InvalidMIMETypeError('Invalid MIME Type found: ' + file_type + '.')

    def download_file(self, url: str):
        """
        Download the file from the given url.

        Will first attempt to download and read the file. Will only accept downloads with status code 200.
        If the file is archived it is unpacked. Can handle .zip & .gz. All other archives will lead to errors.
        Will load all content as binary and then decode to UTF-8.

        Write file to disk.

        :param url:     The url.

        :raises DownloadError   If the download could not be completed.
        """
        if url.startswith('http'):
            try:
                download_file_response = requests.get(url)
            except (requests.exceptions.RequestException, ConnectionError, TimeoutError) as error:
                self.sheet_updates.error_type = 'CONNECTION ERROR'
                self.sheet_updates.error_message = 'Could not connect to ' + url
                self.logger.exception(error)
                raise DownloadError('Could not download from ' + url + ' because of a connection error.')

            if not download_file_response.ok:
                self.sheet_updates.error_type = 'DOWNLOAD ERROR (' + str(download_file_response.status_code) + ')'
                self.sheet_updates.error_message = download_file_response.text
                raise DownloadError('Was unable to download the file from ' + url)
            content = download_file_response.content
            buffer = BytesIO(download_file_response.content)

        elif url.startswith('ftp'):
            import urllib.parse
            import ftplib
            parts = urllib.parse.urlparse(url)
            file_name = parts.path.split('/')[-1]
            path = parts.path.replace(file_name, '')
            ftp = ftplib.FTP(parts.netloc)
            ftp.login()
            ftp.cwd(path)
            ftp.retrbinary('RETR ' + file_name, open(self.temp_path + file_name, 'wb').write)
            ftp.quit()
            with open(self.temp_path + file_name, 'rb') as file:
                content = file.read()
                buffer = BytesIO(content)
        else:
            self.sheet_updates.error_type = 'DOWNLOAD ERROR'
            self.sheet_updates.error_message = 'Invalid protocol: only HTTP[S] & FTP are supported!'
            raise DownloadError('Invalid protocol: only HTTP[S] & FTP are supported!')

        # save downloaded file locally to ensure that it is unzipped
        # and does not need to be downloaded again for getting an URI
        file_name = self.temp_path + 'temporary.' + self.file_end.lower()
        if url.endswith('.zip'):
            z = zipfile.ZipFile(buffer)
            text = z.read(z.infolist()[0]).decode('utf-8')
        elif url.endswith('.gz'):
            text = gzip.decompress(content).decode('utf-8')
        else:
            text = content.decode('utf-8')

        with open(file_name, 'w', encoding='utf-8') as file:
            file.write(text)

        self.local_file_name = file_name

    def upload_file(self):
        """
        Upload the file to the fuseki triple store with PUT. This will overwrite an existing graph with the same name.

        TODO: Change upload to use SPARQL -> for incremental updates to avoid having to download all the files.

        :raises FusekiUploadError  if response status code is lower than 200 or higher than 300.
        """
        with open(self.temp_path + self.local_file_name, 'r', encoding='utf-8') as file:
            data = {'name': (self.short_name.lower(), file.read(), self.mime_type)}
            if self.sparql_graph == '':
                self.sheet_updates.error_type = 'NO GRAPH NAME'
                self.sheet_updates.error_message = 'A graph name is required for a upload to take place. Once set' \
                                                   ' the graph name should not be changed.'
                raise FusekiUploadError
            basic_url = 'http://localhost:3030/skosmos/data?graph=' + self.sparql_graph

            # replace graph on server. overwrites existing data.
            response = requests.request('PUT', basic_url, files=data)

            if not response.ok:
                self.sheet_updates.error_type = 'UPLOAD ERROR ' + str(response.status_code)
                self.sheet_updates.error_message = 'Could not upload item to fuseki: ' + str(response.text)
                raise FusekiUploadError('Could not upload vocabulary ' + self.title + '.')

            self.sheet_updates.triple_count = str(json.loads(response.text)['tripleCount'])

    def create_skosmos_entry(self):
        """Create a basic skosmos config entry. Has to be adjust this by hand and then copy it into the file."""
        short_name = self.short_name.lower().replace(' ', '_')
        result = ':' + short_name + ' a skosmos:Vocabulary, void:Dataset ;\n'
        result += '\tdc:title "' + self.title + '"@en ;\n'
        result += '\tskosmos:shortName "' + self.short_name + '" ;\n'
        result += '\tdc:subject :cat_general ;\n'
        result += '\tvoid:uriSpace "' + str(self.namespace) + '" ;\n'
        result += '\tskosmos:language "en" ;\n'
        result += '\tskosmos:defaultLanguage "en" ;\n'
        result += '\tskosmos:showTopConcepts true ;\n'
        result += '\tvoid:sparqlEndpoint <http://localhost:6081/skosmos/sparql> ;\n'
        # LAST LINE NEEDS TO END WITH A DOT IF EXPANDED!!
        result += '\tskosmos:sparqlGraph <' + str(self.sparql_graph) + '> .\n'
        return result


def update_fuseki(config):
    try:
        credentials = config['data']['base'] + config['data']['credentials']
        temp_path = config['data']['base'] + config['data']['temporary']

        c = pygsheets.authorize(outh_file=credentials + 'client_secrets.json',
                                outh_creds_store=credentials,
                                outh_nonlocal=True)
        sheet = c.open(config['sheet']['sheet_name']).sheet1

        num_col = len(sheet.get_col(1))
        for i in range(2, num_col):
            try:
                row = sheet.get_row(i)
            except googleapiclient.errors.HttpError:
                time.sleep(100)
                row = sheet.get_row(i)
            if len(row) >= int(config['sheet']['last_column']):
                # Ignore vocabularies which are not ready.
                if row[READY] == 'y':
                    update = SheetUpdate()

                    fuseki = FusekiUpdate(title=row[TITLE],
                                          url=row[URL],
                                          file_type=row[FILE_TYPE],
                                          short_name=row[SHORT_NAME],
                                          sparql_graph=row[SPARQL_GRAPH_NAME],
                                          namespace=row[NAMESPACE],
                                          default_language=row[DEFAULT_LANGUAGE],
                                          temp_path=temp_path,
                                          update=update)
                    try:
                        fuseki.process()
                    except (InvalidMIMETypeError, DownloadError, FusekiUploadError, NoNamespaceDetectedError) as error:
                        logging.exception(str(error))
                        pass
                    # catch all unhandled exceptions. This should be updated as new exceptions occur.
                    except Exception as error:
                        update.error_type = 'UNKNOWN ERROR (' + str(type(error)) + ')'
                        update.error_message = str(error)
                        logging.exception('Unhandled exception occurred: ')
                        pass

                    # reload the sheet data to ensure that no data is lost.
                    try:
                        row = sheet.get_row(i)
                    except googleapiclient.errors.HttpError:
                        time.sleep(100)
                        row = sheet.get_row(i)

                    # update the sheet with the values gathered. some of these may be empty.
                    row[NAMESPACE] = update.namespace
                    row[TRIPLE_COUNT] = update.triple_count
                    row[ERROR_TYPE] = update.error_type
                    row[ERROR] = update.error_message
                    row[SKOSMOS_ENTRY] = update.skosmos_entry

                    try:
                        sheet.update_row(i, row)
                    except googleapiclient.errors.HttpError:
                        time.sleep(100)
                        sheet.update_row(i, row)

                    # clean temporary folders to ensure that no corrupted files are left behind if something went wrong.
                    for root, dirs, files in os.walk(temp_path):
                        for file in files:
                            os.remove(root + file)
            else:
                sheet.update_cell('L' + str(i), '#')
    except Exception:
        logging.critical('Something unexpected happened and the application has ended early:', exc_info=True)
    else:
        logging.info('APPLICATION ENDED SUCCESSFULLY.')
