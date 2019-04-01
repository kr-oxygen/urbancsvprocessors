import os
import csv

def comparator():
	first_lines = set()
	second_lines = set()

	with open(os.path.join(os.path.dirname(__file__),'producers.csv'), mode='r') as first:
		for i in first.readlines():
			first_lines.add(i.split(',')[0])

	with open(os.path.join(os.path.dirname(__file__),'newProducers.csv'), mode='r') as second:
		for i in second.readlines():
			second_lines.add(i.split(',')[0])

	for l in list(second_lines - first_lines):
		print(l)

with open(os.path.join(os.path.dirname(__file__), 'producers.csv'), mode='r') as f:
	reader = csv.DictReader(f)

	prod_mag_map = dict()

	with open('/Users/roman/Downloads/producers_merged.csv', mode='r') as producers_with_magento_id:
		pwmir = csv.DictReader(producers_with_magento_id)

		for r in pwmir:
			prod_mag_map[r['Id']] = r['MagentoId']

	with open(os.path.join(os.path.dirname(__file__),'producersProcessed.csv'), mode='w') as producers:
		fields = reader.fieldnames[:]
		fields.append('MagentoId')
		writer = csv.DictWriter(producers, fields)
		
		writer.writeheader()

		for row in reader:
			processed_row = dict((k, v.replace('\t', '')) for k,v in row.items())
			try:
				processed_row['MagentoId'] = prod_mag_map[row['id']]
				writer.writerow(processed_row)
			except:
				print(row)
			
if __name__ == '__main__':
	comparator()