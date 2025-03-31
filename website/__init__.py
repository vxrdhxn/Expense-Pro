from flask import Flask
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
                'connect_timeout': 10
            }
        }
        
        # Initialize extensions
        db.init_app(app)
        
        # Register blueprints
        from .views import views
        from .auth import auth
        
        app.register_blueprint(views, url_prefix='/')
        app.register_blueprint(auth, url_prefix='/')
        
        from .models import User, Expense
        
        # Create database tables
        with app.app_context():
            try:
                db.create_all()
                print('Database tables created successfully!')
            except Exception as e:
                print(f"Error creating tables: {str(e)}", file=sys.stderr)
                # Don't raise the error, try to continue
        
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
            
        return app
        
    except Exception as e:
        print(f"Error creating app: {str(e)}", file=sys.stderr)
        raise