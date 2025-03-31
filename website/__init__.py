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

load_dotenv()

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # Basic configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'project123')
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
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
                'database': 'unknown',
                'storage': 'unknown'
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
        
        # Check storage (upload folder)
        try:
            if os.path.exists(app.config['UPLOAD_FOLDER']) and os.access(app.config['UPLOAD_FOLDER'], os.W_OK):
                status['checks']['storage'] = 'accessible'
            else:
                status['checks']['storage'] = 'inaccessible'
                status['status'] = 'unhealthy'
        except Exception as e:
            print(f"Health check - Storage failed: {str(e)}", file=sys.stderr)
            status['checks']['storage'] = 'error'
            status['status'] = 'unhealthy'
        
        return jsonify(status), 200 if status['status'] == 'healthy' else 500
    
    # Register blueprints
    from .views import views
    from .auth import auth
    
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    
    # Import models
    from .models import User, Expense
    
    # Initialize database with retry mechanism
    def init_db_with_retry(max_retries=5, retry_delay=1):  # Increased retries
        last_error = None
        for attempt in range(max_retries):
            try:
                with app.app_context():
                    print(f"Attempt {attempt + 1}: Testing database connection...", file=sys.stderr)
                    # Test connection
                    result = db.session.execute(text('SELECT 1'))
                    result.fetchone()
                    db.session.commit()
                    print(f"Database connection successful on attempt {attempt + 1}!", file=sys.stderr)
                    return True
            except (OperationalError, TimeoutError) as e:
                last_error = e
                print(f"Database connection attempt {attempt + 1} failed: {str(e)}", file=sys.stderr)
                print(f"Error type: {type(e).__name__}", file=sys.stderr)
                print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...", file=sys.stderr)
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print("Max retries reached.", file=sys.stderr)
            except Exception as e:
                last_error = e
                print(f"Unexpected error during database initialization: {str(e)}", file=sys.stderr)
                print(f"Error type: {type(e).__name__}", file=sys.stderr)
                print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
                break
        
        if last_error:
            print("Database initialization failed. Please check your database configuration.", file=sys.stderr)
            print(f"Final error: {str(last_error)}", file=sys.stderr)
        return False

    # Try to initialize the database
    print("Starting database initialization...", file=sys.stderr)
    init_success = init_db_with_retry()
    print(f"Database initialization {'successful' if init_success else 'failed'}", file=sys.stderr)
    
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
    
    return app