import os
import csv
import json


# def comparator():
# 	first_lines = set()
# 	second_lines = set()

# 	with open(os.path.join(os.path.dirname(__file__),'producers.csv'), mode='r') as first:
# 		for i in first.readlines():
# 			first_lines.add(i.split(',')[0])

# 	with open(os.path.join(os.path.dirname(__file__),'newProducers.csv'), mode='r') as second:
# 		for i in second.readlines():
# 			second_lines.add(i.split(',')[0])

# 	for l in list(second_lines - first_lines):
# 		print(l)

# with open(os.path.join(os.path.dirname(__file__), 'producers.csv'), mode='r') as f:
# 	reader = csv.DictReader(f)

# 	prod_mag_map = dict()

# 	with open('/Users/roman/Downloads/producers_merged.csv', mode='r') as producers_with_magento_id:
# 		pwmir = csv.DictReader(producers_with_magento_id)

# 		for r in pwmir:
# 			prod_mag_map[r['Id']] = r['MagentoId']

# 	with open(os.path.join(os.path.dirname(__file__),'producersProcessed.csv'), mode='w') as producers:
# 		fields = reader.fieldnames[:]
# 		fields.append('MagentoId')
# 		writer = csv.DictWriter(producers, fields)
		
# 		writer.writeheader()

# 		for row in reader:
# 			processed_row = dict((k, v.replace('\t', '')) for k,v in row.items())
# 			try:
# 				processed_row['MagentoId'] = prod_mag_map[row['id']]
# 				writer.writerow(processed_row)
# 			except:
# 				print(row)
			

def map_producers_with_magento_id():
	name_id_map = dict()

	with open(os.path.join(os.path.dirname(__file__),'producersMagentoIds.json'), mode='r', encoding='utf-8') as ids:
		data = json.load(ids)

		for item in data:
			name_id_map[item['label']] = item['value']

	with open(os.path.join(os.path.dirname(__file__),'newProducers.csv'), mode='r') as producers:
		reader = csv.DictReader(producers)

		with open(os.path.join(os.path.dirname(__file__),'newProducersWithMagentoIds.csv'), mode='w') as producersMapped:
			fields = list(reader.fieldnames)
			fields.append('MagentoId')

			writer = csv.DictWriter(producersMapped, fields)
			writer.writeheader()

			for producer in reader:
				new_row = dict(dict((k, v.replace('\t', '')) for k,v in producer.items()))
				
				magento_id = name_id_map.get(producer['producer'], None)

				if not magento_id:
					print(producer['producer'])
				else:
					new_row['MagentoId'] = magento_id
					writer.writerow(new_row)



if __name__ == '__main__':
	map_producers_with_magento_id()