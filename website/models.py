from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Dictionary of supported currencies and their symbols
SUPPORTED_CURRENCIES = {
    'USD': '$',
    'EUR': '€',
    'GBP': '£',
    'JPY': '¥',
    'INR': '₹',
    'AUD': 'A$',
    'CAD': 'C$',
    'CHF': 'Fr',
    'CNY': '¥',
    'NZD': 'NZ$'
}

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    currency = db.Column(db.String(3), default='USD', nullable=False)
    email_notifications = db.Column(db.Boolean, default=False, nullable=False)
    monthly_report = db.Column(db.Boolean, default=False, nullable=False)
    default_view = db.Column(db.String(10), default='monthly', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expenses = db.relationship('Expense', backref='user', lazy=True, cascade='all, delete-orphan')

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_currency_symbol(self):
        return SUPPORTED_CURRENCIES.get(self.currency, '$')

    def __repr__(self):
        return f'<User {self.email}>'

class Expense(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    original_amount = db.Column(db.Float, nullable=False)  # Amount in original currency
    original_currency = db.Column(db.String(3), nullable=False, default='USD')  # Currency at time of entry
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @property
    def formatted_date(self):
        return self.date.strftime('%Y-%m-%d')

    @property
    def formatted_amount(self):
        return "{:.2f}".format(self.amount)

    def to_dict(self):
        return {
            'id': self.id,
            'amount': self.amount,
            'original_amount': self.original_amount,
            'original_currency': self.original_currency,
            'category': self.category,
            'description': self.description,
            'date': self.date.strftime('%Y-%m-%d %H:%M:%S'),
            'user_id': self.user_id
        }
