from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
from drink import Drink
from waitress import serve
import conf

app = Flask(__name__)

app.config['SESSION_TYPE'] = 'filesystem'
app.secret_key = conf.secret_key
Session(app)

drinks = [
	Drink(minimum_price=5, starting_price=8, name="Grøn", starting_stock=100),
	Drink(minimum_price=5, starting_price=11, name="Classic", starting_stock=80),
	Drink(minimum_price=6, starting_price=6, name="Små Sure", starting_stock=200),
	Drink(minimum_price=8, starting_price=10, name="Jäger Bomb", starting_stock=50),
	Drink(minimum_price=10, starting_price=15, name="Filur", starting_stock=70),
]
number_of_drinks = len(drinks)

@app.route('/')
def index():
	# Initialize session counters if not present
	if 'counters' not in session:
		session['counters'] = [0 for _ in range(number_of_drinks)]
	total_price = sum(drinks[i].current_price * session['counters'][i] for i in range(number_of_drinks))
	return render_template('index.html', counters=session['counters'], drinks=drinks, total_price=total_price)

@app.route('/update_counter', methods=['POST'])
def update_counter():
	if 'counters' not in session:
		session['counters'] = [0 for _ in range(number_of_drinks)] 

	data = request.json
	counter_id = data.get('counter_id')
	action = data.get('action')

	if counter_id is not None and 0 <= counter_id < len(session['counters']):
		if action == 'increment':
			session['counters'][counter_id] += 1
		elif action == 'decrement':
			if session['counters'][counter_id] > 0:
				session['counters'][counter_id] -= 1
		session.modified = True
		total_price = sum(drinks[i].current_price * session['counters'][i] for i in range(number_of_drinks))
		return jsonify({
			'success': True,
			'new_value': session['counters'][counter_id],
			'total_price': total_price 
		})

	return jsonify({'success': False}), 400

@app.route('/commit', methods=['POST'])
def commit():
	if 'counters' not in session:
		session['counters'] = [0 for _ in range(number_of_drinks)]

	for i in range(len(drinks)):
		drinks[i].stock -= session['counters'][i]
		session['counters'][i] = 0

	session.modified = True
	total_price = sum(drinks[i].current_price * session['counters'][i] for i in range(number_of_drinks))
	return jsonify({
		'success': True,
		'total_price': total_price 
	})

if __name__ == '__main__':
	serve(app, host='0.0.0.0', port=8000)
