from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from datetime import datetime
import os
import sys
from dotenv import load_dotenv
from sqlalchemy.pool import NullPool
import time

load_dotenv()

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    try:
        app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'project123')
        
        # Get database URL and modify it for SQLAlchemy if needed
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("No DATABASE_URL environment variable set")
            
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        
        print(f"Database URL format: {database_url.split('@')[0].split(':')[0]}://*****@{database_url.split('@')[1]}")
        
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
                'keepalives_count': 5
            }
        }
        
        # Initialize extensions
        db.init_app(app)
        
        # Add health check route
        @app.route('/health')
        def health_check():
            try:
                # Test database connection
                db.session.execute('SELECT 1')
                return jsonify({'status': 'healthy', 'database': 'connected'})
            except Exception as e:
                return jsonify({'status': 'unhealthy', 'database': str(e)}), 500
        
        # Register blueprints
        from .views import views
        from .auth import auth
        
        app.register_blueprint(views, url_prefix='/')
        app.register_blueprint(auth, url_prefix='/')
        
        from .models import User, Expense
        
        # Create database tables with retry logic
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                with app.app_context():
                    db.create_all()
                    print('Database tables created successfully!')
                break
            except Exception as e:
                print(f"Error creating tables (attempt {attempt + 1}/{max_retries}): {str(e)}", file=sys.stderr)
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print("Failed to create tables after all retries", file=sys.stderr)
        
        # Setup login manager
        login_manager = LoginManager()
        login_manager.login_view = 'auth.login'
        login_manager.init_app(app)
        
        @login_manager.user_loader
        def load_user(id):
            try:
                return User.query.get(int(id))
            except Exception as e:
                print(f"Error loading user: {str(e)}")
                return None
        
        @app.context_processor
        def inject_now():
            return {'now': datetime.utcnow()}
        
        # Error handlers
        @app.errorhandler(500)
        def internal_error(error):
            db.session.rollback()
            return jsonify({'error': 'Internal Server Error', 'details': str(error)}), 500
            
        return app
        
    except Exception as e:
        print(f"Error creating app: {str(e)}", file=sys.stderr)
        raise