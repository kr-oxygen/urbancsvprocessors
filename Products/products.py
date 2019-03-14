import csv
import os

bottle_record_type_id = '0121t0000005h6JAAQ'

def get_wines():
	wine_id_to_wine_object_dict = dict()

	with open(os.path.join('Wines', 'wineswithidsandproducers.csv'), mode='r') as wines:
		wines_reader = csv.DictReader(wines)

		for wine in wines_reader:
			wine_id_to_wine_object_dict[wine['MIGRATION_ID__C']] = wine

	return wine_id_to_wine_object_dict

def get_bottle_unique_name(wine_id_to_wine_object_dict, bottle_row):
	wine_id = bottle_row['WineId']
	wine = wine_id_to_wine_object_dict.get(wine_id, None)
				
	if not wine:
		return None

	wine_name = wine['NAME']
	
	bottle_size = bottle_row['BottleContentSize']
	year = bottle_row['Year']
	
	bottle_unique_name = f'{wine_name}-{bottle_size}---Vintage-{year}'

	return bottle_unique_name

def fill_products_with_sf_ids():
	warehouse_id = None
	cells_dict = dict()

	with open(os.path.abspath(os.path.join('WineCellarLocations', 'cellswithids.csv')), mode='r') as cells:
		cells_reader = csv.DictReader(cells)

		for cell in cells_reader:
			cells_dict[cell['NAME']] = cell['ID']
			if not warehouse_id:
				warehouse_id = cell['WAREHOUSE__C']
	
	photos_dict = dict()

	with open(os.path.abspath(os.path.join('Photos','photoswithids.csv')), mode='r') as photos:
		photos_reader = csv.DictReader(photos)

		for photo in photos_reader:
			photo_unique_name = photo['PHOTO_UNIQUE_NAME__C']
			
			if photo_unique_name not in  photos_dict:
				photos_dict[photo_unique_name] = list()

			photos_dict[photo_unique_name].append(photo['ID'])

	wine_id_to_wine_object_dict = get_wines()
	bottle_to_photo_dict = dict()

	accounts_dict = dict()

	with open(os.path.abspath(os.path.join('Users','userswithids.csv')), mode='r') as accounts:
		accounts_reader = csv.DictReader(accounts)

		for account in accounts_reader:
			accounts_dict[str(int(float(account['MIGRATION_ID__C'])))] = account['ID']

	errors = dict(Wines=dict(),Cells=dict(),Accounts=dict())

	with open('products5.csv', mode='r') as products:
		reader = csv.DictReader(products, delimiter='\t')
		fields = set(reader.fieldnames)
		fields.update(['SFWarehouseId', 'SFWarehouseCellId', 'SFMainPhotoId', 'SFAccountId', 'SFWineId', 'SFProducerId', 'RecordTypeId'])

		with open('productswithdependencies.csv', mode='w') as product_with_deps:
			writer = csv.DictWriter(product_with_deps, list(fields), delimiter='\t')

			writer.writeheader()

			counter = 0

			for bottle in reader:
				# copy initial bottle details
				new_bottle = dict(bottle.items())

				wine = wine_id_to_wine_object_dict.get(bottle['WineId'], None)

				# obtaining wine and producer details
				if not wine:
					errors['Wines'][bottle["WineId"]] = bottle["Id"]
					# print(f'ALERT!!! WINE: {bottle["Id"]}, wineId: {bottle["WineId"]}')
				else:
					new_bottle['SFWineId'] = wine['ID']
					new_bottle['SFProducerId'] = wine['PRODUCER__C']

				# obtainig cellar location details
				cell_name = bottle['WarehouseCellLocationName']
				
				if cell_name:
					cell = cells_dict.get(cell_name, None)

					if not cell:
						errors['Cells'][cell_name] = (bottle["Id"],bottle["Status"])
						# print(f'ALERT!!! CELL: {bottle["Id"]}, cell: {cell_name}')
					else:
						new_bottle['SFWarehouseId'] = warehouse_id
						new_bottle['SFWarehouseCellId'] = cell

				# obtaining account details
				account = accounts_dict.get(bottle['AccountId'], None)

				if not account:
					errors['Accounts'][bottle["AccountId"]] = bottle["Id"]
					continue
					# print(f'ALERT!!! ACCOUNT: {bottle["Id"]}, accId: {bottle["AccountId"]}')
				else:
					new_bottle['SFAccountId'] = account
				
				# obtaining photo details
				if bottle['PhotoLink']:
					bottle_unique_name = get_bottle_unique_name(wine_id_to_wine_object_dict, bottle)

					if not bottle_unique_name:
						errors['Wines'][bottle["WineId"]] = bottle["Id"]
						# print(f'ALERT!!! WINE: {bottle["Id"]}, {bottle["WineId"]}')
						continue

					photo_id = photos_dict.get(bottle_unique_name, None)

					if photo_id:
						new_bottle['SFMainPhotoId'] = photo_id[0]
						bottle_to_photo_dict[bottle['Id']] = photo_id[0]

				new_bottle['RecordTypeId'] = bottle_record_type_id
				writer.writerow(new_bottle)
				counter += 1

			print(counter)

	print('\n\n\n')

	for ek,ev in errors.items():
		with open(f'{ek}_errors.txt', mode='w') as err:
			for evk, evv in ev.items():
				if not evk:
					print(f'{ek}, ",".join(evv)')
				else:
					# if ek == 'Cells':
					# 	err.write(f'{evk} -> {",".join(evv)},\n')
					# else:
					err.write(f"'{evk}',\n")
		# print(ek)
		# print(f'\t{",".join(ev.keys())}')


	with open(os.path.abspath(os.path.join('Photos','photoswithproductids.csv')), mode='w') as product_to_photo:
		writer = csv.DictWriter(product_to_photo, ['ProductId', 'SFPhotoId'])

		writer.writeheader()

		for k, v in bottle_to_photo_dict.items():
			writer.writerow(dict(ProductId=k, SFPhotoId=v))


def fill_photos():
	wine_id_to_name_dict = get_wines()

	photos_dict = dict()
	
	with open('products4.csv', mode='r') as products:
		reader = csv.DictReader(products, delimiter='\t')

		for row in reader:
			link = row['PhotoLink']
			
			if not link:
				continue
			
			bottle_unique_name = get_bottle_unique_name(wine_id_to_name_dict, row)

			if not bottle_unique_name:
				continue

			if link not in photos_dict:
				photos_dict[bottle_unique_name] = set()
			photos_dict[bottle_unique_name].add(link)

	with open(os.path.abspath(os.path.join('Photos', 'photos.csv')), mode='w') as photos:
		photo_fields = ['Photo_Unique_Name__c', 'Link']

		writer = csv.DictWriter(photos, photo_fields)
		writer.writeheader()

		for k, v in photos_dict.items():
			writer.writerow(dict(Photo_Unique_Name__c=k, Link=v.pop()))

def process_insert_errors():
	with open('error031319085916067.csv', mode='r') as errors:
		errors_reader = csv.DictReader(errors)

		error_messages = set()

		for error in errors_reader:
			# if 'Warehouse cell should not be occupied' not in error['ERROR'] and 'Bottle Request Name' not in error['ERROR']:
			error_messages.add(error['ERROR'])

		for e in error_messages:
			print(e)

if __name__ == '__main__':
	# fill_photos() # call first to generate s3 photo object then extract ids to insert that ids to the product
	process_insert_errors() # call after photo processing