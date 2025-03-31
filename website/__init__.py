from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from datetime import datetime
import os
import sys
from dotenv import load_dotenv
from sqlalchemy.pool import NullPool

load_dotenv()

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    try:
        # Basic configuration
        app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'project123')
        
        # Database configuration
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("No DATABASE_URL environment variable set")
            
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        
        print(f"Database URL format: {database_url.split('@')[0].split(':')[0]}://*****@{database_url.split('@')[1]}", file=sys.stderr)
        
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
        
        # Register blueprints
        from .views import views
        from .auth import auth
        
        app.register_blueprint(views, url_prefix='/')
        app.register_blueprint(auth, url_prefix='/')
        
        # Import models
        from .models import User, Expense
        
        # Initialize database
        from .db_init import init_db
        if not init_db(app):
            print("Warning: Database initialization failed", file=sys.stderr)
        
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
                return None
        
        # Error handlers
        @app.errorhandler(500)
        def internal_error(error):
            print(f"500 error: {str(error)}", file=sys.stderr)
            db.session.rollback()
            return jsonify({
                'error': 'Internal Server Error',
                'message': str(error)
            }), 500
        
        @app.errorhandler(404)
        def not_found_error(error):
            return jsonify({
                'error': 'Not Found',
                'message': str(error)
            }), 404
            
        return app
        
    except Exception as e:
        print(f"Error creating app: {str(e)}", file=sys.stderr)
        raise