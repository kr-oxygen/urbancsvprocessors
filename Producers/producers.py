with open('/Users/roman/Downloads/UrbanMigration/Producers/ProducersWithoutDublicatesFormatted.csv', mode='r') as f:
	for line in f.readlines():
		if '\t' in line:
			print(line)