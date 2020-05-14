import csv
import math
import os
import datetime
from dateutil import tz
from dateutil.parser import parse
import pytz
import json


class ProductToMigrate(object):
	def __init__(self, product=None, c=None):
		self.id = product['Id'] if product else c['id']
		self.created_date = product['CreatedDate'] if product else None
		self.current_status = product['Status__c'] if product else None
		self.migration = product['Migration_Id__c'] if product else None
		self.incoming = None if not c else c['incoming']
		self.warehoused = None if not c else c['warehoused']
		self.external = None if not c else c['external']
		self.deleted = None if not c else c['deleted']
		self.hand_out = None if not c else c['handout']

	def set_incoming(self, date):
		self.incoming = date

	def set_warehoused(self, date):
		self.warehoused = date
		
	def set_external(self, date):
		self.external = date

	def set_deleted(self, date):
		self.deleted = date
	
	def set_hand_out(self, date):
		self.hand_out = date

	def get_warehoused(self):
		if self.warehoused:
			return self.warehoused
		
		if self.migration:
			if self.hand_out or self.current_status == 'Warehoused':
				return self.created_date
		
		return ''

	def get_hand_out(self):
		if self.hand_out:
			return self.hand_out

		if self.migration and self.current_status == 'Handed out':
			return self.created_date

		return ''

	def get_external(self):
		if self.external:
			return self.external

		if self.deleted or self.current_status == 'External':
			return self.created_date
		
		return ''

	def get_dict(self):
		# ['id', 'incoming', 'warehosed', 'external', 'deleted', 'handout', 'created', 'migration', 'status']
		return dict(
			id=self.id,
			incoming=self.incoming if self.incoming else '',
			warehoused=self.get_warehoused(),
			external=self.get_external(),
			deleted=self.deleted if self.deleted else '',
			handout=self.get_hand_out(),
			created=self.created_date,
			migration=self.migration if self.migration else '',
			status=self.current_status)

	def __str__(self):
		return json.dumps(self.get_dict(), skipkeys=True)

	not_equal = list()

	def compare(self, other):
		if self.incoming != other.incoming or self.warehoused != other.warehoused or self.external != other.external or self.deleted != other.deleted or self.hand_out != other.hand_out:
			print(f'{self}\n{other}')
			print('---------------------------------------------------------------------------------------------------')
			ProductToMigrate.not_equal.append(self)



def migrate_product_status_changes():
	products_map = dict()

	with open(os.path.join(os.path.dirname(__file__), 'products_to_migrate') + '.csv', mode='r') as file:
		raw = csv.DictReader(file)

		for row in raw:
			products_map[row['Id']] = ProductToMigrate(row)

	with open(os.path.join(os.path.dirname(__file__), 'products_hist') + '.csv', mode='r') as file:
		raw = csv.DictReader(file)

		for row in raw:
			id = row['ParentId']
			status = row['NewValue']
			date = row['CreatedDate']

			product = products_map.get(id, None)

			if product:
				if status == 'Incoming':
					product.set_incoming(date)
				elif status == 'Warehoused':
					product.set_warehoused(date)
				elif status == 'External':
					product.set_external(date)
				elif status == 'Deleted':
					product.set_deleted(date)
				elif status == 'Handed out':
					product.set_hand_out(date)

	with open(os.path.join(os.path.dirname(__file__), 'products_migrated_status1') + '.csv', mode='w') as file:
		writer = csv.DictWriter(file,
			[
				'id', 
				'incoming', 
				'warehoused', 
				'external', 
				'deleted', 
				'handout', 
				'created', 
				'migration', 
				'status'
			]
		)

		writer.writeheader()

		for product in products_map.values():
			writer.writerow(product.get_dict())


def compare_migrated_histories():
	old_map = dict()

	with open(os.path.join(os.path.dirname(__file__), 'products_migrated_status') + '.csv', mode='r') as file:
		raw = csv.DictReader(file)
		for row in raw:
			old_map[row['id']] = ProductToMigrate(None,row)

	with open(os.path.join(os.path.dirname(__file__), 'products_migrated_status1') + '.csv', mode='r') as file:
		raw = csv.DictReader(file)
		for row in raw:
			new = ProductToMigrate(None,row)
			old = old_map.get(new.id, None)

			if old:
				new.compare(old)

	print(len(ProductToMigrate.not_equal))
	print(','.join(map(lambda x: f"'{x.id}'", ProductToMigrate.not_equal)))



def to_datetime(str_value):
	if not str_value:
		return None

	sf = parse(str_value)
	sf_repl = sf.replace(tzinfo=pytz.UTC)
	local = sf_repl.astimezone(tz.tzlocal())

	return local


def to_date(str_value):
	if not str_value:
		return None

	sf = parse(str_value)
	sf_repl = sf.replace(tzinfo=pytz.UTC)
	local = sf_repl.astimezone(tz.tzlocal())

	return local.date()
	#
	# dt = datetime.datetime.strptime(str_value[:-5], '%Y-%m-%dT%H:%M:%S.%f')
	#
	# return dt.date()


def round_price(price):
	price = round(price, 2) # (math.ceil(price*100))/100

	return price if isinstance(price, float) and not price.is_integer() else int(price)


class ProductStatus(object):
	absent = None
	incoming = 'Incoming'
	warehoused = 'Warehoused'
	external = 'External'
	deleted = 'Deleted'
	hand_out = 'Handed out'


class TestProduct(object):
	def __init__(self, warehoused=None, external=None, deleted=None, hand_out=None):
		self.warehoused = warehoused
		self.external = external
		self.deleted = deleted
		self.hand_out = hand_out


# class TestOrder(object):
# 	def __init__(self, date):
# 		self.date = date
# 		self.buyer = f'{date} buyer'
# 		self.seller = f'{date} seller'


class Order(object):
	def __init__(self, csv=None, test=None):
		self.id= csv['Id'] if csv else None
		self.product = csv['Product__c'] if csv else None
		self.hash = csv['Product__r.Product_Wine_Hash__c'] if csv else None
		self.date = to_date(csv['Order_Date__c'])  if csv else test.date
		self.buyer = csv['Order__r.Account__c'] if csv else test.buyer
		self.seller = csv['Seller__c']  if csv else test.seller


class StatusDate(object):
	def __init__(self, status, datetime):
		self.status = status
		self.datetime = datetime
		self.date = datetime.date()


class Product(object):
	products_with_final_account_does_not_match_last_buyer = set()

	def __init__(self, csv=None, test=None):
		self.id = csv['Id'] if csv else None
		self.hash_id = csv['Product_Wine_Hash__c'] if csv else None
		size = csv['Bottle_Content_Size__c'].split(' ')[0] if csv else None
		self.bottle_content_size = int(size) if size and size != 'Odd' else 0
		self.bottles_count = int(csv['Bottles_Count__c']) if csv else None
		self.final_account = csv['Account__c'] if csv else None
		self.final_status = csv['Status__c'] if csv else None
		self.final_price = csv['Actual_Price__c'] if csv else None
		self.created_date = to_datetime(csv['CreatedDate']) if csv else None
		self.incoming = to_datetime(csv['Income_Date__c']) if csv else None
		self.warehoused = to_datetime(csv['Warehoused_Date__c']) if csv else test.warehoused
		self.external = to_datetime(csv['External_Date__c']) if csv else test.external
		self.deleted = to_datetime(csv['Deleted_Date__c']) if csv else test.deleted
		self.hand_out = to_datetime(csv['Hand_Out_Date__c']) if csv else test.hand_out
		self.orders = list()
		self.status_points = self._get_time_points()
		self.points_set = set(map(lambda x: x.date, self.status_points))
		self.hash = None
		# self.all_points_set = set(self.points_set)

	def add_hash(self, hash):
		self.hash = hash

	def add_order_info(self, order):
		self.orders.append(order)
		# self.points_set.add(order.date)

	def get_account_at_time_point(self, point):
		if not hasattr(self, 'sorted'):
			self.sorted = True
			self.orders.sort(key=lambda i: i.date)

		if len(self.orders) == 0 or point >= self.orders[-1].date:
			if len(self.orders) > 0 and self.orders[-1].buyer != self.final_account:
				# print(f'ALERT: final account {self.final_account} does not mach last order buyer {self.orders[-1].buyer}')
				Product.products_with_final_account_does_not_match_last_buyer.add(self)

			return self.final_account

		if point < self.orders[0].date:
			return self.orders[0].seller

		return next(iter([order.buyer for order in reversed(self.orders) if order.date <= point]))

	def get_status_at_time_point(self, point):
		# if not self.warehoused and not self.external:
		# 	if self.deleted:
		# 		return ProductStatus.deleted
		#
		# 	return ProductStatus.hand_out
		#
		# if self.warehoused:
		# 	if point < self.warehoused:
		# 		return ProductStatus.absent
		# 	if self.hand_out:
		# 		if point >= self.hand_out:
		# 			return ProductStatus.hand_out
		#
		# 	return ProductStatus.warehoused
		#
		# if self.external:
		# 	if point < self.external:
		# 		return ProductStatus.absent
		# 	if self.deleted:
		# 		if point >= self.deleted:
		# 			return ProductStatus.deleted
		#
		# 	return ProductStatus.external
		#
		# return ProductStatus.absent
		if len(self.status_points) == 0 or point < self.status_points[0].date:
			return ProductStatus.absent

		if point >= self.status_points[-1].date:
			return self.status_points[-1].status

		return next(iter([item.status for item in reversed(self.status_points) if item.date <= point]))

	def get_price_at_time_point(self, point):
		if not self.hash:
			return 0

		hash_price = self.hash.get_price_at_time_point(point)

		price = (hash_price / (750 / self.bottle_content_size)) * self.bottles_count
		price = round_price(price)

		return price

	def _get_time_points(self):
		points_map = dict()

		if self.warehoused:
			Product._add_to_points_map(points_map, StatusDate(ProductStatus.warehoused, self.warehoused))
		
		if self.hand_out:
			Product._add_to_points_map(points_map, StatusDate(ProductStatus.hand_out, self.hand_out))
		
		if self.external:
			Product._add_to_points_map(points_map, StatusDate(ProductStatus.external, self.external))
		
		if self.deleted:
			Product._add_to_points_map(points_map, StatusDate(ProductStatus.deleted, self.deleted))

		if self.incoming:
			Product._add_to_points_map(points_map, StatusDate(ProductStatus.incoming, self.incoming))

		return sorted(points_map.values(), key=lambda x: x.date)

	@staticmethod
	def _add_to_points_map(points_map, value):
		item = points_map.get(value.date, None)

		if not item or value.datetime > item.datetime:
			points_map[value.date] = value


class WinesearcherResponse(object):
	def __init__(self, item):
		self.id = item['Id']
		self.date = to_date(item['CreatedDate'])
		self.price = float(item['Price_Average__c'])

	def __str__(self):
		return f'{self.date}: {self.price}'


class ProductWineHashHistory(object):
	def __init__(self, item):
		self.hash = item['Product_Wine_Hash__c']
		self.current = None
		self.history = list()
		self.products = list()
		self.dates_set = set()

	def add_value(self, item):
		wr = WinesearcherResponse(item)

		if wr.price > 0 and (not self.current or self.current.price != wr.price):
			self.history.append(wr)
			self.current = wr

		self.dates_set.add(wr.date)

	def add_product(self, product):
		self.products.append(product)

	def get_price_at_time_point(self, point):
		if not hasattr(self, 'sorted'):
			self.sorted = True
			self.history.sort(key=lambda i: i.date)

		if len(self.history) == 0:
			return 0
		
		if point <= self.history[0].date:
			return self.history[0].price

		if point >= self.history[-1].date:
			return self.history[-1].price
		
		return next(iter([item.price for item in reversed(self.history) if item.date <= point]))

	def __str__(self):
		str = f'{self.hash}\n'

		for item in self.history:
			str += f'{item}\n'

		return str


class CollectionValue(object):
	props = ['account', 'date', 'bottles', 'external_bottles', 'value', 'external_value']

	def __init__(self, account, date):
		self.account = account
		self.date = date
		self.bottles = 0
		self.external_bottles = 0
		self.value = 0
		self.external_value = 0

	def add_product(self, product, status):
		if status == ProductStatus.warehoused:
			self.bottles += product.bottles_count
			self.value += product.get_price_at_time_point(self.date)

			return
		
		if status == ProductStatus.external:
			self.external_bottles += product.bottles_count
			self.external_value += product.get_price_at_time_point(self.date)

	def get_dict(self):
		return dict(
			account=self.account,
			date=self.date,
			bottles=self.bottles,
			external_bottles=self.external_bottles,
			value=round_price(self.value),
			external_value=round_price(self.external_value)
		)


class Account(object):
	def __init__(self, id):
		self.id = id
		self.collection_values = list()

	def add_collection_value(self, collection_value):
		self.collection_values.append(collection_value)


def get_hash_changes_map():
	hash_changes_map = dict()

	with open(os.path.join(os.path.dirname(__file__), 'winesearcher') + '.csv', mode='r') as file:
		raw = csv.DictReader(file)

		for row in raw:
			id = row['Product_Wine_Hash__c']

			hash_changes = hash_changes_map.get(id, ProductWineHashHistory(row))
			hash_changes.add_value(row)

			hash_changes_map[id] = hash_changes

	return hash_changes_map


def get_products_map(hash_changes_map):
	products_map = dict()

	with open(os.path.join(os.path.dirname(__file__), 'products') + '.csv', mode='r') as file:
		raw = csv.DictReader(file)
		no_match_count = 0

		for row in raw:
			id = row['Id']
			product = Product(row)
			products_map[id] = product

			hash = hash_changes_map.get(product.hash_id, None)


			if not hash:
				# print(f'ALARM: hash is not found for Product: {product.id}')
				no_match_count += 1
			else:
				hash.add_product(product)
				hash_changes_map[product] = hash
				product.add_hash(hash)

		print(f'There are no hash matches for products, count: {no_match_count}')

	return products_map


def fill_products_with_orders(products_map):
	order_dates_map = dict()

	with open(os.path.join(os.path.dirname(__file__), 'orders') + '.csv', mode='r') as file:
		raw = csv.DictReader(file)

		for row in raw:
			order = Order(row)
			
			product = products_map.get(order.product, None)

			if not product:
				print(f'ALARM: product is not found for Order: {order.date}')
			else:
				product.add_order_info(order)
			
			dates = order_dates_map.get(order.date, list())
			dates.append(order)
			order_dates_map[order.date] = dates

	return order_dates_map


class BuiltCollectionValueDataHolder(object):
	def __init__(self):
		self.hash_changes_map = None
		self.products_map = None
		self.order_dates_map = None
		self.collection_values = list()
		self.dates_set = set()
		self.dates_product_map = dict()


# 1) group winesearcher responses by hash
# 2) get all products 
# 3) fill products with orders
# 4) generate set of all dates in changes from winesearcher response dates + order dates + product change dates
# 5) sort dates descending - probably is not necessary
# 6) move through dates 
# 7) get all product wine hashes chaged this date 
# 		plus products changed this date 
# 		plus orders made this date

# 8) get products for this hashes 
# 9) get accounts from products on this date
# 10) get changed products this date
# 11) get accounts for them
def build_collection_value():
	holder = BuiltCollectionValueDataHolder()
	holder.hash_changes_map = get_hash_changes_map()
	holder.products_map = get_products_map(holder.hash_changes_map)
	holder.order_dates_map = fill_products_with_orders(holder.products_map)
	holder.collection_values = list()
	holder.dates_set = set()
	holder.dates_product_map = dict()

	for hash in holder.hash_changes_map.values():
		holder.dates_set.update(hash.dates_set)

	holder.dates_set.update([order_date for order_date in holder.order_dates_map.keys()])

	for product in holder.products_map.values():
		for point in product.points_set:
			products = holder.dates_product_map.get(point, list())
			products.append(product)
			holder.dates_product_map[point] = products

		holder.dates_set.update(product.points_set)

	return holder


def test_built_collection(product, date):
	holder = build_collection_value()

	if date in holder.dates_set:
		print('Date in set')
	else:
		print('Date not in set')

	product = holder.products_map[product]
	account_at_time = product.get_account_at_time_point(date)

	print(f'Account at time: {account_at_time}')

	print(f'Price at time: {product.get_price_at_time_point(date)}')


def test_get_products_by_account_for_day(account, date):
	holder = build_collection_value()

	with open(os.path.join(os.path.dirname(__file__), f'products_for_account') + '.csv', mode='w') as file:
		writer = csv.DictWriter(file, ['id', 'count', 'price', 'status'])
		writer.writeheader()

		for product in holder.products_map.values():
			if account == product.get_account_at_time_point(date):
				writer.writerow(dict(
					id=product.id,
					count=product.bottles_count,
					price=product.get_price_at_time_point(date),
					status=product.get_status_at_time_point(date)
				))


def damp_collection_value_history():
	holder = build_collection_value()
	for date in holder.dates_set:
		accounts = set()

		# find changed account in the winesearcher hashes
		for hash in holder.hash_changes_map.values():
			if date in hash.dates_set:
				accounts.update([
					product.get_account_at_time_point(date)
					for product in hash.products
				])

		orders = holder.order_dates_map.get(date, None)

		# find changed accounts in orders, there are both: buyer and seller
		if orders:
			accounts.update([
				acc for order in orders
					for acc in [
						order.buyer,
						order.seller
					]
			])

		# find changed accounts in products that changed this date
		products = holder.dates_product_map.get(date, None)

		if products:
			accounts.update([product.get_account_at_time_point(date) for product in products])

		accounts_collection_value_map = dict()

		for acc in accounts:
			cv = CollectionValue(acc, date)

			accounts_collection_value_map[acc] = cv

			holder.collection_values.append(cv)

		if len(accounts) == 0:
			continue

		# go through all products and if product account at the date is in the accounts set calculate its collection value
		for product in holder.products_map.values():
			status = product.get_status_at_time_point(date)
			if status == ProductStatus.warehoused or status == ProductStatus.external:
				collection_value = accounts_collection_value_map.get(product.get_account_at_time_point(date), None)

				if collection_value:
					collection_value.add_product(product, status)

	print(f'Dates len: {len(holder.dates_set)}')
	print(f'Product.accounts_no_last_buyer_count: {len(Product.products_with_final_account_does_not_match_last_buyer)}')

	for product in Product.products_with_final_account_does_not_match_last_buyer:
		print(f'Product: {product.id}, '
			f'account: {product.final_account}, '
			f'order date: {product.orders[-1].date}, '
			f'order buyer: {product.orders[-1].buyer}')

	with open(os.path.join(os.path.dirname(__file__), 'collection_value') + '.csv', mode='w') as file:
		writer = csv.DictWriter(file, CollectionValue.props)

		writer.writeheader()

		for cv in holder.collection_values:
			writer.writerow(cv.get_dict())


def test_collection_value():
	local_map = dict()
	no_keys = list()
	not_equal = dict()
	equal = list()

	with open(os.path.join(os.path.dirname(__file__), 'collection_value') + '.csv', mode='r') as file:
		raw = csv.DictReader(file)

		for row in raw:
			local_map[(row['account'], row['date'])] = row

	with open(os.path.join(os.path.dirname(__file__), 'collection_value_prod') + '.csv', mode='r') as file:
		raw = csv.DictReader(file)

		for row in raw:
			key = (row['Account__c'], row['Changed_Date__c'])

			local = local_map.get(key, None)

			if not local:
				print(f'local is not set for prod: {key}')
				no_keys.append(key)
				continue

			if row['Bottles_Count__c'] != local['bottles'] \
				or row['External_Bottles_Count__c'] != local['external_bottles'] \
				or int(float(row['External_Value__c'])) != int(float(local['external_value'])) \
				or int(float(row['Value__c'])) != int(float(local['value'])):
				# print(f'local is not equal to prod: {local}\n{row}')
				item = not_equal.get(row['Account__c'], list())
				item.append((row, local))
				not_equal[row['Account__c']] = item
			else:
				equal.append((row, local))

	print(f'no keys: {len(no_keys)}')
	print(f'not equal: {len(not_equal)}')
	print(f'both: {len(not_equal)+len(no_keys)}')
	print(f'equal: {len(equal)}')

	for k,v in not_equal.items():
		print(f'Not Equal For Account: {k}')
		for i in v:
			print_prod_and_local(i[0], i[1])
		print('=================================================================')

	print(sum([len(value) for value in not_equal.values()]))


def print_prod_and_local(prod, local):
	print(f'pr --> d:{prod["Changed_Date__c"]}, b:{prod["Bottles_Count__c"]}, v:{prod["Value__c"]}, eb:{prod["External_Bottles_Count__c"]}, ev:{prod["External_Value__c"]}')
	print(f'lo --> d:{local["date"]}, b:{local["bottles"]}, v:{local["value"]}, eb:{local["external_bottles"]}, ev:{local["external_value"]}')
	print('----------------------------------------------------------------')


def test_product_hash_history(hash_changes_map):
	m = max(hash_changes_map.values(), key=lambda item: len(item.history))
	print(m)
	print('seek')
	d1 = datetime.datetime(2019, 6, 1).date()
	print(f'd1 {d1} -- {m.get_price_at_time_point(d1)}')
	d2 = datetime.datetime(2019, 11, 20).date()
	print(f'd2 {d2} -- {m.get_price_at_time_point(d2)}')
	d3 = datetime.datetime(2019, 12, 14).date()
	print(f'd3 {d3} -- {m.get_price_at_time_point(d3)}')
	d4 = datetime.datetime(2020, 6, 1).date()
	print(f'd4 {d4} -- {m.get_price_at_time_point(d4)}')


def test_find_item_at_time_point():
	dates = [
		datetime.datetime(2020, 5, 1).date(),
		datetime.datetime(2020, 5, 2).date(),
		datetime.datetime(2020, 5, 3).date(),
		datetime.datetime(2020, 5, 4).date(),
		datetime.datetime(2020, 5, 5).date(),
		datetime.datetime(2020, 5, 6).date(),
		# datetime.datetime(2020, 5, 7).date(),
		datetime.datetime(2020, 5, 8).date(),
		datetime.datetime(2020, 5, 9).date(),
		datetime.datetime(2020, 5, 10).date()
	]

	print(next(iter([d for d in reversed(dates) if d <= datetime.datetime(2020, 5, 7).date()])))


def test_product_status_at_time_point():
	date1 = datetime.datetime(2020, 5, 1).date()
	date2 = datetime.datetime(2020, 5, 2).date()
	point = datetime.datetime(2020, 4, 30).date()
	
	test = TestProduct(external=date1)

	product = Product(test=test)

	print(product.get_status_at_time_point(point))


def test_product_account_at_time_point():
	test = TestProduct()
	product = Product(test=test)

	product.add_order_info(Order(test=TestOrder(datetime.datetime(2020, 3, 1).date())))
	product.add_order_info(Order(test=TestOrder(datetime.datetime(2020, 6, 1).date())))
	product.add_order_info(Order(test=TestOrder(datetime.datetime(2020, 4, 1).date())))
	product.add_order_info(Order(test=TestOrder(datetime.datetime(2020, 9, 1).date())))
	product.add_order_info(Order(test=TestOrder(datetime.datetime(2020, 2, 1).date())))
	product.add_order_info(Order(test=TestOrder(datetime.datetime(2020, 1, 1).date())))
	product.add_order_info(Order(test=TestOrder(datetime.datetime(2020, 7, 1).date())))
	product.add_order_info(Order(test=TestOrder(datetime.datetime(2020, 8, 1).date())))
	product.add_order_info(Order(test=TestOrder(datetime.datetime(2020, 5, 1).date())))

	point = datetime.datetime(2020, 9, 1).date()

	print(product.get_account_at_time_point(point))


class TP(object):
	def __init__(self, prod=None, local=None):
		self.id = prod['Id'] if prod else local['id']
		count = prod['Bottles_Count__c'] if prod else local['count']
		self.count = int(count) if count else 0
		price = prod['Winesearcher_Price__c'] if prod else local['price']
		self.price = float(price) if price else 0
		self.status = prod['Status__c'] if prod else local['status']

	def compare(self, other):

		if self.count != other.count:
			print(f'{self.id} count diff: {self.count} -- {other.count}')
		if self.price != other.price and self.status != 'Handed out' and other.status != 'Handed out':
			print(f'{self.id} price diff: {self.price} -- {other.price}')
		if self.status != other.status:
			print(f'{self.id} status diff: {self.status} -- {other.status}')


def test_account_products():
	prod = '/Users/roman/Downloads/products_for_account_prod.csv'
	local = '/Users/roman/Programing/python/uwbcsv/collection_value/products_for_account.csv'
	prod_map = dict()
	local_map = dict()

	with open(prod, mode='r') as file:
		raw = csv.DictReader(file)

		for row in raw:
			prod_map[row['Id']] = TP(prod=row)

	with open(local, mode='r') as file:
		raw = csv.DictReader(file)

		for row in raw:
			local_map[row['id']] = TP(local=row)

	if len(prod_map) != len(local_map):
		print(f'len diff {len(prod_map)} -- {len(local_map)}')

	for l in local_map.values():
		p = prod_map[l.id]
		p.compare(l)


def get_product_price(product, date):
	holder = build_collection_value()
	p = holder.products_map[product]
	p.get_price_at_time_point(date)


def generate_product_wine_hash_actual_prices():
	hash_map = get_hash_changes_map()

	with open(os.path.join(os.path.dirname(__file__), 'pwh_generated') + '.csv', mode='w') as file:
		writer = csv.DictWriter(file, ['id', 'wsrid', 'date'])

		writer.writeheader()

		for hash in hash_map.values():
			if hash.current is None:
				print(hash)
			else:
				writer.writerow(dict(
				id=hash.hash,
				wsrid=hash.current.id,
				date=hash.current.date
			))


class ProductToChangeDates(object):
	def __init__(self, prod, local):
		self.id = prod['Id']
		self.prod = prod
		self.local = local

	def get_date(self, prod_field, local_field):
		prod = to_datetime(self.prod[prod_field])
		local = to_datetime(self.local[local_field])

		prod = prod if prod else ''
		local = local if local else ''

		if prod > local:
			return self.prod[prod_field]

		else:
			return self.local[local_field]

	def get_dict(self):
		return dict(
			id=self.id,
			incoming=self.get_date('Income_Date__c', 'incoming'),
			warehoused=self.get_date('Warehoused_Date__c', 'warehoused'),
			external=self.get_date('External_Date__c', 'external'),
			deleted=self.get_date('Deleted_Date__c', 'deleted'),
			handout=self.get_date('Hand_Out_Date__c', 'handout'),
		)


def change_product_dates():
	local_map = dict()
	products = list()

	with open(os.path.join(os.path.dirname(__file__), 'products_migrated_status1') + '.csv', mode='r') as file:
		raw = csv.DictReader(file)
		for row in raw:
			local_map[row['id']] = row

	with open(os.path.join(os.path.dirname(__file__), 'products_to_update_with_dates') + '.csv', mode='r') as file:
		raw = csv.DictReader(file)
		for row in raw:
			local = local_map[row['Id']]

			product = ProductToChangeDates(row, local)
			products.append(product)

	with open(os.path.join(os.path.dirname(__file__), 'products_to_update_with_dates_w') + '.csv', mode='w') as file:
		writer = csv.DictWriter(file, ['id', 'incoming', 'warehoused', 'handout', 'external', 'deleted'])
		writer.writeheader()

		for product in products:
			writer.writerow(product.get_dict())



if __name__ == "__main__":
	# damp_collection_value_history()
	# test_product_account_at_time_point()
	# test_collection_value()
	# test_built_collection('a0G1t000005xmrUEAQ', datetime.date(2020, 5, 14)) # Not Equal For Account: 0011t00000NS4ggAAD
	# test_get_products_by_account_for_day('0011t00000NS4foAAD', datetime.date(2020, 5, 14))
	test_account_products()
	# get_product_price('a0G2o00001SaI5lEAF', datetime.date(2020, 5, 13))
	# migrate_product_status_changes()
	# change_product_dates()
