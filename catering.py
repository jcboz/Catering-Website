

import time
import os
from hashlib import md5
from datetime import datetime
from flask import Flask, request, session, url_for, redirect, render_template, abort, g, flash, _app_ctx_stack
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date
from sqlalchemy import not_

from models import db, User, Event

app = Flask(__name__)

# configuration
PER_PAGE = 30
DEBUG = True
SECRET_KEY = 'development key'

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(app.root_path, 'catering.db')

app.config.from_object(__name__)
app.config.from_envvar('CATERING_SETTINGS', silent=True)

db.init_app(app)


@app.cli.command('initdb')
def initdb_command():
	"""Creates the database tables."""
	db.create_all()
	db.session.add(User("owner", generate_password_hash("pass"), True))
	db.session.commit()
	print('Initialized the database.')

@app.cli.command('deletedb')
def deletedb_command():
	db.drop_all()
	

def get_user_id(username):
	"""Convenience method to look up the id for a username."""
	rv = User.query.filter_by(username=username).first()
	return rv.user_id if rv else None

def get_event_id(date):
	"""Convenience method to look up the id for an event"""
	rv = Event.query.filter_by(date=date).first()
	return rv.event_id if rv else None

@app.before_request
def before_request():
	g.user = None
	if 'user_id' in session:
		g.user = User.query.filter_by(user_id=session['user_id']).first()
	g.event = None
	if 'event_id' in session:
		g.event = User.query.filter_by(user_id=session['event_id']).first()


@app.route('/')
def home():
	"""Shows the login screen (for now)"""
	return render_template('home.html')

@app.route('/user', methods=['GET', 'POST'])
def user():
	if not g.user:
		return redirect('/login')

	"""for loop here that cycles through all events and displays user's events"""
	user_events = Event.query.filter(Event.users.contains(g.user)).all()
	print(user_events)
	return render_template('user.html', events=user_events)

@app.route('/register', methods=['GET', 'POST'])
def register():
	"""Register an account"""
	error = None
	if request.method == 'POST':
		if not request.form['username']:
			error = 'You have to enter a username'
		elif not request.form['password']:
			error = 'You have to enter a password'
		elif request.form['password'] != request.form['password2']:
			error = 'The two passwords do not match'
		elif get_user_id(request.form['username']) is not None:
			error = 'The username is already taken'
		else:
			db.session.add(User(request.form['username'], generate_password_hash(request.form['password']), False))
			db.session.commit()
			flash('You were successfully registered and can login now')
			return redirect(url_for('login'))
	return render_template('register.html', error=error)

@app.route('/delete/<eventid>')
def delete(eventid):
	if not g.user:
		return redirect('/login')
	if not eventid:
		abort(404)
	
	event = Event.query.filter_by(event_id=eventid).first()
	db.session.delete(event)
	db.session.commit()
	flash('Event successfully deleted')
	if g.user.username == "owner":
		return redirect(url_for('owner_page'))
	return redirect(url_for('user'))

@app.route('/join/<eventid>')
def join(eventid):
	if not g.user:
		return redirect('/login')
	if not eventid:
		abort(404)
	event = Event.query.filter_by(event_id=eventid).first()
	users = event.users
	users.append(g.user)
	event.users = users
	db.session.commit()
	flash('Event successfully joined')
	return redirect(url_for('staff_page'))	

@app.route('/login', methods=['GET', 'POST'])
def login():
	error = None
	if request.method == 'POST':

		user = User.query.filter_by(username=request.form['username']).first()
		if user is None:
			error = 'Invalid username or password'
		elif not check_password_hash(user.pw_hash, request.form['password']):
			error = 'Invalid username or password'
		else:
			flash('You were logged in')
			session['user_id'] = user.user_id
			if user.username == 'owner':
				return redirect(url_for('owner_page'))
			elif user.isStaff == True:
				return redirect(url_for('staff_page'))
			else:
				return redirect(url_for('user'))
	return render_template('login.html', error=error)

@app.route('/new_staff', methods=['GET', 'POST'])
def new_staff():
	error = None
	if request.method == 'POST':
		if not request.form['username']:
			error = 'You have to enter a username'
		elif not request.form['password']:
			error = 'You have to enter a password'
		elif request.form['password'] != request.form['password2']:
			error = 'The two passwords do not match'
		elif get_user_id(request.form['username']) is not None:
			error = 'The username is already taken'
		else:
			db.session.add(User(request.form['username'], generate_password_hash(request.form['password']), True))
			db.session.commit()
			flash('You have successfully registered a staff account')
			return redirect(url_for('login'))
	return render_template('new_staff.html', error=error)

@app.route('/logout')
def logout():
	"""Logs the user out."""
	flash('You were logged out')
	session.pop('user_id', None)
	return redirect(url_for('home'))

def staff_filter(staff):
	return [ s for s in staff if s.isStaff]
 
@app.route('/owner_page', methods=['GET', 'POST'])
def owner_page():
	if not g.user:
		return redirect('/login')
	all_events = Event.query.all()
	return render_template('owner_page.html', staff_filter=staff_filter, events=all_events)

@app.route('/staff_page', methods=['GET', 'POST'])
def staff_page():
	if not g.user:
		return redirect('/login')


	staff_events = Event.query.filter(not_(Event.users.contains(g.user))).all()

	filter_ = []
	for event in staff_events:
		if len(event.users) < 4:
			filter_.append(event)
	joined_events = Event.query.filter(Event.users.contains(g.user)).all()

	print(filter_)
	print(joined_events)
	return render_template('staff_page.html', events=filter_, joined_events=joined_events)

@app.route('/request_event', methods=['GET', 'POST'])
def request_event():
	error = None
	if request.method == 'POST':
		if not request.form['name']:
			error = 'You have to enter an event name'
		elif not request.form['date']:
			error = 'You have to enter a date'
		elif get_event_id(request.form['date']) is not None:
			error = 'The company is already booked for that date'
		else:
			strDate = str(request.form['date'])
			yint = int(strDate[0:4])
			mint = int(strDate[5:7])
			dint = int(strDate[8:10])
			db.session.add(Event(request.form['name'], date(yint, mint, dint), g.user))
			"""db.session.add(Event(request.form['name'], date(2022, 3, 22)))"""
			db.session.commit()
			flash('You have successfully requested an Event')
			return redirect(url_for('user')) 
	return render_template('request_event.html', error=error)


