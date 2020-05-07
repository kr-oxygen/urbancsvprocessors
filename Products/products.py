import csv
import os
import re

bottle_record_type_id = '0121t0000005h6JAAQ'

def get_wines():
	wine_id_to_wine_object_dict = dict()

	with open(os.path.abspath(os.path.join('Wines', 'wineswithoutproducersFromSf.csv')), mode='r', encoding='utf-8') as wines:
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
	cells_dict = dict()

	with open(os.path.abspath(os.path.join('WineCellarLocations', 'cellswithids.csv')), mode='r', encoding='utf-8') as cells:
		cells_reader = csv.DictReader(cells)

		for cell in cells_reader:
			cells_dict[cell['NAME']] = cell['ID']
			if not warehouse_id:
				warehouse_id = cell['WAREHOUSE__C']
	
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

	with open(os.path.join(os.path.dirname(__file__), 'products_new_2 (2).csv'), mode='r', encoding='utf-8') as products:
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
					continue
				else:
					new_bottle['SFWineId'] = wine['ID']
					new_bottle['SFProducerId'] = wine['PRODUCER__C']

				# obtainig cellar location details
				cell_name = bottle['WarehouseCellLocationName']
				
				if bottle['Status'] == 'Warehoused' and cell_name:
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
				
				if counter == 3000:
					break

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

def match_products_with_photo():
	ids_map = dict()

	with open(os.path.join(os.path.dirname(__file__), 'products_delta_brackets.csv'), mode='r') as items:
		reader = csv.DictReader(items, delimiter='\t')

		for item in reader:
			ids_map[item['Id']] = item

	with open(os.path.join(os.path.dirname(__file__), 'magnumAndHalfWithCorrectYear.csv'), mode='r') as items:
		reader = csv.DictReader(items)

		counter = 0
		counter_with_photo = 0

		item_to_photo_map = dict()
		item_with_photo_map = dict()
		items_without_photo = list()

		for item in reader:
			id_photo = ids_map.get(item['MIGRATION_ID__C'], None)

			counter += 1

			if not id_photo:
				items_without_photo.append(item)
			else:
				counter_with_photo += 1
				photos = item_to_photo_map.get(item['PRODUCT_PHOTO_UNIQUE_NAME__C'], None)
				if not photos:
					item_to_photo_map[item['PRODUCT_PHOTO_UNIQUE_NAME__C']] = set()
				
				item_to_photo_map[item['PRODUCT_PHOTO_UNIQUE_NAME__C']].add(id_photo['PhotoLink'])
				
				items_with_photos = item_with_photo_map.get(item['PRODUCT_PHOTO_UNIQUE_NAME__C'], list())
				
				if len(items_with_photos) == 0:
					item_with_photo_map[item['PRODUCT_PHOTO_UNIQUE_NAME__C']] = items_with_photos

				items_with_photos.append(item)
				# item_with_photo_map[item['PRODUCT_PHOTO_UNIQUE_NAME__C']] = item

		for k, v in item_to_photo_map.items():
			if len(v) > 1:
				print(k)
				for photo in v:
					print(photo)

		without_photo_counter = 0
		with_photo_counter = 0

		for item in items_without_photo:
			items_with_photos = item_with_photo_map.get(item['PRODUCT_PHOTO_UNIQUE_NAME__C'], None)

			if items_with_photos:
				items_with_photos.append(item)
				with_photo_counter += 1
			else:
				without_photo_counter += 1

		print(f'counter: {counter}')
		print(f'counter_with_photo: {counter_with_photo}')
		print(f'len(item_with_photo_map): {len(item_with_photo_map)}')
		print(f'with_photo_counter: {with_photo_counter}')
		print(f'without_photo_counter: {without_photo_counter}')

		overall_counter = 0

		with open(os.path.join(os.path.dirname(__file__), 'magnumAndHalfWithCorrectYearPhotoMap.csv'), mode='w') as matched:
			writer_fields = list(reader.fieldnames)
			writer_fields.append('PhotoLink')
			writer = csv.DictWriter(matched, writer_fields)

			writer.writeheader()

			for k,v in item_with_photo_map.items():
				for item in v:
					new_row = dict(item)
					new_row['PhotoLink'] = list(item_to_photo_map[item['PRODUCT_PHOTO_UNIQUE_NAME__C']])[0]
					writer.writerow(new_row)

		# print(f'overall_counter: {overall_counter}')

def change_photo_unique_name_to_15_chars():
	pattern = '^([a-zA-Z0-9]{18})-([a-zA-Z0-9]{18})(-.+)$'

	with open(os.path.abspath(os.path.join('Photos', 'photosToUpdateProd.csv')), mode='r') as old_photos:
		with open(os.path.abspath(os.path.join('Photos', 'photosToUpdateProdChanged.csv')), mode='w') as new_photos:

			reader = csv.DictReader(old_photos)
			writer = csv.DictWriter(new_photos, reader.fieldnames)
			
			writer.writeheader()

			for photo in reader:
				m = re.search(pattern, photo['PHOTO_UNIQUE_NAME__C'])

				if m:
					new_name = f'{m.group(1)[:15]}-{m.group(2)[:15]}{m.group(3)}'
					new_photo = dict(photo)
					new_photo['PHOTO_UNIQUE_NAME__C'] = new_name
					writer.writerow(new_photo)

def compare_photo_and_products():
	photos = dict()

	with open(os.path.abspath(os.path.join('Photos', 'photosToUpdateProdChanged.csv')), mode='r') as new_photos:
		reader = csv.DictReader(new_photos)

		for photo in reader:
			photos[photo['ID']] = photo['PHOTO_UNIQUE_NAME__C']
	
	with open(os.path.abspath(os.path.join('Photos', 'productsWithPhotos.csv')), mode='r') as products:
		reader = csv.DictReader(products)

		for product in reader:
			photo = photos.get(product['MAIN_PHOTO__C'], None)
			if photo:
				if photos[product['MAIN_PHOTO__C']] != product['PRODUCT_PHOTO_UNIQUE_NAME__C']:
					print(f'{product["ID"]}, {photos[product["MAIN_PHOTO__C"]]}, {product["PRODUCT_PHOTO_UNIQUE_NAME__C"]}')

			else:
				print(product["PRODUCT_PHOTO_UNIQUE_NAME__C"])




def process_products_photos():
	products_with_photos = dict()

	with open(os.path.join(os.path.dirname(__file__), 'productsWithPhotosFromProd.csv'), mode='r') as products:
		reader = csv.DictReader(products)

		for product in reader:
			main_photo = product['MAIN_PHOTO__C']

			if main_photo:
				if not main_photo in products_with_photos:
					products_with_photos[main_photo] = dict()
				products_with_photos[main_photo][product['PRODUCT_PHOTO_UNIQUE_NAME__C']] = product

	wines_dict = dict()

	with open(os.path.abspath(os.path.join('Wines', 'winesWithProducersFromProd.csv')), mode='r') as wines:
		reader = csv.DictReader(wines)

		for wine in reader:
			key = f'{wine["NAME"]}+{wine["PRODUCER_NAME__C"]}'
			if key in wines_dict:
				print(f'{key} is there')
			else:
				wines_dict[key] = wine

	with open(os.path.abspath(os.path.join('Photos', 'photosFromProd.csv')), mode='r') as photos:
		with open(os.path.abspath(os.path.join('Photos', 'productsWithPhotosFromProdChangedPhotoName.csv')), mode='w') as photosChanged:
			reader = csv.DictReader(photos)
			writer = csv.DictWriter(photosChanged, reader.fieldnames)
			writer.writeheader()
			
			with open(os.path.join(os.path.dirname(__file__), 'photosWithoutProducts.csv'), mode='w') as errors:
				errors_writer = csv.DictWriter(errors, reader.fieldnames)
				errors_writer.writeheader()

				for photo in reader:
					photo_unique_name = photo['PHOTO_UNIQUE_NAME__C']
					photo_product_without_brackets = photo_unique_name.endswith('-1')

					products_dict = products_with_photos.get(photo['ID'], None)

					new_photo_name = None

					m = None
					if photo_product_without_brackets:
						m = re.search('(.+)-(.+)(-.+-.+-.+-.+-.+-.+)', photo_unique_name)
					else:
						m = re.search('(.+)-(.+)(-.+-.+-.+-.+-.+-.+-.+)', photo_unique_name)

					if not products_dict and m:
						key = f'{m.group(1)}+{m.group(2)}'
						wine = wines_dict.get(key, None)

						if wine:
							new_photo_name = f'{wine["ID"]}-{wine["PRODUCER__C"]}{m.group(3)}'
					elif m:
						product = list(products_dict.values())[0]
						new_photo_name = f'{product["WINE__C"]}-{product["PRODUCER__C"]}{m.group(3)}'

					if not new_photo_name:
						errors_writer.writerow(photo)
					else:
						new_photo = dict(photo)
						new_photo['PHOTO_UNIQUE_NAME__C'] = new_photo_name
						writer.writerow(new_photo)

	# for photoKey, productDict in products_with_photos.items():
	# 	if len(productDict) > 1:
	# 		for k, v in productDict.items():
	# 			print(v)

def process_photos_without_products():
	wines_dict = dict()

	with open(os.path.abspath(os.path.join('Wines', 'winesWithProducersFromProd.csv')), mode='r') as wines:
		reader = csv.DictReader(wines)

		for wine in reader:
			key = f'{wine["NAME"]}+{wine["PRODUCER_NAME__C"]}'
			if key in wines_dict:
				print(f'{key} is there')
			else:
				wines_dict[key] = wine

	with open(os.path.join(os.path.dirname(__file__), 'photosWithoutProducts.csv'), mode='r') as errors:
		reader = csv.DictReader(errors)

		for photo in reader:
			m = re.search('(.+)-(.+)-.+-.+-.+-.+-.+-.+', photo['PHOTO_UNIQUE_NAME__C'])
			key = f'{m.group(1)}+{m.group(2)}'
			wine = wines_dict.get(key, None)
			if not wine:
				print(photo['ID'])
			else:
				pass

def compare_sf_and_magento_products():
	sf_products = dict()

	with open('/Users/roman/Downloads/SoqlQueryResult.csv', mode='r') as sf:
		sf_reader = csv.DictReader(sf)

		for prod in sf_reader:
			sf_products[str(int(float(prod['Magento_Id__c'])))] = prod
	
	with open('/Users/roman/Downloads/products -bottles - box - 4328.csv', mode='r') as magento:
		reader = csv.DictReader(magento)
		
		with open('/Users/roman/Downloads/diff_user1.csv', mode='w') as diff:
			writer = csv.DictWriter(diff, ['sf_id','magento_id','sf_count', 'magento_count', 'status'])
			writer.writeheader()

			for prod in reader:
				sf_prod = sf_products.get(prod['product_id'], None)

				if not sf_prod:
					print(f'sf does not exist for the {prod}')
					continue

				if float(sf_prod['Bottles_Count__c']) != float(prod['bottles_count']) or sf_prod['Status__c'] != 'Warehoused':
					writer.writerow(dict(sf_id=sf_prod['Id'],magento_id=prod['product_id'],sf_count=sf_prod['Bottles_Count__c'], magento_count=prod['bottles_count'], status=sf_prod['Status__c']))
					print(f"{sf_prod['Id']}, {prod['product_id']}, {sf_prod['Bottles_Count__c']}, {prod['bottles_count']}, {sf_prod['Status__c']}")




if __name__ == '__main__':
	# fill_photos() # call first to generate s3 photo object then extract ids to insert that ids to the product
	# fill_products_with_sf_ids() # then call this one
	# process_insert_errors() # call after photo processing

	# count_warehoused_products()

	# fill_products_with_cells()
	# match_products_to_photos()
	# count_products()
	# add_bracketes_to_products()
	# match_products_with_photo()
	# process_products_photos()

	# process_photos_without_products()

	# change_photo_unique_name_to_15_chars()

	# compare_photo_and_products()

	compare_sf_and_magento_products()