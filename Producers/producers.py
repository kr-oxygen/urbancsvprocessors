import os

with open(os.path.join(os.path.dirname(__file__), 'ProducersWithoutDublicatesFormatted.csv'), mode='r') as f:
	for line in f.readlines():
		if '\t' in line:
			print(line)