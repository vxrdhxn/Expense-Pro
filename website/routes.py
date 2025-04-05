from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from .models import Expense, User, SUPPORTED_CURRENCIES
from . import db
import json
from datetime import datetime
from sqlalchemy import extract, func

views = Blueprint('views', __name__)

@views.route('/')
@login_required
def home():
    # Get current month's expenses
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        extract('year', Expense.date) == current_year,
        extract('month', Expense.date) == current_month
    ).order_by(Expense.date.desc()).all()
    
    # Calculate statistics
    total_expenses = sum(expense.amount for expense in expenses)
    total_transactions = len(expenses)
    average_expense = total_expenses / total_transactions if total_transactions > 0 else 0
    
    return render_template(
        'home.html',
        user=current_user,
        expenses=expenses,
        total_expenses=total_expenses,
        total_transactions=total_transactions,
        average_expense=average_expense,
        today_date=datetime.now().strftime('%Y-%m-%d')
    )

@views.route('/add-expense', methods=['POST'])
@login_required
def add_expense():
    try:
        data = request.json
        amount = float(data.get('amount', 0))
        description = data.get('description', '').strip()
        category = data.get('category', '').strip()
        date_str = data.get('date')

        if not amount or amount <= 0:
            return jsonify({'error': 'Invalid amount'}), 400
        if not description:
            return jsonify({'error': 'Description is required'}), 400
        if not category:
            return jsonify({'error': 'Category is required'}), 400

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.now()
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400

        expense = Expense(
            amount=amount,
            description=description,
            category=category,
            date=date,
            user_id=current_user.id
        )
        db.session.add(expense)
        db.session.commit()

        return jsonify({
            'message': 'Expense added successfully',
            'expense': expense.to_dict()
        })

    except Exception as e:
        db.session.rollback()
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
            'expense': expense.to_dict()
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
        monthly_total = sum(expense.amount for expense in monthly_expenses)
        yearly_total = sum(expense.amount for expense in yearly_expenses)
        
        # Calculate averages
        monthly_avg = monthly_total / len(monthly_expenses) if monthly_expenses else 0
        yearly_avg = yearly_total / len(yearly_expenses) if yearly_expenses else 0
        
        # Get category breakdown for current month
        category_totals = {}
        for expense in monthly_expenses:
            category_totals[expense.category] = category_totals.get(expense.category, 0) + expense.amount
        
        # Format response
        return jsonify({
            'monthly': {
                'total': monthly_total,
                'formatted_total': f"{current_user.get_currency_symbol()}{monthly_total:,.2f}",
                'average': monthly_avg,
                'formatted_average': f"{current_user.get_currency_symbol()}{monthly_avg:,.2f}",
                'count': len(monthly_expenses)
            },
            'yearly': {
                'total': yearly_total,
                'formatted_total': f"{current_user.get_currency_symbol()}{yearly_total:,.2f}",
                'average': yearly_avg,
                'formatted_average': f"{current_user.get_currency_symbol()}{yearly_avg:,.2f}",
                'count': len(yearly_expenses)
            },
            'categories': {
                category: {
                    'total': total,
                    'formatted_total': f"{current_user.get_currency_symbol()}{total:,.2f}",
                    'percentage': (total / monthly_total * 100) if monthly_total > 0 else 0
                }
                for category, total in category_totals.items()
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500 