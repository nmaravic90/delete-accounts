#####################################################
# Deleted Accounts
# Development by: Nikola Maravic
#####################################################

import subprocess
# Check if a python module "requests" exists
try:
	import requests
except ImportError:
	subprocess.call(['pip', 'install', 'requests'])
finally:
	import requests
import sys
import csv
import os
import argparse
from datetime import date
try:
	import dateutil.parser
except ImportError:
	subprocess.call(['pip', 'install', 'python-dateutil'])
finally:
	import dateutil.parser
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from configparser import ConfigParser
from xml.etree import ElementTree 

# Global session
SESSION = requests.Session()

# Contacted function
def contact_url(url):
	try:
		response = requests.get(url)
		# If the response was successful, no Exception will be raised
		response.raise_for_status()

	except Exception:
		print(f'\n "{url}" not available!')
		print('\n### STATUS: Exiting program ###\n')
		sys.exit(0)
	else:
		print(f'\n Successfuly contacted {url}')

# Check URL function, if URL ends with '/' character
def check_url(url):
	if (not url.endswith('/')): url += '/'
	return url

# Login function
def login(url, username, password):
	loginParams = {'login': username, 'password': password}
	url = check_url(url)
	loginResponse = SESSION.get(f'{url}api/xml?action=login', params=loginParams)

	xmlLoginResponse = ElementTree.fromstring(loginResponse.content)
	loginStatus = xmlLoginResponse.find('status').get('code')
	
	if loginStatus == 'ok':
		print(f'\n Sucessfully logged with {username}\n')
	else:
		print('\n Invalid username or password')
		print('\n### STATUS: Exiting program ###\n')
		sys.exit(0)

# Create CSV report function
def create_report(report_file):
	with open(f'../{report_file}.csv', 'w', newline='') as file:
		writer = csv.writer(file)
		writer.writerow(['Accounts deleted report',f'Date: {date.today()}'])
		writer.writerow(['Accounts: ', 'Delete time in seconds:'])

# Append CSV report function
def append_report(report_file, account_id, accountName, seconds):
	with open(f'../{report_file}.csv', 'a', newline='') as file:
		writer = csv.writer(file)
		writer.writerow([f'ID: [{account_id}] - NAME: {accountName}', f'{seconds}'])

# Check if CSV file exist
def report_file_exist(report_file):
	try:
		if os.path.exists(f'../{report_file}.csv'):
  			os.remove(f'../{report_file}.csv')
	except Exception:
		print(f'\n "{report_file}.csv" is already open, please close file!')
		print('\n### STATUS: Exiting program ###\n')
		sys.exit(0)


# Check if "accounts.txt" file exist or empty
def account_file_exist(account_file):
	if not os.path.exists(f'../{account_file}'):
		print(f'\n "{account_file}" file doesn\'t exist!')
		print('\n### STATUS: Exiting program ###\n')
		sys.exit(0)
	elif os.path.getsize(f'../{account_file}') == 0:
		print(f'\n "{account_file}" file is empty!')
		print('\n### STATUS: Exiting program ###\n')
		sys.exit(0)

# Account delete function
def delete_account(account_file, report_file, url, username, password, disabled_months):
	print('### ACCOUNTS: ###\n')
	url = check_url(url)
	curent_time = date.today()
	sub_months = curent_time + relativedelta(months=-int(disabled_months))
	count = 1

	try:
		with open(f'../{account_file}', 'r') as file:
			
			for row in file:
				delete = False  
				purge = False
				obfuscated = False
				accounts = []

				account_id = row
				account_id = ''.join(i for i in account_id if i.isdigit())

				if(account_id == ''): account_id = 'invalid account id'

				# Check if the Account is DISABLED (API: account-list&filter-out-disabled=null)
				disabled_account_list = requests.post(f'{url}api/xml?action=account-list&filter-out-disabled=null', cookies=SESSION.cookies.get_dict())
				xml_response = ElementTree.fromstring(disabled_account_list.content)

				for account in xml_response.findall('accounts/account'):
					accounts.append(account.get('account-id'))

				for i, id in enumerate(accounts):
					if(id == account_id):
						account_name = [{ item.tag: item.text for item in el } for el in xml_response.findall('accounts/account')][i].get('name')
						account_disabled = [{ item.tag: item.text for item in el } for el in xml_response.findall('accounts/account')][i].get('disabled')

						if(account_disabled):
							disabled_time = parse(account_disabled)
							if(sub_months >= disabled_time.date()):
								delete = True 
								purge = True
							else:
								delete = False
								obfuscated = True
						
				# Call "account-delete" API for obfuscate or purge account
				if(delete):
					account_delete_params = {'account-id': account_id, 'purge': str(purge).lower() }
					account_delete = requests.post(f'{url}api/xml?action=account-delete', params=account_delete_params, cookies=SESSION.cookies.get_dict())

					xml_response = ElementTree.fromstring(account_delete.content)
					delete_status = xml_response.find('status').get('code')

					if delete_status == 'ok':
						append_report(report_file, account_id, account_name, account_delete.elapsed.total_seconds())
						print(f'{count}. ID: [{account_id}], NAME: "{account_name}" --> sucessfully delete in [{account_delete.elapsed.total_seconds()}] seconds')
					else:
						append_report(report_file, account_id, account_name, 'Failed to delete.')
						print(f'{count}. ID: [{account_id}], NAME: "{account_name}" --> failed to delete.')
				elif (obfuscated):
					append_report(report_file, account_id, account_name, 'Is already disabled.')
					print(f'{count}. ID: [{account_id}], NAME: "{account_name}" --> is already disabled.')
				else:
					append_report(report_file, account_id, 'Not found','Doesn\'t exist.')
					print(f'{count}. ID: [{account_id}], NAME: Not found --> doesn\'t exist.')

				count += 1	

			print('\n### STATUS: Completed ###\n')

	except Exception:
		print(f' No such file or directory: "{account_file}"')
		print('\n### STATUS: Exiting program ###\n')
		sys.exit(0)

def start():
	print('\n### DELETE BAMA ACCOUNTS ### ')
    # Adding a parameters from the console
	parser = argparse.ArgumentParser(description='This python program delete the accounts.')
	parser.add_argument('-b', '--URL', required=True, help='Url - example "http://account.com"')
	parser.add_argument('-u', '--USERNAME',  required=True, help='Username - example "admin@account.com"')
	parser.add_argument('-p', '--PASSWORD', required=True, help='Password - example "Admin1234"')
	parser.add_argument('-a', '--ACCOUNT_IDS_FILE',  required=True, help='Name for "TXT" file with Account ID-s - example "accounts.txt"')
	parser.add_argument('-r', '--REPORT_FILE', required=True, help='Name for "CSV" report file without extension with deleted results - example "report"')
	parser.add_argument('-d', '--DISABLED_MONTHS', required=False, help='Accounts disabled longer than this number of months should be deleted, default is 6 months')
	args = parser.parse_args()

	url = args.URL
	username  = args.USERNAME
	password = args.PASSWORD
	account_file = args.ACCOUNT_IDS_FILE
	report_file = args.REPORT_FILE

	# Set the number of months for delete accounts, which are disabled for more than that setting number (minimun is 6)
	if args.DISABLED_MONTHS and int(args.DISABLED_MONTHS) >= 6:
		disabled_months = args.DISABLED_MONTHS
	elif args.DISABLED_MONTHS and int(args.DISABLED_MONTHS) < 6:
		print('\n Number of months for deleted account should be greater than or equal to 6')
		print('\n### STATUS: Exiting program ###\n')
		sys.exit(0)
	else:
		disabled_months = 6
	
	if( not (url.startswith('http://') or url.startswith('https://'))):
		print('\n Url must contain "http://" or "https://"')
		print('\n### STATUS: Exiting program ###')
	elif os.path.splitext(account_file)[1] != '.txt':
		print(f'\n Insert file name "{account_file}" with extension')
		print('\n### STATUS: Exiting program ###\n')
	elif os.path.splitext(report_file)[1]:
		print(f'\n Insert only "CSV" file name, without extension "{os.path.splitext(report_file)[1]}"')
		print('\n### STATUS: Exiting program ###\n')
	else:
		report_file_exist(report_file)
		account_file_exist(account_file)
		create_report(report_file)
		contact_url(url)
		login(url, username, password)
		delete_account(account_file, report_file, url, username, password, disabled_months)
		
# Start program
start()

