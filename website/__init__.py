from flask import Flask, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from datetime import datetime
import os
import sys
import traceback
from dotenv import load_dotenv
from sqlalchemy.pool import NullPool
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError, OperationalError
import urllib.parse
import time

load_dotenv()

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # Basic configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'project123')
    
    # Database configuration
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("No DATABASE_URL environment variable set", file=sys.stderr)
        database_url = 'sqlite:///database.db'  # Fallback for development
    
    # Parse and modify database URL for PostgreSQL
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        
        # Parse the URL to add SSL mode if not present
        parsed = urllib.parse.urlparse(database_url)
        query_dict = dict(urllib.parse.parse_qsl(parsed.query))
        
        # Add SSL mode if not present
        if 'sslmode' not in query_dict:
            query_dict['sslmode'] = 'require'
        
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
        'poolclass': NullPool,
        'connect_args': {
            'connect_timeout': 30,
            'keepalives': 1,
            'keepalives_idle': 30,
            'keepalives_interval': 10,
            'keepalives_count': 5,
            'sslmode': 'require'
        } if database_url.startswith('postgresql://') else {}
    }
    
    # Initialize extensions
    db.init_app(app)
    
    # Register blueprints
    from .views import views
    from .auth import auth
    
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    
    # Import models
    from .models import User, Expense
    
    # Initialize database with retry mechanism
    def init_db_with_retry(max_retries=3, retry_delay=1):
        for attempt in range(max_retries):
            try:
                with app.app_context():
                    # Test connection
                    db.session.execute(text("SELECT 1"))
                    db.session.commit()
                    print(f"Database connection verified on attempt {attempt + 1}!", file=sys.stderr)
                    
                    # Create tables
                    db.create_all()
                    print("Database tables created successfully!", file=sys.stderr)
                    return True
            except OperationalError as e:
                print(f"Database connection attempt {attempt + 1} failed: {str(e)}", file=sys.stderr)
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...", file=sys.stderr)
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print("Max retries reached. Continuing without database initialization.", file=sys.stderr)
            except Exception as e:
                print(f"Unexpected error during database initialization: {str(e)}", file=sys.stderr)
                print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
                break
        return False

    # Try to initialize the database
    init_db_with_retry()
    
    # Setup login manager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(id):
        try:
            return User.query.get(int(id))
        except Exception as e:
            print(f"Error loading user: {str(e)}", file=sys.stderr)
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
        db.session.rollback()
        print(f"500 error: {str(error)}", file=sys.stderr)
        print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
        return render_template('error.html', error=error), 500
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('error.html', error=error), 404
    
    return app