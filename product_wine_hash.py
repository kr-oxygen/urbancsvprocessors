import csv
import os
from datetime import datetime
import functools

def main():
	# grouped = dict()

	hash_to_id = None
	old_hash_to_new = None
	responses_without_sf_id = dict()

	with open('/Users/roman/Downloads/wine_hash_with_ids.csv', mode='r') as file:
		reader = csv.DictReader(file)
		
		hash_to_id = {row['WINE_YEAR_HASH__C']:row['ID'] for row in reader}

	with open('/Users/roman/Downloads/magento_old_hash_to_new_sf_hash.csv', mode='r') as file:
		reader = csv.DictReader(file)
		
		old_hash_to_new = {row['magento_hash']:row['sf_hash'] for row in reader}
	
	with open('/Users/roman/Downloads/winesearcher_requests.csv', mode='r') as file:
		reader = csv.DictReader(file)
		
		with open('/Users/roman/Downloads/winesearcher_responses_to_import.csv', mode='w') as to_import:
			writter = csv.DictWriter(to_import, ['id','region','grape','average','min','max','score','created_at','response_code','currency'])

			writter.writeheader()

			for row in reader:
				old_hash = row['product_hash']

				new_hash = old_hash_to_new.get(old_hash, None)

				if not new_hash:
					if old_hash not in responses_without_sf_id:
						responses_without_sf_id[old_hash] = list()

					responses_without_sf_id[old_hash].append(old_hash)

					continue

				sf_id = hash_to_id.get(new_hash, None)

				if not sf_id:
					print(f'No sf_id for {old_hash}')
					continue

				date = datetime.fromtimestamp(int(row['created_at'])).strftime('%Y-%m-%dT%H:%M:%SZ')

				writter.writerow(
					dict(
						id=sf_id,
						region=row['region'],
						grape=row['grape'],
						average=row['price_average'],
						min=row['price_min'],
						max=row['price_max'],
						score=row['ws_score'],
						created_at=date,
						response_code=row['response_code'],
						currency=row['requested_currency']
						)
					)

		print(len(responses_without_sf_id))

		# {k:len(v)for k,v responses_without_sf_id.items()}

		print(functools.reduce(lambda x,y: x+len(y) if isinstance(x, int) else len(x)+len(y), responses_without_sf_id.values()))

	

	# with open('/Users/roman/Downloads/simple_products_hash.csv', mode='r') as magento:
	# 	reader = csv.DictReader(magento)

	# 	magento_dict = {row['sku']:row['hash'] for row in reader}

	# 	with open('/Users/roman/Downloads/products_with_wine_hashes.csv', mode='r') as sf:
	# 		r = csv.DictReader(sf)

	# 		sf_dict = {row['ID']:row['WINE_YEAR_HASH__C'] for row in r}

	# 		with open('/Users/roman/Downloads/magento_old_hash_to_new_sf_hash.csv', mode='w') as to_update:
	# 			writter = csv.DictWriter(f=to_update, fieldnames=['magento_hash', 'sf_hash'])
	# 			writter.writeheader()

	# 			processed_dict = dict()

	# 			for m_sku, m_hash in magento_dict.items():
	# 				sf_hash = sf_dict.get(m_sku, None)
	# 				if not sf_hash:
	# 					print(f'sf hash is not found for {m_sku}')
	# 				else:
	# 					processed_dict[m_hash]=sf_hash
				
	# 			for k,v in processed_dict.items():
	# 				writter.writerow(dict(magento_hash=k, sf_hash=v))

	# with open('/Users/roman/Downloads/wine_hashes.csv', mode='w') as hashes:
	# 	writter = csv.DictWriter(f=hashes, fieldnames=['WINE__C', 'YEAR__C', 'TYPE_OF_WINE_YEAR__C'])

	# 	writter.writeheader()

	# 	for row in grouped.values():
	# 		writter.writerow(dict(WINE__C=row['WINE__C'], YEAR__C=row['YEAR__C'], TYPE_OF_WINE_YEAR__C=row['TYPE_OF_WINE_YEAR__C']))


if __name__ == '__main__':
	strArr = ["1, 3, 4, 7, 13", "1, 2, 4, 13, 15"]

	firstRange = set([int(x) for x in strArr[0].split(',')])
	secondRange = set([int(x) for x in strArr[-1].split(',')])

	res = [str(i) for i in sorted(firstRange.intersection(secondRange))]

	print(res)

	print(','.join(res) if len(res) > 0 else 'false')
	
