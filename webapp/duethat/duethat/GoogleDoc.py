from __future__ import print_function
import httplib2
import os

import io

import textract
from apiclient import discovery
from apiclient import errors
from apiclient.http import MediaIoBaseDownload
import oauth2client
from oauth2client import client
from oauth2client import tools

try:
	import argparse
	flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
	flags = None

# If modifying these scopes, delete your previously saved credentials
# at ./.credentials/drive-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Due That'

class GoogleDoc(object):
	def __init__(self):
		self.service = self._get_service()

	def get_list_of_readable_files(self):
		"""Retrieve a list of File resources.

		Args:
		  service: Drive API service instance.
		Returns:
		  List of File resources.
		"""
		temp_result = []
		page_token = None
		while True:
			try:
				param = {}
				if page_token:
					param['pageToken'] = page_token
				files = self.service.files().list(**param).execute()

				temp_result.extend(files['files'])
				page_token = files.get('nextPageToken')
				if not page_token:
					break
			except errors.HttpError, error:
				print
				'An error occurred: %s' % error
				break

		result = []

		for res in temp_result:
			if res['mimeType'] == 'application/vnd.google-apps.document':
				result.append(res)

		return result

	def get_text_from_file(self, file):
		filename = file['id'] + '.pdf'

		self._download_file(file, filename)
		text = textract.process(filename)
		os.remove(filename)
		return text

	def _get_service(self):
		credentials = self._get_credentials()
		http = credentials.authorize(httplib2.Http())
		service = discovery.build('drive', 'v3', http=http)
		return service

	# Do not use. Called by get_service()
	def _get_credentials(self):
		home_dir = os.path.expanduser('~')
		credential_dir = os.path.join(home_dir, '.credentials')
		if not os.path.exists(credential_dir):
			os.makedirs(credential_dir)
		credential_path = os.path.join(credential_dir, 'drive-python-quickstart.json')

		store = oauth2client.file.Storage(credential_path)
		credentials = store.get()

		if not credentials or credentials.invalid:
			flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
			flow.user_agent = APPLICATION_NAME
			if flags:
				credentials = tools.run_flow(flow, store, flags)
			else:  # Needed only for compatibility with Python 2.6
				credentials = tools.run(flow, store)
			print('Storing credentials to ' + credential_path)
		return credentials

	# do not use, called by get_text_from_file
	def _download_file(self, item, filename):
		"""Downloads item to filename."""
		id = item['id']
		request = self.service.files().export_media(fileId=id,
											   mimeType='application/pdf')
		fh = io.BytesIO()
		downloader = MediaIoBaseDownload(fh, request)
		done = False
		while done is False:
			status, done = downloader.next_chunk()
		open(filename, 'wb').write(fh.getvalue())

def sample():
	google_doc = GoogleDoc()
	readable_files = google_doc.get_list_of_readable_files()
	print (google_doc.get_text_from_file(readable_files[0]))

if __name__ == '__main__':
	sample()
