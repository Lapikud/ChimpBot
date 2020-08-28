# https://developers.google.com/sheets/api/quickstart/python

import json
import re
import time
from sys import exit, argv
from os import path, environ

from googleapiclient.discovery import build
from mailchimp3 import MailChimp

class EmptyEnvVariable(Exception):
	pass

class SpreadSheet:

	_service = None
	_sheet = None
	_sheet_id = None

	def __init__(self, api_key, sheet_id):
		self._service = build('sheets', 'v4', developerKey=api_key)
		self._sheet = self._service.spreadsheets()
		self._sheet_id = sheet_id

	def _get_data(self, range_name):
		result = self._sheet.values().get(spreadsheetId=self._sheet_id, range=range_name).execute()

		return result.get('values', [])

	def get_emails_only(self, range_name):
		raw_data = self._get_data(range_name)
		emails = []

		for item in raw_data[1:]:
			if item and is_email_valid(item[1]):
				emails.append(item[1])

		return emails

	def get_profiles(self, range_name):
		raw_data = self._get_data(range_name)
		profiles = []

		for item in raw_data:
			if item and is_email_valid(item[0]):
				name = item[1].split(" ")

				profiles.append({
					"email": item[0],
					"first_name": name[0],
					"last_name": name[-1]
				})


class LapMailChimp:

	_mpClient = None

	def __init__(self, api_key, user):
		self._mpClient = MailChimp(mc_api=api_key, mc_user=user)

	def get_all_emails(self, list_id):
		raw_data = self._mpClient.lists.members.all(list_id, get_all=True, fields="members.email_address")

		return list(map(lambda email: email['email_address'], raw_data['members']))

	def get_all_lists(self):
		return self._mpClient.lists.all(get_all=True, fields="lists.name,lists.id,lists.stats.member_count")

	def get_list_name(self, list_id):
		return self._mpClient.lists.get(list_id, fields="lists.name")

	def add_new_email(self, list_id, profile):
		if is_email_valid(profile["email"]):
			self._mpClient.lists.members.create(list_id, {
				'email_address': profile["email"],
				'status': 'subscribed',
				'merge_fields': {
					'FNAME': profile["first_name"],
					'LNAME': profile["last_name"]
				}
			})


def is_email_valid(email):
	return re.match(r"[^@]+@[^@]+\.[^@]+", email)


def load_env_variable(name):
	try:
		if not environ[name]:
			raise EmptyEnvVariable(f"Variable {name} is empty!")

		return environ[name]
	except KeyError:
		raise EmptyEnvVariable(f"Env variable not found: {name}\nMake sure you are running this in the docker container.\n")


if __name__ == '__main__':
	mc_api_key = load_env_variable("MAILCHIMP_API_KEY")
	mailChimp = LapMailChimp(mc_api_key, 'LAP-MailChimp Bot')

	try:
		mc_list_ids = load_env_variable("MAILCHIMP_LIST_ID").split(",")
	except EmptyEnvVariable as error:
		mc_lists = mailChimp.get_all_lists()
		
		print(f"No MAILCHIMP_LIST_ID specified, please choose a list ID")
		print(f"List ID	| Member count	| List name")
		print("----------------------------------------")

		for mc_list in mc_lists["lists"]:
			print(f"{mc_list['id']}	| {mc_list['stats']['member_count']}		| {mc_list['name']}	")

		exit(1)

	api_key = load_env_variable('GOOGLE_SHEETS_API_KEY')

	ss_id = load_env_variable('SPREADSHEET_ID')
	ss_range = load_env_variable('SPREADSHEET_RANGE_NAME')

	spreadSheet = SpreadSheet(api_key, ss_id)

	google_current_file = "./cache/current_google.json"

	while True:
		print("Checking for new emails...")
		if path.exists(google_current_file):
			# Load currently cached emails
			with open(google_current_file, "r") as file:
				data = json.load(file)

			# Get new data from google spreadsheet
			newData = spreadSheet.get_emails_only(ss_range)

			# Get email list difference
			diff = list(set(newData) - set(data))

			if diff:
				for mc_list in mc_list_ids:
					mc_all_emails = mailChimp.get_all_emails(mc_list)
					mc_list_name = mailChimp.get_list_name(mc_list)

					# Check if email is in new data
					for profile in diff:
						if profile in newData and profile["email"] not in mc_all_emails:
							print(f"New email added to {mc_list_name}: {profile['email']}")
							mailChimp.add_new_email(mc_list, profile)
			else:
				print("No new emails were found")

				# Move new data to current
				with open(google_current_file, 'w') as file:
					json.dump(newData, file, indent=4)
		else:
			print("First run!")
			# Create current data file
			with open(google_current_file, 'w') as file:
				data = spreadSheet.get_emails_only(ss_range)
				json.dump(data, file, indent=4)

		time.sleep(60)
