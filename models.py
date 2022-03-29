from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

events = db.Table('events',
	db.Column('event_id', db.Integer, db.ForeignKey('event.event_id'), primary_key=True),
	db.Column('user_id', db.Integer, db.ForeignKey('user.user_id'), primary_key=True)
)

class User(db.Model):
	user_id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(24), nullable=False)
	pw_hash = db.Column(db.String(64), nullable=False)
	isStaff = db.Column(db.Boolean, nullable=False)
	events = db.relationship('Event', secondary=events, lazy='dynamic',
		backref=db.backref('users', lazy=True))
	
	
	def __init__(self, username, pw_hash, isStaff):
		self.username = username
		self.pw_hash = pw_hash
		self.isStaff = isStaff

	def __repr__(self):
		return '{}'.format(self.username)

class Event(db.Model):
	event_id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(24), nullable=False)
	date = db.Column(db.Date, nullable=False)

	def __init__(self, name, date, user):
		self.name = name
		self.date = date
		self.users = [user]



