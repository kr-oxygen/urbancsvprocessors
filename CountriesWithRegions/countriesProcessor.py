import csv
import re

class Country(object):
	def __init__(self, id, code):
		self.id = id
		self.code = code
		self.districts = []
		self.translations = []

	def __str__(self):
		return f'Id: {self.id}, Code: {self.code}'

class CountryTranslation(object):
	def __init__(self, id, code):
		self.country_id = id
		self.code = code

	def __str__(self):
		return f'CountryId: {self.country_id}, Code: {self.code}'

class District(object):
	
	def __init__(self, id, district_id, locale, name):
		self.id = id
		self.district_id = district_id
		self.locale = locale
		self.name = name

		parsed = self._split_name()

		self.code = parsed[0]
		self.parsed_name = parsed[1]


	def _split_name(self):
		m = re.search('(.+) - (.+)', self.name)
		code = m.group(1)
		name = m.group(2)

		return (code, name)

	def __str__(self):
	 return f'Id: {self.id}, DistrictId: {self.district_id}, Locale: {self.locale}, Name: {self.name}, Code: {self.code}, ParsedName: {self.parsed_name}'



def csv_parser(file):
	rows = []
	with open(file) as f:
		reader = csv.reader(f)

		for row in reader:
			rows.append(row)
	
	return rows

def main():
	countries = [Country(v[0], v[1]) for i,v in enumerate(csv_parser('Countries.csv')) if i > 0]
	country_translation = [CountryTranslation(v[0], v[1]) for i,v in enumerate(csv_parser('CountryTranslation.csv')) if i > 0]
	districts = [District(v[0], v[1], v[2], v[5]) for i,v in enumerate(csv_parser('DistrictTranslation.csv')) if i > 0]

	countries_dict = dict([(country.code, country) for country in countries])

	for district in districts:
		if district.code in countries_dict:
			countries_dict[district.code].districts.append(district)
		else:
			print(f'THERE IS NO COUNTRY FOR REGION: {district}')

	countries_dict = dict([(v.id, v) for v in countries_dict.values()])

	for ct in country_translation:
		if ct.country_id in countries_dict:
			countries_dict[ct.country_id].translations.append(ct)
		else:
			print(f'THERE IS NO COUNTRY FOR TRANSLATION: {ct}')
	
	s = set()

	for country in sorted(countries_dict.values(), key=lambda c: c.translations[0].code):
		
		if len(country.districts) > 0:
			for d in country.districts:
				if d.parsed_name in s:
					print(d.parsed_name)
				else:
					s.add(d.parsed_name)
				print('\t' + d.parsed_name)
		else:
			if country.translations[0].code in s:
				print(country.translations[0].code)
			else:
				s.add(country.translations[0].code)
			print(country.translations[0].code)

	# for country in countries_dict.values():
	# 	for translation in country.translations:
	# 		print(translation.code)
	# 	if len(country.districts) > 0:
	# 		for district in country.districts:
	# 			print('\t'+ district.parsed_name)
	# 	else:
	# 		print('\tThere is no regions for the country')

	# print(len(countries_dict.values()))


if __name__ == '__main__':
	main()