from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    interests = db.Column(db.String(200))

class Preference(db.Model):
    __tablename__ = 'preferences'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    preferred_age_min = db.Column(db.Integer)
    preferred_age_max = db.Column(db.Integer)
    preferred_gender = db.Column(db.String(10))
    user = db.relationship('User', backref=db.backref('preferences', lazy=True))

class SwipeRight(db.Model):
    __tablename__ = 'swipe_rights'
    id = db.Column(db.Integer, primary_key=True)
    swiper_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    swipee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    swiper = db.relationship('User', foreign_keys=[swiper_id], backref=db.backref('swipes_made', lazy=True))
    swipee = db.relationship('User', foreign_keys=[swipee_id], backref=db.backref('swipes_received', lazy=True))
