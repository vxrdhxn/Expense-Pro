from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
from .models import User
from . import db
import re
import sys

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
            if user.verify_password(password):
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
    try:
        if request.method == 'POST':
            # Get form data
            email = request.form.get('email')
            first_name = request.form.get('first-name')
            last_name = request.form.get('last-name')
            password = request.form.get('password')
            terms = request.form.get('terms')

            print(f"Form data received - Email: {email}, First Name: {first_name}, Last Name: {last_name}, Terms: {terms}", file=sys.stderr)

            # Input validation
            if not all([email, first_name, last_name, password]):
                missing_fields = []
                if not email: missing_fields.append("email")
                if not first_name: missing_fields.append("first name")
                if not last_name: missing_fields.append("last name")
                if not password: missing_fields.append("password")
                flash(f'Missing required fields: {", ".join(missing_fields)}', category='error')
                return render_template("sign_up.html", user=current_user)

            if not terms:
                flash('Please accept the Terms & Conditions.', category='error')
                return render_template("sign_up.html", user=current_user)

            if not is_valid_email(email):
                flash('Please enter a valid email address.', category='error')
                return render_template("sign_up.html", user=current_user)

            if len(first_name) < 2:
                flash('First name must be greater than 1 character.', category='error')
                return render_template("sign_up.html", user=current_user)

            if len(last_name) < 2:
                flash('Last name must be greater than 1 character.', category='error')
                return render_template("sign_up.html", user=current_user)

            if len(password) < 7:
                flash('Password must be at least 7 characters.', category='error')
                return render_template("sign_up.html", user=current_user)

            try:
                # Check if user already exists
                existing_user = User.query.filter_by(email=email).first()
                if existing_user:
                    flash('Email already exists.', category='error')
                    return render_template("sign_up.html", user=current_user)

                # Create new user
                new_user = User(
                    email=email,
                    first_name=first_name,
                    last_name=last_name
                )
                new_user.password = password  # This will use the password property setter

                # Add to database
                db.session.add(new_user)
                db.session.commit()
                
                # Log in the new user
                login_user(new_user, remember=True)
                flash('Account created successfully!', category='success')
                return redirect(url_for('views.home'))

            except Exception as e:
                db.session.rollback()
                print(f"Database error during user creation: {str(e)}", file=sys.stderr)
                flash('An error occurred while creating your account. Please try again.', category='error')
                return render_template("sign_up.html", user=current_user)

    except Exception as e:
        print(f"Unexpected error in sign_up route: {str(e)}", file=sys.stderr)
        return jsonify({'error': 'Internal Server Error', 'details': str(e)}), 500

    return render_template("sign_up.html", user=current_user)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', category='success')
    return redirect(url_for('auth.login'))



