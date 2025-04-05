from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
from flask_cors import cross_origin
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
            print(f"Database error in login: {str(e)}", file=sys.stderr)
            flash('An error occurred while logging in. Please try again.', category='error')
        except Exception as e:
            print(f"Error in login: {str(e)}", file=sys.stderr)
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

            print(f"Sign-up attempt - Email: {email}, First Name: {first_name}, Last Name: {last_name}", file=sys.stderr)

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

            print("Attempting to add user to database...", file=sys.stderr)

            # Add user to database with retry logic
            max_retries = 3
            retry_count = 0
            while retry_count < max_retries:
                try:
                    db.session.add(new_user)
                    db.session.commit()
                    print("User added successfully!", file=sys.stderr)
                    login_user(new_user, remember=True)
                    flash('Account created successfully!', category='success')
                    return redirect(url_for('views.home'))
                except IntegrityError as e:
                    db.session.rollback()
                    print(f"IntegrityError in sign_up: {str(e)}", file=sys.stderr)
                    flash('Email already exists.', category='error')
                    break
                except OperationalError as e:
                    db.session.rollback()
                    retry_count += 1
                    print(f"OperationalError in sign_up (attempt {retry_count}): {str(e)}", file=sys.stderr)
                    if retry_count == max_retries:
                        flash('Database connection error. Please try again.', category='error')
                    time.sleep(0.5)
                except SQLAlchemyError as e:
                    db.session.rollback()
                    print(f"Database error in sign_up: {str(e)}", file=sys.stderr)
                    flash('An error occurred while creating your account. Please try again.', category='error')
                    break

        except Exception as e:
            print(f"Error in sign_up: {str(e)}", file=sys.stderr)
            print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
            flash('An unexpected error occurred. Please try again.', category='error')

    return render_template("sign_up.html", user=current_user)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('views.index'))

@auth.route('/check-email', methods=['POST'])
@cross_origin()
def check_email():
    try:
        # Get JSON data and log request details
        print("Received check-email request", file=sys.stderr)
        print(f"Request headers: {dict(request.headers)}", file=sys.stderr)
        print(f"Request method: {request.method}", file=sys.stderr)
        
        try:
            data = request.get_json()
            print(f"Request data: {data}", file=sys.stderr)
        except Exception as e:
            print(f"Error parsing JSON: {str(e)}", file=sys.stderr)
            return jsonify({'error': 'Invalid JSON data'}), 400
        
        if not data or 'email' not in data:
            print("No email provided in request", file=sys.stderr)
            return jsonify({'error': 'No email provided'}), 400
            
        email = data['email'].strip()
        
        if not email:
            print("Empty email provided", file=sys.stderr)
            return jsonify({'error': 'Email cannot be empty'}), 400
            
        if not is_valid_email(email):
            print(f"Invalid email format: {email}", file=sys.stderr)
            return jsonify({'error': 'Invalid email format'}), 400
            
        try:
            # Test database connection first
            db.session.execute('SELECT 1')
            db.session.commit()
            
            # Check if email exists in database
            user = User.query.filter_by(email=email).first()
            exists = user is not None
            print(f"Email check result for {email}: exists={exists}", file=sys.stderr)
            
            response = jsonify({'exists': exists})
            return response
            
        except OperationalError as e:
            print(f"Database connection error in check_email: {str(e)}", file=sys.stderr)
            db.session.rollback()
            return jsonify({'error': 'Database connection error'}), 503
        except SQLAlchemyError as e:
            print(f"Database error in check_email: {str(e)}", file=sys.stderr)
            db.session.rollback()
            return jsonify({'error': 'Database error occurred'}), 500
            
    except Exception as e:
        print(f"Unexpected error in check_email: {str(e)}", file=sys.stderr)
        print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
        return jsonify({'error': 'An unexpected error occurred'}), 500



