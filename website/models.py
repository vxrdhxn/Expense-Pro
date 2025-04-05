from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

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

EXPENSE_CATEGORIES = {
    'Food': 'Food & Dining',
    'Transportation': 'Transportation',
    'Housing': 'Housing & Utilities',
    'Entertainment': 'Entertainment',
    'Shopping': 'Shopping',
    'Healthcare': 'Healthcare',
    'Education': 'Education',
    'Travel': 'Travel',
    'Investment': 'Investment',
    'Other': 'Other'
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
    monthly_budget = db.Column(db.Float, default=1000.0)
    notification_preferences = db.Column(db.Text, default='{}')
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
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

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_notification_preferences(self):
        try:
            return json.loads(self.notification_preferences)
        except:
            return {}

    def set_notification_preferences(self, preferences):
        self.notification_preferences = json.dumps(preferences)

    def get_monthly_stats(self, year=None, month=None):
        if year is None or month is None:
            now = datetime.now()
            year = now.year
            month = now.month

        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        expenses = Expense.query.filter(
            Expense.user_id == self.id,
            Expense.date >= start_date,
            Expense.date < end_date
        ).all()

        total = sum(expense.amount for expense in expenses)
        count = len(expenses)
        average = total / count if count > 0 else 0

        categories = {}
        for expense in expenses:
            if expense.category not in categories:
                categories[expense.category] = {
                    'total': 0,
                    'count': 0
                }
            categories[expense.category]['total'] += expense.amount
            categories[expense.category]['count'] += 1

        return {
            'total': total,
            'count': count,
            'average': average,
            'categories': categories,
            'budget_percentage': (total / self.monthly_budget * 100) if self.monthly_budget else 0
        }

    def get_yearly_stats(self, year=None):
        if year is None:
            year = datetime.now().year

        start_date = datetime(year, 1, 1)
        end_date = datetime(year + 1, 1, 1)

        expenses = Expense.query.filter(
            Expense.user_id == self.id,
            Expense.date >= start_date,
            Expense.date < end_date
        ).all()

        monthly_totals = {}
        for month in range(1, 13):
            monthly_totals[month] = 0

        for expense in expenses:
            monthly_totals[expense.date.month] += expense.amount

        return {
            'monthly_totals': monthly_totals,
            'total': sum(monthly_totals.values()),
            'average_monthly': sum(monthly_totals.values()) / 12
        }

    def __repr__(self):
        return f'<User {self.email}>'

class Expense(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    date = db.Column(db.DateTime(timezone=True), nullable=False, default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    notes = db.Column(db.Text)
    tags = db.Column(db.Text)

    @property
    def formatted_amount(self):
        return "{:.2f}".format(self.amount)

    @property
    def formatted_date(self):
        return self.date.strftime("%Y-%m-%d")

    def to_dict(self):
        return {
            'id': self.id,
            'amount': self.amount,
            'formatted_amount': self.formatted_amount,
            'description': self.description,
            'category': self.category,
            'date': self.formatted_date,
            'notes': self.notes,
            'tags': json.loads(self.tags) if self.tags else []
        }

    def set_tags(self, tags):
        self.tags = json.dumps(tags) if tags else None

    def __repr__(self):
        return f'<Expense {self.id}: {self.amount}>'
