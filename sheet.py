import logging
import httplib2
from apiclient import discovery
from oauth2client import client, tools
from oauth2client.file import Storage
from googleapiclient.errors import HttpError


class GoogleSheet(object):

    def __init__(self, sheet_id, scopes, application_name, client_secret,
                 credentials, logger=logging.getLogger('google-sheet')):
        self.logger = logger
        self.sheet_id = sheet_id
        self.values = None
        self.service = None
        self.initialize_service(scopes, application_name, client_secret, credentials)

    def initialize_service(self, scopes, application_name, secrets_file, credential_path):
        """
        Authorizes the script with the Google Sheets API.

        Uses the credentials found in CREDENTIALS_FILE. If they are invalid or do not exist new credentials are loaded.
        If new credentials are loaded a browser is necessary to finish the authentication flow.
        But the credentials should be very long lived.
        """
        self.logger.debug('Using local file for authorization with file name: %s.', credential_path)
        store = Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            self.logger.critical('No credentials or invalid credentials found. Loading new credentials through flow. '
                                 'This flow requires a browser to enter login credentials.')
            flow = client.flow_from_clientsecrets(secrets_file, scopes)
            flow.user_agent = application_name
            credentials = tools.run_flow(flow, store)
            self.logger.info('Successfully stored new credentials in: ' + credential_path)

        http = credentials.authorize(httplib2.Http())
        self.service = discovery.build('sheets', 'v4', http=http)

    def load_sheet(self, cells: str):
        """Load the entire sheet into self.values
        :param cells:   The range that should be loaded. Can be two letters (like A:E) to load all rows for these
                        columns or only specific rows (like A3:F17).
        """
        try:
            self.values = self.service.spreadsheets().values().get(spreadsheetId=self.sheet_id, range=cells)\
                .execute().get('values', [])
        except HttpError as http_error:
            self.logger.critical(str(http_error))

    def store_sheet(self, cells: str):
        """
        Store all values in the sheet.

        :param cells:   The range that should be stored. Can be two letters (like A:E) to load all rows for these
                        columns or only specific rows (like A3:F17).
        """
        # It is necessary to pack this value like this as this is what the API expects.
        pack = list()
        pack.append(self.values)
        body = dict()
        body['values'] = list()
        body['values'].append(pack)
        try:
            self.service.spreadsheets().values().update(spreadsheetId=self.sheet_id,
                                                        includeValuesInResponse=True,
                                                        responseValueRenderOption='FORMATTED_VALUE',
                                                        valueInputOption='USER_ENTERED',
                                                        body=body,
                                                        range=cells).execute()
        except HttpError as http_error:
            self.logger.critical(str(http_error))
