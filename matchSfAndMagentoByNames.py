import csv
import os
import json
from datetime import date

def main():
	from_magento = dict()

	with open('/Users/roman/Downloads/magentoWines.json', mode='r') as magento:
		data = json.load(magento)

		for d in data:
			value = int(d['value']) if d['value'] else 0
			from_magento[value] = d['label']

	with open('/Users/roman/Programing/sf/uwb_sfdx/wines.csv', mode='r') as sf:
		sf_reader = csv.DictReader(sf)

		not_in_magento = list()
		not_equal_name = list()

		for sf_item in sf_reader:
			if sf_item['Magento_Id__c']:
				magento = from_magento.get(int(sf_item['Magento_Id__c']), None)
				if not magento:
					print(f'Not found for id {sf_item}')
					continue
				if magento.strip() != sf_item['Name']:
					not_equal_name.append((sf_item, magento))
			else:
				not_in_magento.append(sf_item)

		grouped = dict()
		for item in not_equal_name:
			sf_name = item[0]["Name"].replace('"','""')
			mn = item[1].replace("\'", "\\'")
			magento_name = f'\'{mn}\''
			sf_id = f'\'{item[0]["Id"]}\''
			print(f'toUpdate.add(new Wine__c(Id = {sf_id}, Magento_Name__c = {magento_name}));')
		# 	sf_name = item[0]['Name']
		# 	if sf_name not in grouped.keys():
		# 		grouped[sf_name]=list()
		# 	grouped[sf_name].append(item[1])
		# 	if len(grouped[sf_name]) > 1:
		# 		# print(sf_name)
		# 		pass

		# for k,v in grouped.items():
		# 	print(f'{k},{",".join(set(v))}')

def to_bool(item):
		return item == 'true' or item == '1'

def check_status(sf, magento):
	return sf == magento or (sf == '' and magento == 'NULL')

def accs():
	magento_dict = dict()

	with open('/Users/roman/Downloads/Roma.csv', mode='r') as magento:
		reader = csv.DictReader(magento)

		for i in reader:
			key = i['entity_id']
			magento_dict[key] = i

	with open('/Users/roman/Programing/sf/uwb_sfdx/accounts.csv', mode='r') as sf:
		reader = csv.DictReader(sf)

		for item in reader:
			magento = magento_dict.get(item['Magento_Id__c'], None)
			
			if not magento:
				print(f'Not magento {item}')
				continue
			
			equals = to_bool(item['Locked__c']) == to_bool(magento['is_locked']) and \
				'2020-01-31' in magento['subscription_date'] and \
				check_status(item['Sensorist_Status__c'], magento['sensorist_status']) and \
				check_status(item['Subscription_Type__c'], magento['subscription_label']) and \
				to_bool(item['Want_To_Share_Sensorist_Data__c']) == to_bool(magento['wants_share_sensorist_data'])

			if not equals:
				print('-------------------------------------------------------')
				print(magento)
				print(item)

	

if __name__ == '__main__':
	main()