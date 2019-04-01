import os
import csv

with open(os.path.join(os.path.dirname(__file__), 'products_new.csv'), mode='r', encoding='utf-8') as products:
		reader = csv.DictReader(products, delimiter='\t')
		fields = set(reader.fieldnames)
		fields.update(['SFWarehouseId', 'SFWarehouseCellId', 'SFMainPhotoId', 'SFAccountId', 'SFWineId', 'SFProducerId', 'RecordTypeId'])

		with open(os.path.join(os.path.dirname(__file__), 'productswithdependencies.csv'), mode='w', encoding='utf-8') as product_with_deps:
			writer = csv.DictWriter(product_with_deps, list(fields), delimiter='\t')

			writer.writeheader()

			counter = 0

			for bottle in reader:
				# copy initial bottle details
				new_bottle = dict(bottle.items())
				if not new_bottle['Year']:
					new_bottle['Year'] = new_bottle['Year'] if new_bottle['Year'] or new_bottle['Year'] != '' else 9999
					print(new_bottle)
					break