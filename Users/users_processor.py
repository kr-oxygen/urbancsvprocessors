import os
import csv
from datetime import datetime

class User(object):
	unknown = 1
	email_counter = 0
	person_record_type_id = '0121t0000005hIfAAI' # prod_person_account_id

	def __init__(self, *args):
		self.id = args[0]['id']
		self.country = args[0]['countryname'] 
		User.email_counter += 1
		email = args[0]['email']
		self.email = f'{User.email_counter}_{email}'
		self.created = self.process_date(args[0]['created_at'])
		self.updated = self.process_date(args[0]['updated_at'])
		self.deleted = self.process_date(args[0]['deleted_at'])
		self.stripe_customer = args[0]['stripe_customer_id']
		self.name = args[0]['name']
		self.phone = args[0]['phone_number']
		if not self.phone or 'NULL' in self.phone:
			self.phone = '00000000'
		self.person_city = args[0]['personcity']
		self.address = args[0]['address']
		self.address_city = args[0]['addresscity']
		self.zipcode = args[0]['zipcode']
		self.process_name()
		self.process_city()
		self.record_type_id = User.person_record_type_id

	def process_date(self, d):
		return '' if not d or 'NULL' == d else datetime.strptime(d, '%Y-%m-%d %H:%M:%S.%f').strftime('%Y-%m-%dT%H:%M:%SZ')

	def process_name(self):
		if self.name == 'NULL':
			self.first_name = f'User {User.unknown}'
			self.last_name = 'UNKNOWN'
			print(f'Unknown user {User.unknown}')
			User.unknown += 1

		else:
			parts = self.name.split()
			if len(parts) > 1:
				self.first_name = parts[0]
				self.last_name = ' '.join(parts[1:])
			else:
				self.first_name = parts[0]
				self.last_name = 'ADD LASTNAME'

	def process_city(self):
		self.city = self.address_city if self.address_city == 'NULL' else self.person_city


def main():
	users = []
	with open(os.path.join(os.path.dirname(__file__), 'delta.csv'), mode='r') as fread:
		raw = csv.DictReader(fread)

		for row in raw:
			users.append(User(row))

	print(User.unknown)
	print(len(users))
	users_dict = [user.__dict__ for user in users]


	with open(os.path.join(os.path.dirname(__file__),'deltaProcessed.csv'), mode='w') as fwrite:
		fields = users[0].__dict__.keys()
		writer = csv.DictWriter(fwrite, users[0].__dict__.keys())
		writer.writeheader()

		writer.writerows(users_dict)
		# (fwrite, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)

def process_extract():
	with open(os.path.join(os.path.dirname(__file__),'usersFromSf.csv'), mode='r') as rf:
		raw = csv.DictReader(rf)

		with open(os.path.join(os.path.dirname(__file__),'usersFromSfProcessed.csv'), mode='w') as wf:

			writer = csv.DictWriter(wf, raw.fieldnames)
			# ['ID', 'MIGRATION_ID__C'])
			writer.writeheader()
			
			for row in raw:
				writer.writerow(dict(ID=row['ID'], MIGRATION_ID__C=int(float(row["MIGRATION_ID__C"]))))

def comparator():
	first_lines = set()
	second_lines = set()

	with open(os.path.join(os.path.dirname(__file__),'usersProcessed.csv'), mode='r') as first:
		for i in first.readlines():
			first_lines.add(i.split(',')[0])

	with open(os.path.join(os.path.dirname(__file__),'newUsersProcessed.csv'), mode='r') as second:
		for i in second.readlines():
			second_lines.add(i.split(',')[0])

	for l in list(second_lines - first_lines):
		print(l)

def map_magento_id_to_email():
	email_id_map = dict()

	with open(os.path.join(os.path.dirname(__file__),'emailtomigrationId.csv'), mode='r') as f:
		reader = csv.DictReader(f)

		for r in reader:
			email_id_map[int(r['id'])] = r['email']

	with open(os.path.join(os.path.dirname(__file__),'magentoidtomigrationid.csv'), mode='r') as f:
		reader = csv.DictReader(f)

		with open(os.path.join(os.path.dirname(__file__),'sf_id_email_map.csv'), mode='w') as fr:
			writer = csv.DictWriter(fr, ['Id', 'Email'])
			writer.writeheader()

			for r in reader:
				new_row = dict(Id=r['ID'], Email=email_id_map[int(float(r['MIGRATION_ID__C']))])
				writer.writerow(new_row)

if __name__ == '__main__':
	map_magento_id_to_email()