from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from .models import Expense, User, SUPPORTED_CURRENCIES, EXPENSE_CATEGORIES
from . import db
import json
from datetime import datetime
from sqlalchemy import extract, func

views = Blueprint('views', __name__)

@views.route('/')
@login_required
def home():
    today_date = datetime.now().strftime('%Y-%m-%d')
    stats = current_user.get_monthly_stats()
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).limit(10).all()
    
    return render_template(
        'home.html',
        user=current_user,
        expenses=expenses,
        total_expenses=stats['total'],
        total_transactions=stats['count'],
        average_expense=stats['average'],
        today_date=today_date
    )

@views.route('/get-stats')
@login_required
def get_stats():
    monthly_stats = current_user.get_monthly_stats()
    yearly_stats = current_user.get_yearly_stats()
    
    return jsonify({
        'categories': monthly_stats['categories'],
        'monthly_trend': yearly_stats['monthly_totals'],
        'total': monthly_stats['total'],
        'count': monthly_stats['count'],
        'average': monthly_stats['average'],
        'budget_percentage': monthly_stats['budget_percentage']
    })

@views.route('/get-expenses')
@login_required
def get_expenses():
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()
    return jsonify({
        'expenses': [expense.to_dict() for expense in expenses]
    })

@views.route('/get-expense/<int:expense_id>')
@login_required
def get_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    if expense.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    return jsonify(expense.to_dict())

@views.route('/add-expense', methods=['POST'])
@login_required
def add_expense():
    try:
        data = request.get_json()
        
        if not all(key in data for key in ['amount', 'description', 'category', 'date']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        amount = float(data['amount'])
        if amount <= 0:
            return jsonify({'error': 'Amount must be greater than 0'}), 400
        
        if data['category'] not in EXPENSE_CATEGORIES:
            return jsonify({'error': 'Invalid category'}), 400
        
        expense = Expense(
            user_id=current_user.id,
            amount=amount,
            description=data['description'],
            category=data['category'],
            date=datetime.strptime(data['date'], '%Y-%m-%d'),
            notes=data.get('notes'),
            tags=json.dumps(data.get('tags', []))
        )
        
        db.session.add(expense)
        db.session.commit()
        
        return jsonify({'message': 'Expense added successfully', 'expense': expense.to_dict()})
    
    except ValueError as e:
        return jsonify({'error': 'Invalid amount format'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@views.route('/update-expense/<int:expense_id>', methods=['PUT'])
@login_required
def update_expense(expense_id):
    try:
        expense = Expense.query.get_or_404(expense_id)
        if expense.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        
        if not all(key in data for key in ['amount', 'description', 'category', 'date']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        amount = float(data['amount'])
        if amount <= 0:
            return jsonify({'error': 'Amount must be greater than 0'}), 400
        
        if data['category'] not in EXPENSE_CATEGORIES:
            return jsonify({'error': 'Invalid category'}), 400
        
        expense.amount = amount
        expense.description = data['description']
        expense.category = data['category']
        expense.date = datetime.strptime(data['date'], '%Y-%m-%d')
        expense.notes = data.get('notes')
        expense.tags = json.dumps(data.get('tags', []))
        
        db.session.commit()
        
        return jsonify({'message': 'Expense updated successfully', 'expense': expense.to_dict()})
    
    except ValueError as e:
        return jsonify({'error': 'Invalid amount format'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@views.route('/delete-expense/<int:expense_id>', methods=['DELETE'])
@login_required
def delete_expense(expense_id):
    try:
        expense = Expense.query.get_or_404(expense_id)
        if expense.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        db.session.delete(expense)
        db.session.commit()
        
        return jsonify({'message': 'Expense deleted successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@views.route('/update-settings', methods=['POST'])
@login_required
def update_settings():
    try:
        data = request.get_json()
        
        if 'monthly_budget' in data:
            try:
                monthly_budget = float(data['monthly_budget'])
                if monthly_budget < 0:
                    return jsonify({'error': 'Budget must be non-negative'}), 400
                current_user.monthly_budget = monthly_budget
            except ValueError:
                return jsonify({'error': 'Invalid budget format'}), 400
        
        if 'notification_preferences' in data:
            current_user.set_notification_preferences(data['notification_preferences'])
        
        db.session.commit()
        return jsonify({'message': 'Settings updated successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500 