from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
from .models import User
from . import db
import re
import sys
import traceback
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
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
    try:
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            
            if not email or not password:
                flash('Please fill in all fields', category='error')
                return render_template("login.html", user=None)
            
            try:
                user = User.query.filter_by(email=email).first()
            except SQLAlchemyError as e:
                print(f"Database error during login: {str(e)}", file=sys.stderr)
                flash('An error occurred while accessing the database. Please try again.', category='error')
                return render_template("login.html", user=None)
            
            if user:
                if user.verify_password(password):
                    try:
                        login_user(user, remember=True)
                        flash('Logged in successfully!', category='success')
                        return redirect(url_for('views.home'))
                    except Exception as e:
                        print(f"Error during login_user: {str(e)}", file=sys.stderr)
                        flash('An error occurred during login. Please try again.', category='error')
                else:
                    flash('Incorrect password, try again.', category='error')
            else:
                flash('Email does not exist.', category='error')
        
        return render_template("login.html", user=None)
    except Exception as e:
        print(f"Unexpected error in login route: {str(e)}", file=sys.stderr)
        print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
        flash('An unexpected error occurred. Please try again.', category='error')
        return render_template("login.html", user=None)

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    try:
        if request.method == 'POST':
            email = request.form.get('email')
            first_name = request.form.get('first-name')
            last_name = request.form.get('last-name')
            password = request.form.get('password')
            terms = request.form.get('terms')
            
            print(f"Sign-up attempt for email: {email}", file=sys.stderr)
            print(f"Form data received - first_name: {bool(first_name)}, last_name: {bool(last_name)}, email: {bool(email)}, password: {bool(password)}, terms: {bool(terms)}", file=sys.stderr)
            
            if not all([email, first_name, last_name, password, terms]):
                flash('Please fill in all fields and accept the terms', category='error')
                return render_template("sign_up.html", user=None)
            
            if not is_valid_email(email):
                flash('Please enter a valid email address', category='error')
                return render_template("sign_up.html", user=None)
            
            try:
                existing_user = User.query.filter_by(email=email).first()
                if existing_user:
                    flash('Email already exists.', category='error')
                    return render_template("sign_up.html", user=None)
                
                # Create new user
                new_user = User(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=password  # This will use the password setter
                )
                db.session.add(new_user)
                db.session.commit()
                
                # Log in the new user
                login_user(new_user, remember=True)
                
                flash('Account created successfully!', category='success')
                print(f"User created successfully: {email}", file=sys.stderr)
                return redirect(url_for('views.home'))
                
            except IntegrityError as e:
                db.session.rollback()
                print(f"Database integrity error: {str(e)}", file=sys.stderr)
                flash('This email is already registered.', category='error')
            except SQLAlchemyError as e:
                db.session.rollback()
                print(f"Database error creating new user: {str(e)}", file=sys.stderr)
                print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
                flash('An error occurred while creating your account. Please try again.', category='error')
            except Exception as e:
                db.session.rollback()
                print(f"Unexpected error creating user: {str(e)}", file=sys.stderr)
                print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
                flash('An unexpected error occurred. Please try again.', category='error')
        
        return render_template("sign_up.html", user=None)
    except Exception as e:
        print(f"Unexpected error in sign-up route: {str(e)}", file=sys.stderr)
        print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
        flash('An unexpected error occurred. Please try again.', category='error')
        return render_template("sign_up.html", user=None)

@auth.route('/logout')
@login_required
def logout():
    try:
        logout_user()
        flash('Logged out successfully!', category='success')
        return redirect(url_for('auth.login'))
    except Exception as e:
        print(f"Error during logout: {str(e)}", file=sys.stderr)
        flash('An error occurred during logout.', category='error')
        return redirect(url_for('views.home'))

@auth.route('/check-email', methods=['POST'])
def check_email():
    try:
        data = request.get_json()
        if not data or 'email' not in data:
            return jsonify({'error': 'No email provided'}), 400
            
        email = data['email']
        if not is_valid_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
            
        user = User.query.filter_by(email=email).first()
        return jsonify({'exists': user is not None})
    except SQLAlchemyError as e:
        print(f"Database error checking email: {str(e)}", file=sys.stderr)
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        print(f"Error checking email: {str(e)}", file=sys.stderr)
        print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
        return jsonify({'error': 'Server error'}), 500



