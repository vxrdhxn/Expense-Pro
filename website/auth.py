from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
from .models import User
from . import db
import re
import sys
import traceback
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError, TimeoutError
import time

auth = Blueprint('auth', __name__)

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def try_db_operation(operation, max_retries=3):
    """Helper function to retry database operations"""
    retry_delay = 1
    last_error = None
    
    for attempt in range(max_retries):
        try:
            result = operation()
            db.session.commit()
            return result
        except OperationalError as e:
            last_error = e
            print(f"Database operation attempt {attempt + 1} failed: {str(e)}", file=sys.stderr)
            db.session.rollback()
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...", file=sys.stderr)
                time.sleep(retry_delay)
                retry_delay *= 2
        except SQLAlchemyError as e:
            print(f"Database error: {str(e)}", file=sys.stderr)
            db.session.rollback()
            raise
    
    if last_error:
        raise last_error

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            password = request.form.get('password')
            remember = request.form.get('remember', False)

            if not email or not password:
                flash('Please fill in all fields.', category='error')
                return render_template("login.html", user=current_user)

            user = User.query.filter_by(email=email).first()
            
            if user:
                if user.verify_password(password):
                    flash('Logged in successfully!', category='success')
                    login_user(user, remember=remember)
                    return redirect(url_for('views.home'))
                else:
                    flash('Incorrect password.', category='error')
            else:
                flash('Email does not exist.', category='error')

        except TimeoutError:
            flash('Request timed out. Please try again.', category='error')
        except SQLAlchemyError as e:
            print(f"Database error in login: {str(e)}")
            flash('An error occurred while logging in. Please try again.', category='error')
        except Exception as e:
            print(f"Error in login: {str(e)}")
            flash('An unexpected error occurred. Please try again.', category='error')

    return render_template("login.html", user=current_user)

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            first_name = request.form.get('first-name')
            last_name = request.form.get('last-name')
            password = request.form.get('password')
            terms = request.form.get('terms')

            # Validate all required fields are present
            if not all([email, first_name, last_name, password, terms]):
                flash('Please fill in all fields and accept the terms.', category='error')
                return render_template("sign_up.html", user=current_user)

            # Validate email format
            if not is_valid_email(email):
                flash('Invalid email format.', category='error')
                return render_template("sign_up.html", user=current_user)

            # Check if email already exists
            user = User.query.filter_by(email=email).first()
            if user:
                flash('Email already exists.', category='error')
                return render_template("sign_up.html", user=current_user)

            # Validate password length
            if len(password) < 7:
                flash('Password must be at least 7 characters.', category='error')
                return render_template("sign_up.html", user=current_user)

            # Validate name lengths
            if len(first_name) < 2 or len(last_name) < 2:
                flash('First and last name must be at least 2 characters.', category='error')
                return render_template("sign_up.html", user=current_user)

            # Create new user
            new_user = User(
                email=email,
                first_name=first_name,
                last_name=last_name
            )
            new_user.password = password  # This will use the password setter to hash

            # Add user to database with retry logic
            max_retries = 3
            retry_count = 0
            while retry_count < max_retries:
                try:
                    db.session.add(new_user)
                    db.session.commit()
                    login_user(new_user, remember=True)
                    flash('Account created successfully!', category='success')
                    return redirect(url_for('views.home'))
                except SQLAlchemyError as e:
                    db.session.rollback()
                    retry_count += 1
                    if retry_count == max_retries:
                        print(f"Database error in sign_up after {max_retries} retries: {str(e)}")
                        flash('An error occurred while creating your account. Please try again.', category='error')
                    time.sleep(0.5)  # Wait before retrying

        except TimeoutError:
            flash('Request timed out. Please try again.', category='error')
        except Exception as e:
            print(f"Error in sign_up: {str(e)}")
            flash('An unexpected error occurred. Please try again.', category='error')

    return render_template("sign_up.html", user=current_user)

@auth.route('/logout')
@login_required
def logout():
    try:
        logout_user()
        flash('Logged out successfully!', category='success')
    except Exception as e:
        print(f"Error in logout: {str(e)}")
        flash('An error occurred while logging out.', category='error')
    return redirect(url_for('auth.login'))

@auth.route('/check-email', methods=['POST'])
def check_email():
    try:
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({'error': 'No email provided'}), 400
            
        email = data['email']
        
        if not is_valid_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
            
        # Add a small delay to prevent brute force attempts
        time.sleep(0.1)
        
        user = User.query.filter_by(email=email).first()
        return jsonify({'exists': user is not None})
        
    except Exception as e:
        print(f"Error in check_email: {str(e)}")
        return jsonify({'error': 'An error occurred while checking email'}), 500



