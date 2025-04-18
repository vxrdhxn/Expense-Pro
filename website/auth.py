from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
from . import db
from .models import User
import re
from datetime import datetime, timedelta
from .forms import SignUpForm, LoginForm
from flask import current_app

auth = Blueprint('auth', __name__)

def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def is_strong_password(password):
    """Check if password meets security requirements"""
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    return True

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('views.home'))  # Changed from dashboard to home
        
    form = LoginForm()
    if form.validate_on_submit():
        with current_app.app_context():
            user = User.query.filter_by(email=form.email.data).first()
            if user and check_password_hash(user.password_hash, form.password.data):
                login_user(user, remember=form.remember.data)
                flash('Logged in successfully!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page if next_page else url_for('views.home'))  # Changed from dashboard to home
            flash('Invalid email or password.', 'error')
    
    return render_template('login.html', form=form)

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if current_user.is_authenticated:
        return redirect(url_for('views.home'))  # Changed from dashboard to home
    
    form = SignUpForm()
    if form.validate_on_submit():
        email = form.email.data
        first_name = form.first_name.data
        password1 = form.password1.data
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        else:
            try:
                # Create new user
                new_user = User(
                    email=email,
                    first_name=first_name,
                    password_hash=generate_password_hash(password1, method='pbkdf2:sha256')
                )
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user)
                flash('Account created successfully!', category='success')
                return redirect(url_for('views.home'))  # Changed from dashboard to home
            except Exception as e:
                db.session.rollback()
                print(f"Error creating account: {str(e)}")  # Debug print
                flash('An error occurred while creating your account.', category='error')
    
    return render_template('sign_up.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', category='success')
    return redirect(url_for('auth.login'))

@auth.route('/forgot-password')
def forgot_password():
    return render_template('forgot_password.html')