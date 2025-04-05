from flask import Flask, jsonify, render_template, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from datetime import datetime
import os
import sys
import traceback
from dotenv import load_dotenv
from sqlalchemy.pool import NullPool
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError, OperationalError, TimeoutError
import urllib.parse
import time
from os import path

load_dotenv()

db = SQLAlchemy()
DB_NAME = "database.db"

def create_app():
    app = Flask(__name__)
    
    # Basic configuration
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev')
    
    # Configure static files for serverless
    app.config['STATIC_FOLDER'] = None  # Disable automatic static serving
    
    # Database configuration with detailed logging
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("No DATABASE_URL environment variable set", file=sys.stderr)
        raise ValueError("DATABASE_URL environment variable is required")
    
    print("Initializing database connection...", file=sys.stderr)
    
    # Parse and modify database URL for PostgreSQL
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        
        # Parse the URL
        parsed = urllib.parse.urlparse(database_url)
        query_dict = dict(urllib.parse.parse_qsl(parsed.query))
        
        # Add required parameters for Supabase
        query_dict.update({
            'sslmode': 'require',
            'connect_timeout': '10',
            'application_name': 'expense_pro',
            'statement_timeout': '30000',  # 30 seconds
            'idle_in_transaction_session_timeout': '30000'  # 30 seconds
        })
        
        # Reconstruct the URL with updated query parameters
        new_query = urllib.parse.urlencode(query_dict)
        database_url = urllib.parse.urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))
    
    print(f"Database URL format: {database_url.split('@')[0].split(':')[0]}://*****@{database_url.split('@')[1] if '@' in database_url else 'local'}", file=sys.stderr)
    
    # Configure SQLAlchemy for serverless environment
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'poolclass': NullPool,  # Disable connection pooling
        'connect_args': {
            'connect_timeout': 10,
            'application_name': 'expense_pro',
            'sslmode': 'require',
            'options': '-c statement_timeout=30000 -c idle_in_transaction_session_timeout=30000'
        }
    }
    
    # Initialize extensions
    db.init_app(app)
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        status = {
            'status': 'healthy',
            'checks': {
                'database': 'unknown'
            }
        }
        
        # Check database
        try:
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            status['checks']['database'] = 'connected'
        except Exception as e:
            print(f"Health check - Database failed: {str(e)}", file=sys.stderr)
            status['checks']['database'] = 'disconnected'
            status['status'] = 'unhealthy'
        
        return jsonify(status), 200 if status['status'] == 'healthy' else 500
    
    # Register blueprints
    from .views import views
    from .auth import auth
    from .settings import settings
    
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(settings, url_prefix='/')
    
    # Import models
    from .models import User, Expense
    
    # Create database
    create_database(app)
    
    # Setup login manager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(id):
        try:
            return User.query.get(int(id))
        except Exception as e:
            print(f"Error loading user {id}: {str(e)}", file=sys.stderr)
            print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
            return None
    
    @app.context_processor
    def utility_processor():
        def format_datetime(dt):
            if dt is None:
                return ""
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        return dict(format_datetime=format_datetime, now=datetime.utcnow)
    
    # Error handlers
    @app.errorhandler(500)
    def internal_error(error):
        print(f"500 error occurred: {str(error)}", file=sys.stderr)
        print(f"Error type: {type(error).__name__}", file=sys.stderr)
        print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
        
        try:
            db.session.rollback()
        except Exception as e:
            print(f"Error during session rollback: {str(e)}", file=sys.stderr)
        
        try:
            user = current_user if current_user.is_authenticated else None
        except Exception as e:
            print(f"Error getting current user: {str(e)}", file=sys.stderr)
            user = None
            
        return render_template('error.html', 
                             error=error,
                             error_type=type(error).__name__,
                             user=user), 500
    
    @app.errorhandler(404)
    def not_found_error(error):
        try:
            user = current_user if current_user.is_authenticated else None
        except:
            user = None
        return render_template('error.html', error=error, user=user), 404
    
    # Handle favicon.ico requests
    @app.route('/favicon.ico')
    def favicon():
        return '', 204  # Return no content
        
    return app

def create_database(app):
    if not path.exists('website/' + DB_NAME):
        with app.app_context():
            db.create_all()
            print('Created Database!')