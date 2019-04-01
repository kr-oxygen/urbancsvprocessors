import os
import csv

def comparator():
	first_lines = set()
	second_lines = set()

	with open(os.path.join(os.path.dirname(__file__),'photos.csv'), mode='r') as first:
		for i in first.readlines():
			first_lines.add(i.split(',')[0])

	with open(os.path.join(os.path.dirname(__file__),'photos_delta.csv'), mode='r') as second:
		for i in second.readlines():
			second_lines.add(i.split(',')[0])

	for l in second_lines:
		if l not in first_lines:
			print(l)

def update_name():
	with open(os.path.join(os.path.dirname(__file__),'photosIds.csv'), mode='r') as r:
		reader = csv.DictReader(r)

		with open(os.path.join(os.path.dirname(__file__),'photosIdsUpdated.csv'), mode='w') as w:
			writer = csv.DictWriter(w, reader.fieldnames)
			writer.writeheader()

			for line in reader:
				new_line = dict(line)
				unique_name = new_line['PHOTO_UNIQUE_NAME__C']
				new_line['PHOTO_UNIQUE_NAME__C'] = '{}9999-1'.format(unique_name) if unique_name.endswith('-') else '{}-1'.format(unique_name)
				writer.writerow(new_line)


if __name__ == '__main__':
	update_name()