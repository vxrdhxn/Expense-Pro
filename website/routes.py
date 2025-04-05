from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from .models import Expense, User, SUPPORTED_CURRENCIES
from . import db
from .utils import convert_currency, format_currency
import json
from datetime import datetime
from sqlalchemy import extract, func

views = Blueprint('views', __name__)

@views.route('/')
@login_required
def home():
    return render_template('home.html', user=current_user, currencies=SUPPORTED_CURRENCIES)

@views.route('/add-expense', methods=['POST'])
@login_required
def add_expense():
    try:
        data = request.json
        amount = float(data.get('amount', 0))
        currency = data.get('currency', current_user.preferred_currency)
        description = data.get('description', '').strip()
        category = data.get('category', '').strip()
        date_str = data.get('date')

        if not amount or amount <= 0:
            return jsonify({'error': 'Invalid amount'}), 400
        if not description:
            return jsonify({'error': 'Description is required'}), 400
        if not category:
            return jsonify({'error': 'Category is required'}), 400
        if currency not in SUPPORTED_CURRENCIES:
            return jsonify({'error': 'Invalid currency'}), 400

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.now()
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400

        expense = Expense(
            amount=amount,
            currency=currency,
            description=description,
            category=category,
            date=date,
            user_id=current_user.id
        )
        db.session.add(expense)
        db.session.commit()

        return jsonify({
            'message': 'Expense added successfully',
            'expense': expense.to_dict(current_user.preferred_currency)
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@views.route('/get-expenses')
@login_required
def get_expenses():
    try:
        # Get query parameters
        period = request.args.get('period', 'all')
        category = request.args.get('category')
        currency = request.args.get('currency', current_user.preferred_currency)
        
        # Base query
        query = Expense.query.filter_by(user_id=current_user.id)
        
        # Apply period filter
        if period == 'month':
            current_month = datetime.now().month
            current_year = datetime.now().year
            query = query.filter(
                extract('year', Expense.date) == current_year,
                extract('month', Expense.date) == current_month
            )
        elif period == 'year':
            current_year = datetime.now().year
            query = query.filter(extract('year', Expense.date) == current_year)
        
        # Apply category filter
        if category:
            query = query.filter_by(category=category)
        
        # Get expenses
        expenses = query.order_by(Expense.date.desc()).all()
        
        # Calculate totals
        total_amount = 0
        for expense in expenses:
            if expense.currency != currency:
                amount = expense.get_amount_in_currency(currency)
            else:
                amount = expense.amount
            total_amount += amount
        
        # Format response
        return jsonify({
            'expenses': [expense.to_dict(currency) for expense in expenses],
            'total': {
                'amount': total_amount,
                'currency': currency,
                'formatted': format_currency(total_amount, currency)
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@views.route('/update-expense/<int:expense_id>', methods=['PUT'])
@login_required
def update_expense(expense_id):
    try:
        expense = Expense.query.get(expense_id)
        if not expense:
            return jsonify({'error': 'Expense not found'}), 404
        if expense.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403

        data = request.json
        if 'amount' in data:
            try:
                amount = float(data['amount'])
                if amount <= 0:
                    return jsonify({'error': 'Invalid amount'}), 400
                expense.amount = amount
            except ValueError:
                return jsonify({'error': 'Invalid amount format'}), 400

        if 'currency' in data:
            currency = data['currency']
            if currency not in SUPPORTED_CURRENCIES:
                return jsonify({'error': 'Invalid currency'}), 400
            expense.currency = currency

        if 'description' in data:
            description = data['description'].strip()
            if not description:
                return jsonify({'error': 'Description is required'}), 400
            expense.description = description

        if 'category' in data:
            category = data['category'].strip()
            if not category:
                return jsonify({'error': 'Category is required'}), 400
            expense.category = category

        if 'date' in data:
            try:
                expense.date = datetime.strptime(data['date'], '%Y-%m-%d')
            except ValueError:
                return jsonify({'error': 'Invalid date format'}), 400

        db.session.commit()
        return jsonify({
            'message': 'Expense updated successfully',
            'expense': expense.to_dict(current_user.preferred_currency)
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@views.route('/delete-expense/<int:expense_id>', methods=['DELETE'])
@login_required
def delete_expense(expense_id):
    try:
        expense = Expense.query.get(expense_id)
        if not expense:
            return jsonify({'error': 'Expense not found'}), 404
        if expense.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403

        db.session.delete(expense)
        db.session.commit()
        return jsonify({'message': 'Expense deleted successfully'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@views.route('/get-stats')
@login_required
def get_stats():
    try:
        currency = request.args.get('currency', current_user.preferred_currency)
        
        # Get current month and year
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Query for monthly stats
        monthly_expenses = Expense.query.filter(
            Expense.user_id == current_user.id,
            extract('year', Expense.date) == current_year,
            extract('month', Expense.date) == current_month
        ).all()
        
        # Query for yearly stats
        yearly_expenses = Expense.query.filter(
            Expense.user_id == current_user.id,
            extract('year', Expense.date) == current_year
        ).all()
        
        # Calculate totals
        monthly_total = sum(
            expense.get_amount_in_currency(currency)
            for expense in monthly_expenses
        )
        
        yearly_total = sum(
            expense.get_amount_in_currency(currency)
            for expense in yearly_expenses
        )
        
        # Calculate averages
        monthly_avg = monthly_total / len(monthly_expenses) if monthly_expenses else 0
        yearly_avg = yearly_total / len(yearly_expenses) if yearly_expenses else 0
        
        # Get category breakdown for current month
        category_totals = {}
        for expense in monthly_expenses:
            amount = expense.get_amount_in_currency(currency)
            category_totals[expense.category] = category_totals.get(expense.category, 0) + amount
        
        # Format response
        return jsonify({
            'monthly': {
                'total': monthly_total,
                'formatted_total': format_currency(monthly_total, currency),
                'average': monthly_avg,
                'formatted_average': format_currency(monthly_avg, currency),
                'count': len(monthly_expenses)
            },
            'yearly': {
                'total': yearly_total,
                'formatted_total': format_currency(yearly_total, currency),
                'average': yearly_avg,
                'formatted_average': format_currency(yearly_avg, currency),
                'count': len(yearly_expenses)
            },
            'categories': {
                category: {
                    'total': total,
                    'formatted_total': format_currency(total, currency),
                    'percentage': (total / monthly_total * 100) if monthly_total > 0 else 0
                }
                for category, total in category_totals.items()
            },
            'currency': currency
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@views.route('/update-settings', methods=['POST'])
@login_required
def update_settings():
    try:
        data = request.json
        
        if 'preferred_currency' in data:
            currency = data['preferred_currency']
            if currency not in SUPPORTED_CURRENCIES:
                return jsonify({'error': 'Invalid currency'}), 400
            current_user.preferred_currency = currency
        
        db.session.commit()
        return jsonify({'message': 'Settings updated successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500 