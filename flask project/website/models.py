from flask_login import UserMixin
from datetime import datetime, timedelta
from sqlalchemy import CheckConstraint, ForeignKey, event
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from . import db  # Import db from __init__.py instead

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    first_name = db.Column(db.String(150), nullable=False)
    currency = db.Column(db.String(3), default='INR', nullable=False)
    monthly_budget = db.Column(db.Float, default=0.0, nullable=False)
    theme = db.Column(db.String(10), default='light', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    expenses = db.relationship('Expense', back_populates='user', cascade='all, delete-orphan')
    categories = db.relationship('Category', back_populates='user', cascade='all, delete-orphan')
    budgets = db.relationship('Budget', back_populates='user', cascade='all, delete-orphan')

    def set_password(self, password):
        """Hash and set the user's password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the hash"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(7), default='#808080')
    icon = db.Column(db.String(50))
    user_id = db.Column(db.Integer, ForeignKey('users.id'), nullable=True)
    
    # Relationships
    user = db.relationship('User', back_populates='categories')
    expenses = db.relationship('Expense', back_populates='category')
    budgets = db.relationship('Budget', back_populates='category')

class Budget(db.Model):
    __tablename__ = 'budgets'
    
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, ForeignKey('categories.id'), nullable=False)
    
    # Relationships
    user = db.relationship('User', back_populates='budgets')
    category = db.relationship('Category', back_populates='budgets')

class Expense(db.Model):
    __tablename__ = 'expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    currency = db.Column(db.String(3), nullable=False)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, ForeignKey('categories.id'), nullable=False)
    
    # Relationships
    user = db.relationship('User', back_populates='expenses')
    category = db.relationship('Category', back_populates='expenses')
