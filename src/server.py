import threading
import time
import conf

from flask import Flask, jsonify, request, render_template
from drink import Drink

app = Flask(__name__)

drinks_mutex = threading.Lock()
drinks = (
	Drink(minimum_price=5, starting_price=8, name="Grøn", starting_stock=100),
	Drink(minimum_price=5, starting_price=11, name="Classic", starting_stock=80),
	Drink(minimum_price=6, starting_price=6, name="Små Sure", starting_stock=200),
	Drink(minimum_price=8, starting_price=10, name="Jäger Bomb", starting_stock=50),
	Drink(minimum_price=10, starting_price=15, name="Filur", starting_stock=70),
)
time_mutex = threading.Lock()
last_updated = time.time()

def update_loop():
	global last_updated
	while True:
		time.sleep(300)
		with drinks_mutex:
			for drink in drinks:
				drink.update_price()
		with time_mutex:
			last_updated = time.time()

@app.route("/get-drinks", methods=["GET"])
def get_data():
	client_last_updated = float(request.args.get("last_updated", 0))
	while True:
		ready = False
		with time_mutex:
			if last_updated > client_last_updated:
				ready = True
		if ready:
			with drinks_mutex:
				return jsonify({
						"last_updated": last_updated,
						"drinks": [{"id": i, "name": drink.name, "price": drink.current_price, "stock": drink.stock} for i, drink in enumerate(drinks)]
					})
		time.sleep(1)

@app.route("/update-stock", methods=["POST"])
def update_stock():
	global drinks, last_updated
	request_data = request.json
	
	with drinks_mutex:
		try:
			for drink in request_data:
				drinks[int(drink["id"])].stock += int(drink["count"])
				drinks[int(drink["id"])].update_price()
		except KeyError:
			return jsonify({"error": "Invalid data"}), 400
	with time_mutex:
		last_updated = time.time()

	return jsonify({"message": "Stock updated successfully", "data": request_data}), 200

@app.route("/admin", methods=["GET"])
def admin_page():
	return render_template("admin.html")

@app.route("/admin/update-drink", methods=["POST"])
def admin_update_drink():
	global last_updated
	request_data = request.json
	print(request_data)

	try:
		drink_id = int(request_data["id"])
		with drinks_mutex:
			if name := request_data.get('name'):
				drinks[drink_id].name = name
			if price := request_data.get('price'):
				drinks[drink_id].current_price = float(price)
			if stock := request_data.get('stock'):
				drinks[drink_id].stock = int(stock)
			drinks[drink_id].update_price()
		with time_mutex:
			last_updated = time.time()
		return jsonify({"message": "Drink updated successfully"}), 200
	except (KeyError, ValueError, IndexError):
		return jsonify({"error": "Invalid input"}), 400

if __name__ == "__main__":
	update_loop_thread = threading.Thread(target=update_loop, daemon=True)
	update_loop_thread.start()
	app.run(debug=True, port=conf.server_port)
