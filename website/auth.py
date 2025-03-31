from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
from .models import User
from . import db
import re
import sys
import traceback
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError

auth = Blueprint('auth', __name__)

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
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
        except Exception as e:
            print(f"Error during login: {str(e)}", file=sys.stderr)
            flash('An error occurred during login. Please try again.', category='error')
    
    return render_template("login.html", user=current_user)

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        try:
            print("Processing sign-up POST request", file=sys.stderr)
            
            # Get form data
            form_data = request.form.to_dict()
            print(f"Raw form data: {form_data}", file=sys.stderr)
            
            email = request.form.get('email')
            first_name = request.form.get('first-name')
            last_name = request.form.get('last-name')
            password = request.form.get('password')
            terms = request.form.get('terms')

            print(f"Processed form data - Email: {email}, First Name: {first_name}, Last Name: {last_name}, Terms: {terms}", file=sys.stderr)

            # Input validation
            if not all([email, first_name, last_name, password]):
                missing_fields = []
                if not email: missing_fields.append("email")
                if not first_name: missing_fields.append("first name")
                if not last_name: missing_fields.append("last name")
                if not password: missing_fields.append("password")
                print(f"Missing fields: {missing_fields}", file=sys.stderr)
                flash(f'Missing required fields: {", ".join(missing_fields)}', category='error')
                return render_template("sign_up.html", user=current_user)

            if not terms:
                print("Terms not accepted", file=sys.stderr)
                flash('Please accept the Terms & Conditions.', category='error')
                return render_template("sign_up.html", user=current_user)

            if not is_valid_email(email):
                print(f"Invalid email format: {email}", file=sys.stderr)
                flash('Please enter a valid email address.', category='error')
                return render_template("sign_up.html", user=current_user)

            if len(first_name) < 2:
                print(f"First name too short: {first_name}", file=sys.stderr)
                flash('First name must be greater than 1 character.', category='error')
                return render_template("sign_up.html", user=current_user)

            if len(last_name) < 2:
                print(f"Last name too short: {last_name}", file=sys.stderr)
                flash('Last name must be greater than 1 character.', category='error')
                return render_template("sign_up.html", user=current_user)

            if len(password) < 7:
                print("Password too short", file=sys.stderr)
                flash('Password must be at least 7 characters.', category='error')
                return render_template("sign_up.html", user=current_user)

            try:
                print("Checking for existing user...", file=sys.stderr)
                # Check if user already exists
                existing_user = User.query.filter_by(email=email).first()
                if existing_user:
                    print(f"User already exists with email: {email}", file=sys.stderr)
                    flash('Email already exists.', category='error')
                    return render_template("sign_up.html", user=current_user)

                print("Creating new user...", file=sys.stderr)
                # Create new user
                new_user = User(
                    email=email,
                    first_name=first_name,
                    last_name=last_name
                )
                new_user.password = password  # This will use the password property setter

                # Add to database
                print("Adding user to database...", file=sys.stderr)
                db.session.add(new_user)
                db.session.commit()
                print("User successfully added to database", file=sys.stderr)
                
                # Log in the new user
                login_user(new_user, remember=True)
                flash('Account created successfully!', category='success')
                return redirect(url_for('views.home'))

            except IntegrityError as e:
                db.session.rollback()
                print(f"Database integrity error: {str(e)}", file=sys.stderr)
                flash('This email is already registered.', category='error')
                return render_template("sign_up.html", user=current_user)
                
            except OperationalError as e:
                db.session.rollback()
                print(f"Database operational error: {str(e)}", file=sys.stderr)
                print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
                flash('Unable to connect to the database. Please try again later.', category='error')
                return render_template("sign_up.html", user=current_user)
                
            except SQLAlchemyError as e:
                db.session.rollback()
                print(f"Database error: {str(e)}", file=sys.stderr)
                print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
                flash('An error occurred while creating your account. Please try again.', category='error')
                return render_template("sign_up.html", user=current_user)

        except Exception as e:
            print(f"Unexpected error in sign_up route: {str(e)}", file=sys.stderr)
            print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
            flash('An unexpected error occurred. Please try again.', category='error')
            return render_template("sign_up.html", user=current_user)

    return render_template("sign_up.html", user=current_user)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', category='success')
    return redirect(url_for('auth.login'))



