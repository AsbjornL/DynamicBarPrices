class Drink:
	def __init__(self, minimum_price : int, starting_price : int, name : str, starting_stock : int):
		self.minimum_price = minimum_price
		self.current_price = starting_price
		self.name = name
		self.starting_stock = starting_stock
		self.stock = starting_stock
