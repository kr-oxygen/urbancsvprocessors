import csv
import os
import datetime

class ProductToMigrate(object):
	def __init__(self, product):
		self.id = product['Id']
		self.created_date = product['CreatedDate']
		self.current_status = product['Status__c']
		self.migration = product['Migration_Id__c']
		self.incoming = None
		self.warehoused = None
		self.external = None
		self.deleted = None
		self.hand_out = None

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

def migrate_product_status_changes():
	products_map = dict()

	with open(os.path.join(os.path.dirname(__file__), 'products') + '.csv', mode='r') as file:
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

	with open(os.path.join(os.path.dirname(__file__), 'products_migrated_status') + '.csv', mode='w') as file:
		writter = csv.DictWriter(file, 
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

		writter.writeheader()

		for product in products_map.values():
			writter.writerow(product.get_dict())

def to_date(str_value):
	if not str_value:
		return None

	dt = datetime.datetime.strptime(str_value[:-5], '%Y-%m-%dT%H:%M:%S.%f')

	return dt.date()


class ProductStatus(object):
	absent = None
	warehoused = 'Warehoused'
	external = 'External'
	deleted = 'Deleted'
	hand_out = 'Handed out'


class TestProduct(object):
	def __init__(self, warehosed=None, external=None, deleted=None, hand_out=None):
		self.warehoused = warehosed
		self.external = external
		self.deleted = deleted
		self.hand_out = hand_out


class TestOrder(object):
	def __init__(self, date):
		self.date = date
		self.buyer = f'{date} buyer'
		self.seller = f'{date} seller'


class Order(object):
	def __init__(self, csv=None, test=None):
		self.product = csv['Product__c'] if csv else None
		self.hash = csv['Product__r.Product_Wine_Hash__c'] if csv else None
		self.date = to_date(csv['Order_Date__c'])  if csv else test.date
		self.buyer = csv['Order__r.Account__c'] if csv else test.buyer
		self.seller = csv['Seller__c']  if csv else test.seller


class Product(object):
	def __init__(self, csv=None, test=None):
		self.id = csv['Id'] if csv else None
		self.hash = csv['Product_Wine_Hash__c'] if csv else None
		self.bottle_content_size = csv['Bottle_Content_Size__c'] if csv else None
		self.bottles_count = csv['Bottles_Count__c'] if csv else None
		self.final_account = csv['Account__c'] if csv else None
		self.final_status = csv['Status__c'] if csv else None
		self.final_price = csv['Actual_Price__c'] if csv else None
		self.created_date = to_date(csv['CreatedDate']) if csv else None
		self.warehoused = to_date(csv['Warehoused_Date__c']) if csv else test.warehoused
		self.external = to_date(csv['External_Date__c']) if csv else test.external
		self.deleted = to_date(csv['Deleted_Date__c']) if csv else test.deleted
		self.hand_out = to_date(csv['Hand_Out_Date__c']) if csv else test.hand_out
		self.orders = list()
		self.points_set = set(self._get_time_points())

	def add_order_info(self, order):
		self.orders.append(order)
		self.points_set.add(order.date)


	def get_account_at_time_point(self, point):
		if not hasattr(self, 'sorted'):
			self.sorted = True
			self.orders.sort(key=lambda i: i.date)

		if len(self.orders) == 0 or point >= self.orders[-1].date:
			if len(self.orders) > 0 and not self.orders[-1].buyer == self.final_account:
				print(f'ALERT: final account does not mach last order buyer')

			return self.final_account

		if point < self.orders[0].date:
			return self.orders[0].seller

		return next(iter([order.buyer for order in reversed(self.orders) if order.date <= point]))


	def get_status_at_time_point(self, point):
		if not self.warehoused and not self.external:
			if self.deleted:
				return ProductStatus.deleted
			
			return ProductStatus.hand_out

		if self.warehoused:
			if point < self.warehoused:
				return ProductStatus.absent
			if self.hand_out:
				if point >= self.hand_out:
					return ProductStatus.hand_out

			return ProductStatus.warehoused
		
		if self.external:
			if point < self.external:
				return ProductStatus.absent
			if self.deleted:
				if point >= self.deleted:
					return ProductStatus.deleted

			return ProductStatus.external

		return ProductStatus.absent

	def _get_time_points(self):
		points = list()

		if self.warehoused:
			points.append(self.warehoused)
		
		if self.hand_out:
			points.append(self.hand_out)
		
		if self.external:
			points.append(self.external)
		
		if self.deleted:
			points.append(self.deleted)

		return points


class WinesearcherResponse(object):
	def __init__(self, item):
		self.date = to_date(item['CreatedDate'])
		self.price = float(item['Price_Average__c'])

	def __str__(self):
		return f'{self.date}: {self.price}'

class ProductWineHashHistory(object):
	def __init__(self, item):
		self.hash = item['Product_Wine_Hash__c']
		self.current = None
		self.history = []
		

	def add_value(self, item):
		wr = WinesearcherResponse(item)

		if not self.current or self.current.price != wr.price:
			self.history.append(wr)
			self.current = wr


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


	def get_all_time_points(self):
		return list([wr.date for wr in self.history])


	def __str__(self):
		str = f'{self.hash}\n'

		for item in self.history:
			str += f'{item}\n'

		return str

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
def build_collection_history():
	hash_changes_map = dict()
	products_dict = dict()
	orders_dict = dict()

	with open(os.path.join(os.path.dirname(__file__), 'winesearcher') + '.csv', mode='r') as file:
		raw = csv.DictReader(file)

		for row in raw:
			id = row['Product_Wine_Hash__c']

			hash_changes = hash_changes_map.get(id, ProductWineHashHistory(row))
			hash_changes.add_value(row)

			hash_changes_map[id] = hash_changes


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

if __name__ == "__main__":
	# build_collection_history()
	test_product_account_at_time_point()

