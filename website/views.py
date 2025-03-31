from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from .models import Expense, User, SUPPORTED_CURRENCIES
from . import db
from datetime import datetime, timedelta
from .utils import convert_currency, format_currency
from dateutil.relativedelta import relativedelta
from werkzeug.security import check_password_hash

views = Blueprint('views', __name__)

@views.route('/')
@login_required
def home():
    return render_template("home.html", user=current_user)

@views.route('/quick_access', methods=['GET', 'POST'])
@login_required
def quick_access():
    if request.method == 'POST':
        amount = request.form.get('amount')
        category = request.form.get('category')
        description = request.form.get('description')
        currency = request.form.get('currency', current_user.currency)

        if not amount or not category or not description:
            flash('All fields are required!', category='error')
        else:
            try:
                original_amount = float(amount)
                # Convert to user's preferred currency if different
                converted_amount = convert_currency(original_amount, currency, current_user.currency)
                
                new_expense = Expense(
                    amount=converted_amount,
                    original_amount=original_amount,
                    original_currency=currency,
                    category=category,
                    description=description,
                    date=datetime.now(),
                    user_id=current_user.id
                )
                db.session.add(new_expense)
                db.session.commit()
                flash('Expense added successfully!', category='success')
                return redirect(url_for('views.quick_access'))
            except ValueError:
                flash('Invalid amount!', category='error')

    # Get recent transactions
    recent_transactions = Expense.query.filter_by(user_id=current_user.id)\
        .order_by(Expense.date.desc())\
        .limit(5)\
        .all()

    return render_template(
        "quick_access.html",
        user=current_user,
        transactions=recent_transactions,
        supported_currencies=SUPPORTED_CURRENCIES
    )

@views.route('/monthly-report')
@views.route('/monthly_report')  # Add support for underscore version
@login_required
def monthly_report():
    # Get selected month or default to current month
    selected_month = request.args.get('month')
    if selected_month:
        selected_month = datetime.strptime(selected_month, '%Y-%m')
    else:
        selected_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Calculate first and last day of selected month
    first_day = selected_month.replace(day=1)
    if selected_month.month == 12:
        last_day = selected_month.replace(year=selected_month.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last_day = selected_month.replace(month=selected_month.month + 1, day=1) - timedelta(days=1)

    # Get all expenses for the selected month
    expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= first_day,
        Expense.date <= last_day
    ).all()

    # Calculate total expenses
    total_expenses = sum(expense.amount for expense in expenses)

    # Calculate daily expenses
    daily_expenses = {}
    for expense in expenses:
        date_str = expense.date.strftime('%Y-%m-%d')
        if date_str in daily_expenses:
            daily_expenses[date_str] += expense.amount
        else:
            daily_expenses[date_str] = expense.amount

    # Fill in missing days with zero expenses
    current_date = first_day
    while current_date <= last_day:
        date_str = current_date.strftime('%Y-%m-%d')
        if date_str not in daily_expenses:
            daily_expenses[date_str] = 0
        current_date += timedelta(days=1)

    # Calculate category totals
    category_totals = {}
    for expense in expenses:
        if expense.category in category_totals:
            category_totals[expense.category] += expense.amount
        else:
            category_totals[expense.category] = expense.amount

    # Calculate average daily expense
    days_in_month = (last_day - first_day).days + 1
    average_daily = total_expenses / days_in_month if total_expenses > 0 else 0

    # Find highest spending category
    highest_category = max(category_totals.items(), key=lambda x: x[1])[0] if category_totals else None

    # Get list of last 12 months for the dropdown
    months = []
    current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    for i in range(12):
        months.append(current_month - relativedelta(months=i))

    return render_template(
        'monthly_report.html',
        user=current_user,
        selected_month=selected_month,
        months=months,
        total_expenses=total_expenses,
        average_daily=average_daily,
        highest_category=highest_category,
        category_totals=category_totals,
        daily_expenses=daily_expenses
    )

@views.route('/expenses')
@login_required
def expenses():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get filter parameters
    date_range = request.args.get('date_range', 'all')
    category = request.args.get('category', 'all')
    sort_by = request.args.get('sort_by', 'date-desc')
    search = request.args.get('search', '')
    
    # Base query
    query = Expense.query.filter_by(user_id=current_user.id)
    
    # Apply filters
    if date_range != 'all':
        if date_range == 'today':
            query = query.filter(db.func.date(Expense.date) == db.func.date(datetime.now()))
        elif date_range == 'week':
            query = query.filter(Expense.date >= datetime.now() - timedelta(days=7))
        elif date_range == 'month':
            query = query.filter(Expense.date >= datetime.now() - timedelta(days=30))
        elif date_range == 'year':
            query = query.filter(Expense.date >= datetime.now() - timedelta(days=365))
    
    if category != 'all':
        query = query.filter(Expense.category == category)
    
    if search:
        query = query.filter(Expense.description.ilike(f'%{search}%'))
    
    # Apply sorting
    if sort_by == 'date-desc':
        query = query.order_by(Expense.date.desc())
    elif sort_by == 'date-asc':
        query = query.order_by(Expense.date.asc())
    elif sort_by == 'amount-desc':
        query = query.order_by(Expense.amount.desc())
    elif sort_by == 'amount-asc':
        query = query.order_by(Expense.amount.asc())
    
    # Paginate results
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template(
        "expenses.html",
        user=current_user,
        expenses=pagination.items,
        pagination=pagination,
        date_range=date_range,
        category=category,
        sort_by=sort_by,
        search=search,
        format_currency=format_currency,
        supported_currencies=SUPPORTED_CURRENCIES
    )

@views.route('/expenses/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_expense(id):
    expense = Expense.query.get_or_404(id)
    if expense.user_id != current_user.id:
        flash('Access denied.', category='error')
        return redirect(url_for('views.expenses'))
        
    if request.method == 'POST':
        amount = request.form.get('amount')
        category = request.form.get('category')
        description = request.form.get('description')
        currency = request.form.get('currency', expense.original_currency)
        
        if not amount or not category or not description:
            flash('All fields are required!', category='error')
        else:
            try:
                original_amount = float(amount)
                # Convert to user's preferred currency if different
                converted_amount = convert_currency(original_amount, currency, current_user.currency)
                
                expense.amount = converted_amount
                expense.original_amount = original_amount
                expense.original_currency = currency
                expense.category = category
                expense.description = description
                db.session.commit()
                flash('Expense updated successfully!', category='success')
                return redirect(url_for('views.expenses'))
            except ValueError:
                flash('Invalid amount!', category='error')
    
    return render_template(
        "edit_expense.html",
        user=current_user,
        expense=expense,
        supported_currencies=SUPPORTED_CURRENCIES
    )

@views.route('/expenses/delete/<int:id>', methods=['DELETE'])
@login_required
def delete_expense(id):
    expense = Expense.query.get_or_404(id)
    if expense.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    db.session.delete(expense)
    db.session.commit()
    return jsonify({'success': True})

@views.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        
        if form_type == 'profile':
            current_user.first_name = request.form.get('first_name')
            current_user.last_name = request.form.get('last_name')
            current_user.email = request.form.get('email')
            current_user.currency = request.form.get('currency')
            db.session.commit()
            flash('Profile updated successfully!', category='success')
            
        elif form_type == 'password':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if not current_user.check_password(current_password):
                flash('Current password is incorrect!', category='error')
            elif new_password != confirm_password:
                flash('New passwords do not match!', category='error')
            else:
                current_user.set_password(new_password)
                db.session.commit()
                flash('Password updated successfully!', category='success')
                
        elif form_type == 'preferences':
            current_user.email_notifications = bool(request.form.get('email_notifications'))
            current_user.monthly_report = bool(request.form.get('monthly_report'))
            current_user.default_view = request.form.get('default_view')
            db.session.commit()
            flash('Preferences updated successfully!', category='success')
    
    return render_template("settings.html", user=current_user)

@views.route('/settings/update-profile', methods=['POST'])
@login_required
def update_profile():
    if request.method == 'POST':
        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')
        email = request.form.get('email')
        
        if not first_name or not last_name or not email:
            flash('All fields are required!', category='error')
            return redirect(url_for('views.settings'))
        
        # Check if email is already taken by another user
        existing_user = User.query.filter(User.email == email, User.id != current_user.id).first()
        if existing_user:
            flash('Email is already taken!', category='error')
            return redirect(url_for('views.settings'))
        
        current_user.first_name = first_name
        current_user.last_name = last_name
        current_user.email = email
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', category='success')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating your profile.', category='error')
            
    return redirect(url_for('views.settings'))

@views.route('/settings/update-currency', methods=['POST'])
@login_required
def update_currency():
    if request.method == 'POST':
        currency = request.form.get('currency')
        
        if not currency or currency not in SUPPORTED_CURRENCIES:
            flash('Please select a valid currency!', category='error')
            return redirect(url_for('views.settings'))
        
        current_user.currency = currency
        
        try:
            db.session.commit()
            flash('Currency updated successfully!', category='success')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating your currency.', category='error')
            
    return redirect(url_for('views.settings'))

@views.route('/settings/change-password', methods=['POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('currentPassword')
        new_password = request.form.get('newPassword')
        confirm_password = request.form.get('confirmPassword')
        
        if not current_password or not new_password or not confirm_password:
            flash('All fields are required!', category='error')
            return redirect(url_for('views.settings'))
            
        if not current_user.check_password(current_password):
            flash('Current password is incorrect!', category='error')
            return redirect(url_for('views.settings'))
            
        if new_password != confirm_password:
            flash('New passwords do not match!', category='error')
            return redirect(url_for('views.settings'))
            
        if len(new_password) < 6:
            flash('Password must be at least 6 characters long!', category='error')
            return redirect(url_for('views.settings'))
        
        current_user.set_password(new_password)
        
        try:
            db.session.commit()
            flash('Password updated successfully!', category='success')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating your password.', category='error')
            
    return redirect(url_for('views.settings'))

@views.route('/settings/delete-account', methods=['POST'])
@login_required
def delete_account():
    if request.method == 'POST':
        confirm_delete = request.form.get('confirmDelete')
        
        if confirm_delete != 'DELETE':
            flash('Please type DELETE to confirm account deletion!', category='error')
            return redirect(url_for('views.settings'))
        
        try:
            # Delete all user's expenses
            Expense.query.filter_by(user_id=current_user.id).delete()
            # Delete user
            db.session.delete(current_user)
            db.session.commit()
            flash('Your account has been deleted successfully.', category='success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while deleting your account.', category='error')
            
    return redirect(url_for('views.settings'))

@views.route('/test-db')
def test_db():
    try:
        db.session.execute('SELECT 1')
        return 'Database connection successful!'
    except Exception as e:
        return f'Database connection failed: {str(e)}'