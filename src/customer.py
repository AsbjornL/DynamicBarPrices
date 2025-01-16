import threading
import requests
import time
import conf

from flask import Flask, render_template, jsonify

app = Flask(__name__)

drinks = []
last_updated = 0
lock = threading.Lock()

@app.route("/")
def page():
	return render_template("customer.html")

@app.route("/get-updates")
def get_updates():
	with lock:
		return jsonify({"data": drinks})

def update_loop():
	global drinks, last_updated
	while True:
		try:
			response = requests.get(conf.server_url + "/get-drinks", params={"last_updated": last_updated}, timeout=60)
			if response.status_code == 200:
				response_data = response.json()
				with lock:
					drinks = response_data["drinks"]
					last_updated = response_data["last_updated"]
		except requests.exceptions.Timeout:
			print("Request timed out. Retrying...")
		except Exception as e:
			print("Error:", e)
			break
		time.sleep(1)

if __name__ == "__main__":
	update_loop_thread = threading.Thread(target=update_loop, daemon=True)
	update_loop_thread.start()
	app.run(debug=True, port=conf.customer_port)
