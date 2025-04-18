from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, session
from flask_login import login_required, current_user
from . import db
from .models import User, Expense, Category, Budget
from datetime import datetime, timedelta
import calendar
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash
from .auth import is_strong_password

views = Blueprint('views', __name__)

CURRENCIES = [
    ('USD', 'US Dollar ($)'),
    ('EUR', 'Euro (€)'),
    ('GBP', 'British Pound (£)'),
    ('JPY', 'Japanese Yen (¥)'),
    ('INR', 'Indian Rupee (₹)'),
    ('CNY', 'Chinese Yuan (¥)'),
    ('CAD', 'Canadian Dollar ($)'),
    ('AUD', 'Australian Dollar ($)'),
    ('SGD', 'Singapore Dollar ($)'),
    ('HKD', 'Hong Kong Dollar ($)')
]

@views.route('/')
@login_required
def home():
    # Get theme-based colors
    theme_colors = {
        'light': {
            'box_bg': '#ffffff',
            'text': '#2c3e50',
            'border': '#e2e8f0',
            'shadow': 'rgba(0, 0, 0, 0.1)'
        },
        'dark': {
            'box_bg': '#1a202c',
            'text': '#e2e8f0',
            'border': '#2d3748',
            'shadow': 'rgba(0, 0, 0, 0.25)'
        }
    }
    current_theme = current_user.theme or 'light'
    colors = theme_colors[current_theme]
    
    # Get user's categories
    categories = Category.query.filter_by(user_id=current_user.id).all()
    chart_categories = [category.name for category in categories]
    
    # Get expenses by category
    chart_amounts = []
    for category in categories:
        amount = db.session.query(func.sum(Expense.amount))\
            .filter_by(user_id=current_user.id, category_id=category.id)\
            .scalar() or 0
        chart_amounts.append(float(amount))
    
    # Get daily expenses for the last 7 days
    today = datetime.now().date()
    daily_expenses = []
    for i in range(7):
        date = today - timedelta(days=i)
        amount = db.session.query(func.sum(Expense.amount))\
            .filter(
                Expense.user_id == current_user.id,
                func.date(Expense.date) == date
            ).scalar() or 0
        daily_expenses.append({
            'date': date.strftime('%Y-%m-%d'),
            'amount': float(amount)
        })
    daily_expenses.reverse()  # Show oldest to newest
    
    # Get recent expenses
    recent_expenses = Expense.query.filter_by(user_id=current_user.id)\
        .order_by(Expense.date.desc())\
        .limit(5)\
        .all()
    
    # Calculate total expenses
    total_expenses = db.session.query(func.sum(Expense.amount))\
        .filter_by(user_id=current_user.id)\
        .scalar() or 0

    # Calculate monthly average
    first_expense = Expense.query.filter_by(user_id=current_user.id)\
        .order_by(Expense.date.asc())\
        .first()
    
    if first_expense:
        months = (datetime.now().date() - first_expense.date.date()).days / 30.44  # Average days in a month
        monthly_average = total_expenses / max(1, months)
    else:
        monthly_average = 0

    # Calculate current month's expenses and budget progress
    current_month = datetime.now().month
    current_year = datetime.now().year
    current_month_expenses = db.session.query(func.sum(Expense.amount))\
        .filter(
            Expense.user_id == current_user.id,
            func.extract('month', Expense.date) == current_month,
            func.extract('year', Expense.date) == current_year
        ).scalar() or 0

    # Get user's monthly budget
    monthly_budget = current_user.monthly_budget or 0
    
    # Calculate budget progress
    if monthly_budget > 0:
        budget_progress = min(100, round((current_month_expenses / monthly_budget) * 100))
    else:
        budget_progress = 0
    
    return render_template('home.html',
                         user=current_user,
                         chart_categories=chart_categories,
                         chart_amounts=chart_amounts,
                         daily_expenses=daily_expenses,
                         recent_expenses=recent_expenses,
                         total_expenses=total_expenses,
                         monthly_average=monthly_average,
                         budget_progress=budget_progress,
                         colors=colors)

@views.route('/dashboard')
@login_required
def dashboard():
    # Get theme-based colors
    theme_colors = {
        'light': {
            'box_bg': '#ffffff',
            'text': '#2c3e50',
            'border': '#e2e8f0',
            'shadow': 'rgba(0, 0, 0, 0.1)'
        },
        'dark': {
            'box_bg': '#1a202c',
            'text': '#e2e8f0',
            'border': '#2d3748',
            'shadow': 'rgba(0, 0, 0, 0.25)'
        }
    }
    current_theme = current_user.theme or 'light'
    colors = theme_colors[current_theme]
    
    # Get user's categories
    categories = Category.query.filter_by(user_id=current_user.id).all()
    chart_categories = [category.name for category in categories]
    
    # Get expenses by category
    chart_amounts = []
    for category in categories:
        amount = db.session.query(func.sum(Expense.amount))\
            .filter_by(user_id=current_user.id, category_id=category.id)\
            .scalar() or 0
        chart_amounts.append(float(amount))
    
    # Get daily expenses for the last 7 days
    today = datetime.now().date()
    daily_expenses = []
    for i in range(7):
        date = today - timedelta(days=i)
        amount = db.session.query(func.sum(Expense.amount))\
            .filter(
                Expense.user_id == current_user.id,
                func.date(Expense.date) == date
            ).scalar() or 0
        daily_expenses.append({
            'date': date.strftime('%Y-%m-%d'),
            'amount': float(amount)
        })
    daily_expenses.reverse()  # Show oldest to newest
    
    # Get recent expenses
    recent_expenses = Expense.query.filter_by(user_id=current_user.id)\
        .order_by(Expense.date.desc())\
        .limit(5)\
        .all()
    
    # Calculate total expenses
    total_expenses = db.session.query(func.sum(Expense.amount))\
        .filter_by(user_id=current_user.id)\
        .scalar() or 0

    # Calculate monthly average
    first_expense = Expense.query.filter_by(user_id=current_user.id)\
        .order_by(Expense.date.asc())\
        .first()
    
    if first_expense:
        months = (datetime.now().date() - first_expense.date.date()).days / 30.44  # Average days in a month
        monthly_average = total_expenses / max(1, months)
    else:
        monthly_average = 0

    # Calculate current month's expenses and budget progress
    current_month = datetime.now().month
    current_year = datetime.now().year
    current_month_expenses = db.session.query(func.sum(Expense.amount))\
        .filter(
            Expense.user_id == current_user.id,
            func.extract('month', Expense.date) == current_month,
            func.extract('year', Expense.date) == current_year
        ).scalar() or 0

    # Get user's monthly budget
    monthly_budget = current_user.monthly_budget or 0
    
    # Calculate budget progress
    if monthly_budget > 0:
        budget_progress = min(100, round((current_month_expenses / monthly_budget) * 100))
    else:
        budget_progress = 0
        
    # Calculate monthly trend (compared to previous month)
    previous_month = current_month - 1 if current_month > 1 else 12
    previous_year = current_year if current_month > 1 else current_year - 1
    
    previous_month_expenses = db.session.query(func.sum(Expense.amount))\
        .filter(
            Expense.user_id == current_user.id,
            func.extract('month', Expense.date) == previous_month,
            func.extract('year', Expense.date) == previous_year
        ).scalar() or 0
    
    if previous_month_expenses > 0:
        monthly_trend = ((current_month_expenses - previous_month_expenses) / previous_month_expenses) * 100
    else:
        monthly_trend = 0
    
    return render_template('dashboard.html',
                         user=current_user,
                         chart_categories=chart_categories,
                         chart_amounts=chart_amounts,
                         daily_expenses=daily_expenses,
                         recent_expenses=recent_expenses,
                         total_expenses=total_expenses,
                         monthly_average=monthly_average,
                         budget_progress=budget_progress,
                         current_month_expenses=current_month_expenses,
                         monthly_trend=monthly_trend,
                         colors=colors)

@views.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@views.route('/expenses')
@login_required
def expenses():
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of items per page
    
    # Get filter parameters
    selected_category = request.args.get('category', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Build the query
    query = Expense.query.filter_by(user_id=current_user.id)
    
    # Apply filters if they exist
    if selected_category:
        query = query.filter_by(category_id=selected_category)
    if start_date:
        query = query.filter(Expense.date >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        query = query.filter(Expense.date <= datetime.strptime(end_date, '%Y-%m-%d'))
    
    # Calculate statistics for all matching expenses (before pagination)
    total_amount = db.session.query(func.sum(Expense.amount)).filter(query.whereclause).scalar() or 0
    expense_count = db.session.query(func.count(Expense.id)).filter(query.whereclause).scalar() or 0
    average_amount = total_amount / expense_count if expense_count > 0 else 0
    
    # Order by date descending and paginate
    pagination = query.order_by(Expense.date.desc()).paginate(page=page, per_page=per_page)
    expenses = pagination.items
    
    # Get all categories for the filter dropdown
    categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.name).all()
    
    return render_template('expenses.html', 
                         user=current_user, 
                         expenses=expenses, 
                         pagination=pagination,
                         categories=categories,
                         selected_category=selected_category,
                         start_date=start_date,
                         end_date=end_date,
                         total_amount=total_amount,
                         average_amount=average_amount,
                         expense_count=expense_count)

@views.route('/categories')
@login_required
def categories():
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('categories.html', user=current_user, categories=categories)

@views.route('/budgets')
@login_required
def budgets():
    budgets = Budget.query.filter_by(user_id=current_user.id).all()
    return render_template('budgets.html', user=current_user, budgets=budgets)

@views.route('/add-expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        try:
            amount = float(request.form.get('amount'))
            currency = request.form.get('currency')
            category_id = request.form.get('category')
            date = datetime.strptime(request.form.get('date'), '%Y-%m-%d')
            description = request.form.get('description')

            new_expense = Expense(
                amount=amount,
                currency=currency,
                category_id=category_id,
                date=date,
                description=description,
                user_id=current_user.id
            )

            db.session.add(new_expense)
            db.session.commit()
            flash('Expense added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error adding expense: ' + str(e), 'error')
        return redirect(url_for('views.expenses'))

    # Get user's categories
    categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.name).all()
    
    # If user has no categories, add default ones
    if not categories:
        try:
            # Default categories
            default_categories = [
                {'name': 'Food & Dining', 'color': '#FF6B6B', 'icon': 'fas fa-utensils'},
                {'name': 'Transportation', 'color': '#4ECDC4', 'icon': 'fas fa-car'},
                {'name': 'Shopping', 'color': '#45B7D1', 'icon': 'fas fa-shopping-bag'},
                {'name': 'Entertainment', 'color': '#96CEB4', 'icon': 'fas fa-film'},
                {'name': 'Housing', 'color': '#FFEEAD', 'icon': 'fas fa-home'},
                {'name': 'Utilities', 'color': '#D4A5A5', 'icon': 'fas fa-bolt'},
                {'name': 'Healthcare', 'color': '#9B6B6B', 'icon': 'fas fa-medkit'},
                {'name': 'Education', 'color': '#A8E6CF', 'icon': 'fas fa-graduation-cap'},
                {'name': 'Personal Care', 'color': '#FFB6B9', 'icon': 'fas fa-heart'},
                {'name': 'Travel', 'color': '#957DAD', 'icon': 'fas fa-plane'}
            ]
            
            for cat in default_categories:
                new_category = Category(
                    name=cat['name'],
                    color=cat['color'],
                    icon=cat['icon'],
                    user_id=current_user.id
                )
                db.session.add(new_category)
            db.session.commit()
            
            # Refresh categories after adding defaults
            categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.name).all()
            flash('Default categories have been added for you!', 'success')
        except Exception as e:
            db.session.rollback()
            print(f"Error adding default categories: {e}")
            flash('Error adding default categories. Please try again.', 'error')
    
    today = datetime.today()
    
    return render_template(
        'add_expense.html',
        user=current_user,
        categories=categories,
        today=today,
        currencies=CURRENCIES
    )

@views.route('/add-category', methods=['GET', 'POST'])
@login_required
def add_category():
    if request.method == 'POST':
        name = request.form.get('name')
        color = request.form.get('color')
        icon = request.form.get('icon')
        
        new_category = Category(
            name=name,
            color=color,
            icon=icon,
            user_id=current_user.id
        )
        
        try:
            db.session.add(new_category)
            db.session.commit()
            flash('Category added successfully!', 'success')
            return redirect(url_for('views.categories'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while adding the category.', 'error')
            return redirect(url_for('views.add_category'))
    
    return render_template('add_category.html', user=current_user)

@views.route('/add-budget', methods=['GET', 'POST'])
@login_required
def add_budget():
    if request.method == 'POST':
        amount = float(request.form.get('amount'))
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
        end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')
        category_id = request.form.get('category')
        
        new_budget = Budget(
            amount=amount,
            start_date=start_date,
            end_date=end_date,
            user_id=current_user.id,
            category_id=category_id if category_id else None
        )
        
        try:
            db.session.add(new_budget)
            db.session.commit()
            flash('Budget added successfully!', 'success')
            return redirect(url_for('views.budgets'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while adding the budget.', 'error')
            return redirect(url_for('views.add_budget'))
    
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('add_budget.html', user=current_user, categories=categories)

@views.route('/quick-access', methods=['GET', 'POST'])
@login_required
def quick_access():
    if request.method == 'POST':
        amount = float(request.form.get('amount'))
        category_id = request.form.get('category')
        description = request.form.get('description')
        date = datetime.strptime(request.form.get('date'), '%Y-%m-%d')
        currency = request.form.get('currency')
        
        new_expense = Expense(
            amount=amount,
            description=description,
            date=date,
            user_id=current_user.id,
            category_id=category_id if category_id else None,
            original_currency=currency
        )
        
        try:
            db.session.add(new_expense)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error: {e}")
            flash('An error occurred while adding the expense.', 'error')
        
        flash('Expense added successfully!', 'success')
        return redirect(url_for('views.quick_access'))
    
    # Get user's categories
    categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.name).all()
    
    # Get recent expenses (last 5)
    recent_expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).limit(5).all()
    
    # Get today's date
    today = datetime.utcnow()
    
    # Comprehensive list of currencies with symbols
    currencies = [
        ('USD', 'US Dollar ($)'),
        ('EUR', 'Euro (€)'),
        ('GBP', 'British Pound (£)'),
        ('JPY', 'Japanese Yen (¥)'),
        ('AUD', 'Australian Dollar (A$)'),
        ('CAD', 'Canadian Dollar (C$)'),
        ('CHF', 'Swiss Franc (Fr)'),
        ('CNY', 'Chinese Yuan (¥)'),
        ('INR', 'Indian Rupee (₹)'),
        ('NZD', 'New Zealand Dollar (NZ$)'),
        ('SGD', 'Singapore Dollar (S$)'),
        ('HKD', 'Hong Kong Dollar (HK$)'),
        ('SEK', 'Swedish Krona (kr)'),
        ('KRW', 'South Korean Won (₩)'),
        ('ZAR', 'South African Rand (R)'),
        ('BRL', 'Brazilian Real (R$)'),
        ('MXN', 'Mexican Peso (Mex$)'),
        ('AED', 'UAE Dirham (د.إ)'),
        ('SAR', 'Saudi Riyal (﷼)'),
        ('RUB', 'Russian Ruble (₽)')
    ]
    
    # Default categories if user has none
    default_categories = [
        {'name': 'Food & Dining', 'color': '#FF6B6B', 'icon': 'fas fa-utensils'},
        {'name': 'Transportation', 'color': '#4ECDC4', 'icon': 'fas fa-car'},
        {'name': 'Shopping', 'color': '#45B7D1', 'icon': 'fas fa-shopping-bag'},
        {'name': 'Entertainment', 'color': '#96CEB4', 'icon': 'fas fa-film'},
        {'name': 'Housing', 'color': '#FFEEAD', 'icon': 'fas fa-home'},
        {'name': 'Utilities', 'color': '#D4A5A5', 'icon': 'fas fa-bolt'},
        {'name': 'Healthcare', 'color': '#9B6B6B', 'icon': 'fas fa-medkit'},
        {'name': 'Education', 'color': '#A8E6CF', 'icon': 'fas fa-graduation-cap'},
        {'name': 'Personal Care', 'color': '#FFB6B9', 'icon': 'fas fa-heart'},
        {'name': 'Travel', 'color': '#957DAD', 'icon': 'fas fa-plane'}
    ]
    
    # If user has no categories, add default ones
    if not categories:
        try:
            for cat in default_categories:
                new_category = Category(
                    name=cat['name'],
                    color=cat['color'],
                    icon=cat['icon'],
                    user_id=current_user.id
                )
                db.session.add(new_category)
            db.session.commit()
            categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.name).all()
            flash('Default categories have been added for you!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error adding default categories.', 'error')
    
    return render_template(
        "quick_access.html",
        user=current_user,
        categories=categories,
        recent_expenses=recent_expenses,
        today=today,
        currencies=currencies
    )

@views.route('/set-theme', methods=['POST'])
@login_required
def set_theme():
    data = request.get_json()
    theme = data.get('theme', 'light')
    
    # Update session
    session['theme'] = theme
    
    # Update user's theme preference in database
    if current_user.is_authenticated:
        current_user.theme = theme
        db.session.commit()
    
    return jsonify({'status': 'success'})

@views.route('/monthly-report')
@login_required
def monthly_report():
    # Get selected month and year from query parameters
    selected_month = request.args.get('month', datetime.now().month, type=int)
    selected_year = request.args.get('year', datetime.now().year, type=int)

    # Get all expenses for the selected month
    start_date = datetime(selected_year, selected_month, 1)
    if selected_month == 12:
        end_date = datetime(selected_year + 1, 1, 1)
    else:
        end_date = datetime(selected_year, selected_month + 1, 1)

    expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= start_date,
        Expense.date < end_date
    ).order_by(Expense.date.desc()).all()

    # Calculate statistics
    total_expenses = sum(expense.amount for expense in expenses)
    total_transactions = len(expenses)
    
    # Calculate average daily expense
    days_in_month = (end_date - start_date).days
    avg_daily_expense = total_expenses / days_in_month if days_in_month > 0 else 0
    
    # Calculate highest daily expense
    daily_expenses = {}
    for expense in expenses:
        date_key = expense.date.date()
        daily_expenses[date_key] = daily_expenses.get(date_key, 0) + expense.amount
    max_daily_expense = max(daily_expenses.values()) if daily_expenses else 0

    # Prepare data for charts
    daily_labels = []
    daily_values = []
    current_date = start_date
    while current_date < end_date:
        date_key = current_date.date()
        daily_labels.append(date_key.strftime('%d %b'))
        daily_values.append(daily_expenses.get(date_key, 0))
        current_date += timedelta(days=1)

    # Get category distribution
    category_totals = {}
    for expense in expenses:
        category_name = expense.category.name if expense.category else 'Uncategorized'
        category_totals[category_name] = category_totals.get(category_name, 0) + expense.amount
    
    category_labels = list(category_totals.keys())
    category_values = list(category_totals.values())

    # Prepare month/year selection options
    months = [(i, calendar.month_name[i]) for i in range(1, 13)]
    years = range(datetime.now().year - 2, datetime.now().year + 1)

    return render_template('monthly_report.html',
        user=current_user,
        expenses=expenses,
        total_expenses=total_expenses,
        avg_daily_expense=avg_daily_expense,
        max_daily_expense=max_daily_expense,
        total_transactions=total_transactions,
        daily_labels=daily_labels,
        daily_values=daily_values,
        category_labels=category_labels,
        category_values=category_values,
        months=months,
        years=years,
        selected_month=selected_month,
        selected_year=selected_year
    )

@views.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        # Update user settings
        current_user.first_name = request.form.get('first_name', current_user.first_name)
        current_user.email = request.form.get('email', current_user.email)
        current_user.currency = request.form.get('currency', current_user.currency)
        current_user.monthly_budget = float(request.form.get('monthly_budget', current_user.monthly_budget))
        current_user.theme = request.form.get('theme', current_user.theme)
        
        # Handle password change if provided
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if current_password and new_password and confirm_password:
            if check_password_hash(current_user.password, current_password):
                if new_password == confirm_password:
                    if is_strong_password(new_password):
                        current_user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
                        flash('Password updated successfully!', 'success')
                    else:
                        flash('New password must be at least 8 characters and contain uppercase, lowercase, and numbers.', 'error')
                else:
                    flash('New passwords do not match.', 'error')
            else:
                flash('Current password is incorrect.', 'error')
        
        try:
            db.session.commit()
            flash('Settings updated successfully!', 'success')
            return redirect(url_for('views.settings'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating settings.', 'error')
    
    return render_template('settings.html', user=current_user)

@views.route('/edit-expense/<int:expense_id>', methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    
    # Ensure user can only edit their own expenses
    if expense.user_id != current_user.id:
        flash('You do not have permission to edit this expense.', 'error')
        return redirect(url_for('views.expenses'))
    
    if request.method == 'POST':
        try:
            expense.amount = float(request.form.get('amount'))
            expense.currency = request.form.get('currency')
            expense.category_id = request.form.get('category')
            expense.date = datetime.strptime(request.form.get('date'), '%Y-%m-%d')
            expense.description = request.form.get('description')
            
            db.session.commit()
            flash('Expense updated successfully!', 'success')
            return redirect(url_for('views.expenses'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the expense.', 'error')
            return redirect(url_for('views.edit_expense', expense_id=expense_id))
    
    categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.name).all()
    
    return render_template(
        'edit_expense.html',
        user=current_user,
        expense=expense,
        categories=categories,
        currencies=CURRENCIES
    )

@views.route('/delete-expense/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    
    # Ensure user can only delete their own expenses
    if expense.user_id != current_user.id:
        flash('You do not have permission to delete this expense.', 'error')
        return redirect(url_for('views.expenses'))
    
    try:
        db.session.delete(expense)
        db.session.commit()
        flash('Expense deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the expense.', 'error')
    
    return redirect(url_for('views.expenses'))