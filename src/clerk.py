import threading
import requests
import time
import conf

from flask import Flask, render_template, jsonify, session, request
from flask_session import Session

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.secret_key = conf.secret_key
Session(app)

drinks = []
last_updated = 0
lock = threading.Lock()

@app.route("/")
def index():
	if 'counts' not in session:
		session['counts'] = {}
	total_price = sum(drink['price'] * session['counts'].get(drink['id'], 0) for drink in drinks)
	return render_template("clerk.html", counts=session['counts'], drinks=drinks, total_price=total_price)

@app.route("/get-updates")
def get_updates():
	with lock:
		total_price = sum(drink['price'] * session['counts'].get(drink['id'], 0) for drink in drinks)
		return jsonify({"drinks": drinks, "total_price": total_price})

@app.route('/update_counter', methods=['POST'])
def update_counter():
	if 'counts' not in session:
		session['counts'] = {}

	data = request.json
	counter_id = data.get('counter_id')
	action = data.get('action')

	if counter_id is not None:
		if action == 'increment':
			session['counts'][counter_id] = session['counts'].get(counter_id, 0) + 1
		elif action == 'decrement':
			if session['counts'].get(counter_id, 0) > 0:
				session['counts'][counter_id] -= 1
		session.modified = True
		total_price = sum(drink['price'] * session['counts'].get(drink['id'], 0) for drink in drinks)
		return jsonify({
			'success': True,
			'new_value': session['counts'].get(counter_id),
			'total_price': total_price 
		})

	return jsonify({'success': False}), 400

@app.route('/commit', methods=['POST'])
def commit():
	if 'counts' not in session:
		session['counts'] = {}

	request_data = []
	with lock:
		for id, count in session['counts'].items():
			request_data.append({"id": id, "count": -count})
			session['counts'][id] = 0

	session.modified = True

	headers = {'Content-type': 'application/json'}
	response = requests.post(conf.server_url + "/update-stock", json=request_data, headers=headers)
	if response.status_code == 200:
		return jsonify({"success": True, "total_price": 0}), 200
	else:
		error = response.json()['error']
		print("Commiting failed:", error)
		return jsonify({"success": False, "error": error, "total_price": 0}), 200

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
	app.run(debug=True, port=conf.clerk_port)
