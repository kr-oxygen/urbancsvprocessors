import csv
import os

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
	with open(os.path.abspath(os.path.join('Producers', 'producersids.csv')), mode='r') as producers:
		producer_reader = csv.DictReader(producers)
		producsers_map = dict((row['MIGRATION_ID__C'], row['ID']) for row in producer_reader)

		with open(os.path.join(os.path.dirname(__file__),'wines_new.csv'), mode='r') as wines:
			wines_reader = csv.DictReader(wines, delimiter='\t')

			with open(os.path.join(os.path.dirname(__file__),'wineswithproducers.csv'), mode='w') as wines_with_producers:
				columns = wines_reader.fieldnames.copy()
				columns.append('PRODUCER_SALESFORCE_ID')
				
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

							writer.writerow(new_row)

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

if __name__ == '__main__':
	map_producer_ids_from_sf()