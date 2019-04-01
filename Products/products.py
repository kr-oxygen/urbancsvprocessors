import csv
import os

bottle_record_type_id = '0121t0000005h6JAAQ'

def get_wines():
	wine_id_to_wine_object_dict = dict()

	with open(os.path.abspath(os.path.join('Wines', 'wineswithproducers.csv')), mode='r', encoding='utf-8') as wines:
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
	producer_name = wine['PRODUCER_NAME__C']
	
	bottle_size = bottle_row['BottleContentSize']
	year = 9999 if not bottle_row['Year'] or bottle_row['Year'] == '' or bottle_row['Year'] == 'NULL' else bottle_row['Year']
	brackets = '-{}'.format(bottle_row['BracketsWineName']) if bottle_row['BracketsWineName'] else ''
	
	bottle_unique_name = f'{wine_name}-{producer_name}-{bottle_size}-No-OC-Vintage-{year}-1{brackets}'

	return bottle_unique_name

def fill_products_with_sf_ids():
	warehouse_id = None
	# cells_dict = dict()

	# with open(os.path.abspath(os.path.join('WineCellarLocations', 'cellswithids.csv')), mode='r', encoding='utf-8') as cells:
	# 	cells_reader = csv.DictReader(cells)

	# 	for cell in cells_reader:
	# 		cells_dict[cell['NAME']] = cell['ID']
	# 		if not warehouse_id:
	# 			warehouse_id = cell['WAREHOUSE__C']
	
	photos_dict = dict()

	with open(os.path.abspath(os.path.join('Photos','photoswithids.csv')), mode='r', encoding='utf-8') as photos:
		photos_reader = csv.DictReader(photos)

		for photo in photos_reader:
			photo_unique_name = photo['PHOTO_UNIQUE_NAME__C']
			
			if photo_unique_name not in  photos_dict:
				photos_dict[photo_unique_name] = list()

			photos_dict[photo_unique_name].append(photo['ID'])

	wine_id_to_wine_object_dict = get_wines()
	bottle_to_photo_dict = dict()

	accounts_dict = dict()

	with open(os.path.abspath(os.path.join('Users','usersFromSfProcessed.csv')), mode='r') as accounts:
		accounts_reader = csv.DictReader(accounts)

		for account in accounts_reader:
			accounts_dict[str(int(float(account['MIGRATION_ID__C'])))] = account['ID']

	errors = dict(Wines=dict(),Cells=dict(),Accounts=dict())

	with open(os.path.join(os.path.dirname(__file__), 'products_delta.csv'), mode='r', encoding='utf-8') as products:
		reader = csv.DictReader(products, delimiter='\t')
		fields = set(reader.fieldnames)
		fields.update(['SFWarehouseId', 'SFWarehouseCellId', 'SFMainPhotoId', 'SFAccountId', 'SFWineId', 'SFProducerId', 'RecordTypeId'])

		with open(os.path.join(os.path.dirname(__file__), 'productswithdependencies.csv'), mode='w', encoding='utf-8') as product_with_deps:
			writer = csv.DictWriter(product_with_deps, list(fields))

			writer.writeheader()

			counter = 0

			for bottle in reader:
				# copy initial bottle details
				new_bottle = dict(bottle.items())
				new_bottle['Year'] = new_bottle['Year'] if new_bottle['Year'] or new_bottle['Year'] != '' else 9999
				new_bottle['Status'] = new_bottle['Status'] if bottle['Status'] != 'Incoming' else 'Handed Out'

				wine = wine_id_to_wine_object_dict.get(bottle['WineId'], None)

				# obtaining wine and producer details
				if not wine:
					errors['Wines'][bottle["WineId"]] = bottle["Id"]
					# print(f'ALERT!!! WINE: {bottle["Id"]}, wineId: {bottle["WineId"]}')
				else:
					new_bottle['SFWineId'] = wine['ID']
					new_bottle['SFProducerId'] = wine['PRODUCER__C']

				# obtainig cellar location details
				# cell_name = bottle['WarehouseCellLocationName']
				
				# if bottle['Status'] == 'Warehoused' and cell_name:
				# 	cell = cells_dict.get(cell_name, None)

				# 	if not cell:
				# 		errors['Cells'][cell_name] = (bottle["Id"],bottle["Status"])
				# 		# print(f'ALERT!!! CELL: {bottle["Id"]}, cell: {cell_name}')
				# 	else:
				# 		new_bottle['SFWarehouseId'] = warehouse_id
				# 		new_bottle['SFWarehouseCellId'] = cell

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
		with open(os.path.join(os.path.dirname(__file__), f'{ek}_errors.txt'), mode='w') as err:
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


	with open(os.path.abspath(os.path.join('Photos','photoswithproductids.csv')), mode='w', encoding='utf-8') as product_to_photo:
		writer = csv.DictWriter(product_to_photo, ['ProductId', 'SFPhotoId'])

		writer.writeheader()

		for k, v in bottle_to_photo_dict.items():
			writer.writerow(dict(ProductId=k, SFPhotoId=v))


def fill_photos():
	wine_id_to_name_dict = get_wines()

	photos_dict = dict()
	
	with open(os.path.join(os.path.dirname(__file__), 'products_new_2 (2).csv'), mode='r', encoding='utf-8') as products:
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

	with open(os.path.abspath(os.path.join('Photos', 'photos_delta.csv')), mode='w', encoding='utf-8') as photos:
		photo_fields = ['Photo_Unique_Name__c', 'Link']

		writer = csv.DictWriter(photos, photo_fields)
		writer.writeheader()

		for k, v in photos_dict.items():
			writer.writerow(dict(Photo_Unique_Name__c=k, Link=v.pop()))

def process_insert_errors():
	with open(os.path.join(os.path.dirname(__file__), 'error031319085916067.csv'), mode='r', encoding='utf-8') as errors:
		errors_reader = csv.DictReader(errors)

		error_messages = set()

		for error in errors_reader:
			# if 'Warehouse cell should not be occupied' not in error['ERROR'] and 'Bottle Request Name' not in error['ERROR']:
			error_messages.add(error['ERROR'])

		for e in error_messages:
			print(e)

def count_warehoused_products():
	with open(os.path.join(os.path.dirname(__file__), 'products_new.csv'), mode='r', encoding='utf-8') as products:
		reader = csv.DictReader(products, delimiter='\t')

		counter = 0

		for product in reader:
			if 'Warehoused' in product['Status']:
				counter += 1

		print(counter)

def fill_products_with_cells():
	warehouse_id = None
	cells_dict = dict()

	with open(os.path.abspath(os.path.join('WineCellarLocations', 'cellswithids.csv')), mode='r', encoding='utf-8') as cells:
		cells_reader = csv.DictReader(cells)

		for cell in cells_reader:
			cells_dict[cell['NAME']] = cell['ID']
			if not warehouse_id:
				warehouse_id = cell['WAREHOUSE__C']

	migid_to_sfid = dict()

	with open(os.path.join(os.path.dirname(__file__), 'sfidtomigrationmapping.csv'), mode='r', encoding='utf-8') as ids:
		ids_reader = csv.DictReader(ids)

		for id in ids_reader:
			migid_to_sfid[id['MIGRATION_ID__C']] = id['ID']

	with open(os.path.join(os.path.dirname(__file__), 'products_new_2.csv'), mode='r', encoding='utf-8') as products:
		reader = csv.DictReader(products, delimiter='\t')

		with open(os.path.join(os.path.dirname(__file__), 'productswithcells.csv'), mode='w', encoding='utf-8') as product_with_deps:
			writer = csv.DictWriter(product_with_deps, ['Id', 'SFWarehouseId', 'SFWarehouseCellId'])

			writer.writeheader()

			counter = 0

			for bottle in reader:
				# copy initial bottle details
				new_bottle = dict()
	
				# obtainig cellar location details
				cell_name = bottle['WarehouseCellLocationName']
				
				if bottle['Status'] == 'Warehoused' and cell_name:
					cell = cells_dict.get(cell_name, None)

					if not cell:
						continue
					else:
						new_bottle['SFWarehouseId'] = warehouse_id
						new_bottle['SFWarehouseCellId'] = cell
						new_bottle['Id'] = migid_to_sfid[bottle['Id']]

						writer.writerow(new_bottle)
						counter += 1
						

			print(counter)

def count_products():
	with open(os.path.join(os.path.dirname(__file__), 'products_new_2 (2).csv'), mode='r') as products:

		reader = csv.DictReader(products, delimiter='\t')

		count_with_photo = 0
		count_without_photo = 0
		count_with_brackets = 0
		count_without_brackets = 0

		for product in reader:
			if product['PhotoLink']:
				count_with_photo += 1
				if product['BracketsWineName']:
					count_with_brackets += 1
				else:
					count_without_brackets += 1
			else:
				count_without_photo += 1

		print(f'count_with_photo: {count_with_photo}')
		print(f'count_without_photo: {count_without_photo}')
		print(f'count_with_brackets: {count_with_brackets}')
		print(f'count_without_brackets: {count_without_brackets}')

def match_products_to_photos():
	photos_dict = dict()
	with open(os.path.join('Photos', 'photoWithIds.csv'), mode='r') as photos:
		photo_reader = csv.DictReader(photos)

		for photo in photo_reader:
			# print(photo['PHOTO_UNIQUE_NAME__C'])
			photos_dict[photo['PHOTO_UNIQUE_NAME__C']] = photo
	
	with open(os.path.join(os.path.dirname(__file__), 'productsToUpdateWithPhotos.csv'), mode='r') as products:
		products_reader = csv.DictReader(products)

		with open(os.path.join(os.path.dirname(__file__), 'productsToUpdateWithPhotosLinks.csv'), mode='w') as products_to_update_with_photos:
			product_to_update_fields = list(products_reader.fieldnames)
			product_to_update_fields.append('MainPhoto')
			product_to_update_fields.append('MainPhotoLink')

			products_writer = csv.DictWriter(products_to_update_with_photos, product_to_update_fields)
			products_writer.writeheader()

			with open(os.path.join(os.path.dirname(__file__), 'productsToUpdateWithPhotosLinksWithBrackets.csv'), mode='w') as photos_with_brackets:
				products_with_brackets_writer = csv.DictWriter(photos_with_brackets, product_to_update_fields)
				products_with_brackets_writer.writeheader()

				count_with_photo = 0
				count_without_photo = 0
				count_with_brackets = 0
				count_without_brackets = 0

				for product in products_reader:
					product_unique_photo_name = product['PRODUCT_PHOTO_UNIQUE_NAME__C']
					photo = photos_dict.get(product_unique_photo_name, None)

					if not photo:
						count_without_photo += 1
						continue

					count_with_photo += 1

					new_product = dict(product)
					new_product['MainPhoto'] = photo['ID']
					new_product['MainPhotoLink'] = photo['LINK__C']
					
					if product['BRACKETS_WINE_NAME__C']:
						count_with_brackets += 1
						products_with_brackets_writer.writerow(new_product)
					else:
						products_writer.writerow(new_product)
						count_without_brackets += 1

				print(f'count_with_photo: {count_with_photo}')
				print(f'count_without_photo: {count_without_photo}')
				print(f'count_with_brackets: {count_with_brackets}')
				print(f'count_without_brackets: {count_without_brackets}')



def add_bracketes_to_products():
	products_to_update = dict()

	with open(os.path.join(os.path.dirname(__file__), 'productsToUpdateWithPhotos.csv'), mode='r') as products:
		products_reader = csv.DictReader(products)

		for product in products_reader:
			products_to_update[product['MIGRATION_ID__C']] = product


	with open(os.path.join(os.path.dirname(__file__), 'products_delta_brackets.csv'), mode='r') as brackets:
		reader = csv.DictReader(brackets, delimiter='\t')

		with open(os.path.join(os.path.dirname(__file__), 'products_to_update_delta_brackets.csv'), mode='w') as products_to_update_delta:
			writer = csv.DictWriter(products_to_update_delta, ['Id', 'MainPhoto', 'BracketsName'])
			writer.writeheader()

			for bracket in reader:
				product = products_to_update.get(str(bracket['Id']), None)

				if not product:
					print(bracket)
					continue

				new_row = dict(Id=product['ID'], MainPhoto=None, BracketsName=bracket['BracketsWineName'])
				writer.writerow(new_row)
	
	# with open(os.path.join(os.path.dirname(__file__), 'productsToUpdateWithPhotos.csv'), mode='r') as products:
	# 	products_reader = csv.DictReader(products)

	# 	with open(os.path.join(os.path.dirname(__file__), 'productsToUpdateWithPhotosLinks1.csv'), mode='w') as products_to_update_with_photos:
	# 		product_to_update_fields = list(products_reader.fieldnames)
	# 		product_to_update_fields.append('MainPhoto')
	# 		product_to_update_fields.append('MainPhotoLink')

	# 		products_writer = csv.DictWriter(products_to_update_with_photos, product_to_update_fields)
	# 		products_writer.writeheader()

	# 		with open(os.path.join(os.path.dirname(__file__), 'productsToUpdateWithPhotosLinksWithBrackets1.csv'), mode='w') as photos_with_brackets:
	# 			products_with_brackets_writer = csv.DictWriter(photos_with_brackets, product_to_update_fields)
	# 			products_with_brackets_writer.writeheader()

	# 			count_with_photo = 0
	# 			count_without_photo = 0
	# 			count_with_brackets = 0
	# 			count_without_brackets = 0

	# 			for product in products_reader:
	# 				photo = photos_dict.get(product['MIGRATION_ID__C'], None)

	# 				if not photo:
	# 					count_without_photo += 1
	# 					continue

	# 				count_with_photo += 1

	# 				new_product = dict(product)
	# 				new_product['MainPhoto'] = photo['ID']
	# 				new_product['MainPhotoLink'] = photo['LINK__C']
					
	# 				if product['BRACKETS_WINE_NAME__C']:
	# 					count_with_brackets += 1
	# 					products_with_brackets_writer.writerow(new_product)
	# 				else:
	# 					products_writer.writerow(new_product)
	# 					count_without_brackets += 1

	# 			print(f'count_with_photo: {count_with_photo}')
	# 			print(f'count_without_photo: {count_without_photo}')
	# 			print(f'count_with_brackets: {count_with_brackets}')
	# 			print(f'count_without_brackets: {count_without_brackets}')

			


if __name__ == '__main__':
	# fill_photos() # call first to generate s3 photo object then extract ids to insert that ids to the product
	# fill_products_with_sf_ids() # then call this one
	# process_insert_errors() # call after photo processing

	# count_warehoused_products()

	# fill_products_with_cells()
	# match_products_to_photos()
	# count_products()
	add_bracketes_to_products()
	