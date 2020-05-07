import csv
import os
import json

def update_full_name():
	with open(os.path.join(os.path.dirname(__file__),'wines.csv'), mode='r', encoding='utf-8', errors='ignore') as wines:
		reader = csv.DictReader(wines)
		with open(os.path.join(os.path.dirname(__file__),'winesToUpdate.csv'), mode='w') as to_update:
				writer = csv.DictWriter(to_update, ['Id', 'CombinedName'])
				writer.writeheader()

				for line in reader:
					combined_name = f'{line["Name"]} {line["Producer_Name__c"]}'
					new_line = dict(Id=line['Id'], CombinedName=combined_name)
					writer.writerow(new_line)

def errors():
	with open(os.path.join(os.path.dirname(__file__),'error030719081755151 Wines Load1.csv'), mode='r', encoding='utf-8', errors='ignore') as f:
		reader = csv.DictReader(f)
		
		restricted_picklist_errors = 0
		other_errors = 0

		for row in reader:
			error = row['ERROR']

			if 'restricted picklist' in error:
				restricted_picklist_errors += 1
			else:
				other_errors += 1
				print(row)

		print(f'Restricted errors number is {restricted_picklist_errors}')
		print(f'Not Restricted errors number is {other_errors}')

def map_producer_ids_from_sf():
	with open(os.path.abspath(os.path.join('Producers', 'producersWithMagentoAndSfIds.csv')), mode='r') as producers:
		producer_reader = csv.DictReader(producers)
		producsers_map = dict((row['MIGRATION_ID__C'], row['ID']) for row in producer_reader)

		prod_mag_map = dict()

		with open(os.path.join(os.path.dirname(__file__),'magentoWinesIds.json'), mode='r') as js:
			data = json.load(js)

			for d in data:
				prod_mag_map[d['label']] = d['value']

		# with open('/Users/roman/Downloads/Wines.json', mode='r') as wines_with_magento_id:
		# 	pwmir = csv.DictReader(wines_with_magento_id)

		# 	for r in pwmir:
		# 		prod_mag_map[r['Id']] = r['MagentoId']

		with open(os.path.join(os.path.dirname(__file__),'wines_new_2.csv'), mode='r') as wines:
			wines_reader = csv.DictReader(wines, delimiter='\t')

			with open(os.path.join(os.path.dirname(__file__),'wineswithproducers.csv'), mode='w') as wines_with_producers:
				columns = wines_reader.fieldnames.copy()
				columns.append('PRODUCER_SALESFORCE_ID')
				columns.append('Magento_Id')
				
				writer = csv.DictWriter(wines_with_producers, columns)
				
				writer.writeheader()

				with open(os.path.join(os.path.dirname(__file__),'wineswithoutproducers.csv'), mode='w') as wines_without_producers:
					ww = csv.DictWriter(wines_without_producers, wines_reader.fieldnames)
					ww.writeheader()
				
					for wine in wines_reader:
						sf_producer_id = producsers_map.get(wine['ProducerId'], None)
						if not sf_producer_id:
							ww.writerow(wine)
						else:
							new_row = dict(wine.items())
							new_row['PRODUCER_SALESFORCE_ID'] = sf_producer_id
							
							try:
								new_row['Magento_Id'] = prod_mag_map[wine['Name']]
								writer.writerow(new_row)
							except:
								print(wine['Name'])

def process_errors():
	with open(os.path.join(os.path.dirname(__file__),'error031119094053007.csv'), mode='r') as errors_file:
		errors_reader = csv.DictReader(errors_file)

		countries_to_region_dict = {}

		for error in errors_reader:
			if 'restricted picklist' in error['ERROR']:
				country = error['COUNTRY']

				if country not in countries_to_region_dict:
					countries_to_region_dict[country] = set()

				countries_to_region_dict[country].add(error['REGION'])
			else:
				print(error)

		for k,v in countries_to_region_dict.items():
			print(k)
			for item in v:
				print(f'\t{item}')

def error_records():
	with open(os.path.join(os.path.dirname(__file__),'error031119094053007.csv'), 'r') as errors:
		errors_reader = csv.DictReader(errors)
		ids = set()
		for error in errors_reader:
			ids.add(error['ID'])

		print(','.join(ids))

def wines_without_magento_id():
	wines_dict = dict()

	with open('/Users/roman/Downloads/wines.csv', mode='r') as wines:
		wines_reader = csv.DictReader(wines)

		for wine in wines_reader:
			if wine['value'] not in wines_dict.keys():
				wines_dict[wine['value']] = list()
				
			wines_dict[wine['value']].append(wine['option_id'])

	for k, v in wines_dict.items():
		if len(v) > 1:
			print(k, max(v))
		else:
			print(k, v)



if __name__ == '__main__':
	# map_producer_ids_from_sf()
	# wines_without_magento_id()
	update_full_name()