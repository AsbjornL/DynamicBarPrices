from flask import Flask, jsonify, request
from drink import Drink
import threading
import time

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
	while True:
		time.sleep(300)
		with drink_mutex:
			for drink in drinks:
				pass
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
						"drinks": [{"id": i, "name": drink.name, "price": drink.current_price} for i, drink in enumerate(drinks)]
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
		except KeyError:
			return jsonify({"error", "Invalid data"}), 400
	with time_mutex:
		last_updated = time.time()

	return jsonify({"message": "Stock updated successfully", "data": request_data}), 200

if __name__ == "__main__":
	update_loop_thread = threading.Thread(target=update_loop, daemon=True)
	update_loop_thread.start()
	app.run(debug=True)
