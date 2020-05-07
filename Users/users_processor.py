import os
import csv
from datetime import datetime
import json

class User(object):
	unknown = 1
	person_record_type_id = '0121t0000005hIfAAI' # '0121t0000005hIfAAI' # prod_person_account_id

	def __init__(self, *args):
		self.id = args[0]['id']
		self.country = args[0]['countryname']
		email = f'{self.id}test@test.com' #args[0]['email']
		self.email = f'{email}'
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
	with open(os.path.join(os.path.dirname(__file__), 'newUsers.csv'), mode='r') as fread:
		raw = csv.DictReader(fread)

		for row in raw:
			users.append(User(row))

	print(User.unknown)
	print(len(users))
	users_dict = [user.__dict__ for user in users]


	with open(os.path.join(os.path.dirname(__file__),'newUsersProcessed.csv'), mode='w') as fwrite:
		fields = list(users[0].__dict__.keys())
		writer = csv.DictWriter(fwrite, fields)
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


def map_magento_id_to_sf_id():
	map = dict()
	
	with open(os.path.join(os.path.dirname(__file__), 'usersFromMagento.json'), mode='r') as magento_json:
		data = json.load(magento_json)
		counter = 0
		for item in data['items']:
			sf_id = next((x['value'] for x in item['custom_attributes'] if x['attribute_code'] == 'salesforce_id'), None)

			if not sf_id:
				counter += 1
			else:
				map[sf_id] = item['id']

	with open(os.path.join(os.path.dirname(__file__), 'usersPushedWithErrors.csv'), mode='r') as sf_accs:
		reader = csv.DictReader(sf_accs)

		with open(os.path.join(os.path.dirname(__file__), 'usersPushedWithErrorsMapped.csv'), mode='w') as sf_accs_with_magento:
			fields = list(reader.fieldnames)
			fields.append('MagentoId')
			writer = csv.DictWriter(sf_accs_with_magento, fields)
			writer.writeheader()

			for row in reader:
				id = map.get(row['ID'], None)

				if id:
					new_row = dict(row)
					new_row['MagentoId'] = id
					writer.writerow(new_row)
				else:
					print(row)

def update_accs_with_stripe_tokens():
	stripe_dict = dict()

	with open('/Users/roman/Downloads/customers.csv', mode='r') as stripe:
		reader = csv.DictReader(stripe)

		for s in reader:
			stripe_dict[s['Email']] = s
	
	with open('/Users/roman/Downloads/freeAccountsWithStripeCustomerId.csv', mode='r') as accs:
		reader = csv.DictReader(accs)

		with open(os.path.join(os.path.dirname(__file__), 'accs_updated_stripe_customer_id.csv'), mode='w') as accs_with_tokens:
			writer = csv.DictWriter(accs_with_tokens, ['Id', 'Email', 'Description', 'Customer', 'Token', 'SF_Customer', 'SF_Token'])
 
			writer.writeheader()

			count = 0
			no_count = 0

			for a in reader:
				s = stripe_dict.get(a['PersonEmail'], None)

				if s:
					if s['id'] != a['Stripe_Customer__c']:
						# print(f'NOT MATCH: {a["PersonEmail"]} {s["id"]} {a["Stripe_Customer__c"]}')
						writer.writerow(dict(Id=a['Id'], Email=a['PersonEmail'], Description=s['Description'], Customer=s['id'], Token=s['Card ID'], SF_Customer=a['Stripe_Customer__c'], SF_Token=a['Stripe_Card_Token__c']))
					# customer = s['id'] if not a['STRIPE_CUSTOMER__C'] or a['STRIPE_CUSTOMER__C'] == 'NULL' else a['STRIPE_CUSTOMER__C']
					# token = s['Card ID']  if not a['STRIPE_CARD_TOKEN__C'] else a['STRIPE_CARD_TOKEN__C']
					# writer.writerow(dict(Id=a['ID'], Email=a['PERSONEMAIL'], Description=s['Description'], Customer=customer, Token=token, SF_Customer=a['STRIPE_CUSTOMER__C'], SF_Token=a['STRIPE_CARD_TOKEN__C']))
						count += 1
				else:
					print(f"{a['Id']}")
					writer.writerow(dict(Id=a['Id'], Email=a['PersonEmail'], Description=None, Customer='INVALID', Token=None, SF_Customer=a['Stripe_Customer__c'], SF_Token=a['Stripe_Card_Token__c']))
					# customer = None if not a['STRIPE_CUSTOMER__C'] or a['STRIPE_CUSTOMER__C'] == 'NULL' else a['STRIPE_CUSTOMER__C']
					# writer.writerow(dict(Id=a['ID'], Email=a['PERSONEMAIL'], Description=None, Customer=customer, Token=a['STRIPE_CARD_TOKEN__C'], SF_Customer=a['STRIPE_CUSTOMER__C'], SF_Token=a['STRIPE_CARD_TOKEN__C']))
					no_count += 1

			print(count)
			print(no_count)

def verify_accounts():
	magento_dict = dict()

	with open('/Users/roman/Downloads/user_plans_magento.csv', mode='r') as magento:
		reader = csv.DictReader(magento)

		for r in reader:
			magento_dict[r['entity_id']] = r['value']

	with open('/Users/roman/Downloads/accountsWithSubscriptionDetails.csv', mode='r') as sf:
		reader = csv.DictReader(sf)

		for r in reader:
			magento_val = magento_dict.get(int(float(r['Magento_Id__c'])), None)

			if not magento_val:
				print(f'there is not magento for sf {r["Magento_Id__c"]}')
			else:
				if magento_val != r['Subscription_Type__c']:
					print(f'Alert, magento {magento_val}, sf {r["Subscription_Type__c"]}')

def get_value_or_none(val):
	return '' if not val or 'NULL' == val else val

def get_money(val):
	amount = get_value_or_none(val)

	return float(amount)/100 if amount else amount

def process_historical_order_sales_ad():
	users_dict = dict()

	with open('/Users/roman/Programing/python/uwbcsv/Users/usersSF.csv', mode='r') as users:
		reader = csv.DictReader(users)

		for user in reader:
			users_dict[int(float(user['MIGRATION_ID__C']))] = user['ID']
	
	products_dict = dict()

	with open('/Users/roman/Programing/python/uwbcsv/Users/productsSF.csv', mode='r') as products:
		reader = csv.DictReader(products)

		for product in reader:
			products_dict[int(float(product['MIGRATION_ID__C']))] = product['ID']

	orders_dict = dict()

	with open('/Users/roman/Programing/python/uwbcsv/Users/success051319024451093.csv', mode='r') as orders:
		reader = csv.DictReader(orders)

		for order in reader:
			orders_dict[int(float(order['ID']))] = order['SF_ID']
			

	with open('/Users/roman/Downloads/ordersMigration/orderLinesSalesAds.csv', mode='r') as oli:
		reader = csv.DictReader(oli)

		with open('/Users/roman/Downloads/ordersMigration/orderLinesSalesAdsHist.csv', mode='w') as historical_sales_ads_olis:
			writer = csv.DictWriter(historical_sales_ads_olis, ['migration_id', 'order_id', 'price', 'text', 'wine_name', 'product_id', 'sa_price', 'seller_id', 'sales_fee', 'sa_state'])
			writer.writeheader()

			for oli in reader:
				hist = dict()

				order_id = orders_dict.get(int(oli['order_id']), None)
				price = get_money(oli['price_cents'])
				text = get_value_or_none(oli['text'])
				wine = get_value_or_none(oli['wine'])
				bottle = products_dict.get(int(oli['bottle_id']), None)
				sa_price = get_money(oli['sa_price'])
				user_id = users_dict.get(int(oli['seller_id']), None)
				sales_fee = get_money(oli['sales_fee_cents'])
				state = get_value_or_none(oli['sa_state'])


				if not order_id:
					print(f'There is no data for order id {oli["order_id"]}')
					continue

				hist['migration_id'] = oli['id']
				hist['order_id'] = order_id
				hist['price'] = price
				hist['text'] = text
				hist['wine_name'] = wine
				hist['product_id'] = bottle
				hist['sa_price'] = sa_price
				hist['sa_price'] = sa_price
				hist['seller_id'] = get_value_or_none(user_id)
				hist['sales_fee'] = sales_fee
				hist['sa_state'] = state

				writer.writerow(hist)


def process_historical_order_bid():
	users_dict = dict()

	with open('/Users/roman/Programing/python/uwbcsv/Users/usersSF.csv', mode='r') as users:
		reader = csv.DictReader(users)

		for user in reader:
			users_dict[int(float(user['MIGRATION_ID__C']))] = user['ID']

	orders_dict = dict()

	with open('/Users/roman/Programing/python/uwbcsv/Users/success051319024451093.csv', mode='r') as orders:
		reader = csv.DictReader(orders)

		for order in reader:
			orders_dict[int(float(order['ID']))] = order['SF_ID']
			

	with open('/Users/roman/Downloads/ordersMigration/orderLinesBids.csv', mode='r') as oli:
		reader = csv.DictReader(oli)

		with open('/Users/roman/Downloads/ordersMigration/orderLinesBidsHist.csv', mode='w') as historical_sales_ads_olis:
			writer = csv.DictWriter(historical_sales_ads_olis, ['migration_id', 'order_id', 'price', 'text', 'state', 'amount', 'user_id'])
			writer.writeheader()

			for oli in reader:
				hist = dict()

				order_id = orders_dict.get(int(oli['order_id']), None)
				price = get_money(oli['price_cents'])
				text = get_value_or_none(oli['text'])
				user_id = users_dict.get(int(oli['user_id']), None)
				state = get_value_or_none(oli['state'])
				amount = get_money(oli['amount_cents'])

				if not order_id:
					print(f'There is no data for order id {oli["order_id"]}')
					continue

				hist['migration_id'] = oli['id']
				hist['order_id'] = order_id
				hist['price'] = price
				hist['text'] = text
				hist['state'] = state
				hist['amount'] = amount
				hist['user_id'] = get_value_or_none(user_id)

				writer.writerow(hist)


def process_historical_order_bsp():
	users_dict = dict()

	with open('/Users/roman/Programing/python/uwbcsv/Users/usersSF.csv', mode='r') as users:
		reader = csv.DictReader(users)

		for user in reader:
			users_dict[int(float(user['MIGRATION_ID__C']))] = user['ID']

	orders_dict = dict()

	with open('/Users/roman/Programing/python/uwbcsv/Users/success051319024451093.csv', mode='r') as orders:
		reader = csv.DictReader(orders)

		for order in reader:
			orders_dict[int(float(order['ID']))] = order['SF_ID']
			

	with open('/Users/roman/Downloads/ordersMigration/orderLinesBottleStorageProducts.csv', mode='r') as oli:
		reader = csv.DictReader(oli)

		with open('/Users/roman/Downloads/ordersMigration/orderLinesBottleStorageProductsHist.csv', mode='w') as historical_sales_ads_olis:
			writer = csv.DictWriter(historical_sales_ads_olis, ['migration_id', 'order_id', 'price', 'text', 'amount_of_bottles', 'amount', 'user_id'])
			writer.writeheader()

			for oli in reader:
				hist = dict()

				order_id = orders_dict.get(int(oli['order_id']), None)
				price = get_money(oli['price_cents'])
				text = get_value_or_none(oli['text'])
				user_id = users_dict.get(int(oli['user_id']), None)
				state = get_value_or_none(oli['amount_of_bottles'])
				amount = get_money(oli['amount_cents'])

				if not order_id:
					print(f'There is no data for order id {oli["order_id"]}')
					continue

				hist['migration_id'] = oli['id']
				hist['order_id'] = order_id
				hist['price'] = price
				hist['text'] = text
				hist['amount_of_bottles'] = state
				hist['amount'] = amount
				hist['user_id'] = get_value_or_none(user_id)

				writer.writerow(hist)


def process_historical_order_products():
	users_dict = dict()

	with open('/Users/roman/Programing/python/uwbcsv/Users/usersSF.csv', mode='r') as users:
		reader = csv.DictReader(users)

		for user in reader:
			users_dict[int(float(user['MIGRATION_ID__C']))] = user['ID']

	orders_dict = dict()

	with open('/Users/roman/Programing/python/uwbcsv/Users/success051319024451093.csv', mode='r') as orders:
		reader = csv.DictReader(orders)

		for order in reader:
			orders_dict[int(float(order['ID']))] = order['SF_ID']
			

	with open('/Users/roman/Downloads/ordersMigration/orderLinesProducts.csv', mode='r') as oli:
		reader = csv.DictReader(oli)

		with open('/Users/roman/Downloads/ordersMigration/orderLinesProductsHist.csv', mode='w') as historical_sales_ads_olis:
			writer = csv.DictWriter(historical_sales_ads_olis, ['migration_id', 'order_id', 'price', 'text', 'identifier'])
			writer.writeheader()

			for oli in reader:
				hist = dict()

				order_id = orders_dict.get(int(oli['order_id']), None)
				price = get_money(oli['price_cents'])
				text = get_value_or_none(oli['text'])
				state = get_value_or_none(oli['identifier'])

				if not order_id:
					print(f'There is no data for order id {oli["order_id"]}')
					continue

				hist['migration_id'] = oli['id']
				hist['order_id'] = order_id
				hist['price'] = price
				hist['text'] = text
				hist['identifier'] = state

				writer.writerow(hist)



if __name__ == '__main__':
	# map_magento_id_to_email()
	# main()
	# map_magento_id_to_sf_id()
	# update_accs_with_stripe_tokens()

	# verify_accounts()

	process_historical_order_products()