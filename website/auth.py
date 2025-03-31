from flask import Blueprint, render_template, request, flash, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
from .models import User
from . import db
import re

auth = Blueprint('auth', __name__)

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password_hash, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password.', category='error')
        else:
            flash('Email does not exist.', category='error')
    
    return render_template("login.html", user=current_user)

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('first-name')
        last_name = request.form.get('last-name')
        password = request.form.get('password')
        terms = request.form.get('terms')

        # Input validation
        if not email or not first_name or not last_name or not password:
            flash('Please fill in all fields.', category='error')
        elif not terms:
            flash('Please accept the Terms & Conditions.', category='error')
        elif not is_valid_email(email):
            flash('Please enter a valid email address.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(first_name) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif len(last_name) < 2:
            flash('Last name must be greater than 1 character.', category='error')
        elif len(password) < 6:
            flash('Password must be at least 7 characters.', category='error')
        else:
            # Check if user already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash('Email already exists.', category='error')
            else:
                # Create new user
                new_user = User(
                    email=email,
                    first_name=first_name,
                    last_name=last_name
                )
                new_user.set_password(password)
                try:
                    db.session.add(new_user)
                    db.session.commit()
                    login_user(new_user, remember=True)
                    flash('Account created successfully!', category='success')
                    return redirect(url_for('views.home'))
                except Exception as e:
                    db.session.rollback()
                    flash('An error occurred while creating your account.', category='error')
                    print(f"Database error: {str(e)}")

    return render_template("sign_up.html", user=current_user)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', category='success')
    return redirect(url_for('auth.login'))



