from flask import Flask, jsonify, render_template
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
    
    # Basic configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'project123')
    
    # Database configuration
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("No DATABASE_URL environment variable set", file=sys.stderr)
        database_url = 'sqlite:///database.db'  # Fallback for development
        
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    print(f"Database URL format: {database_url.split('@')[0].split(':')[0]}://*****@{database_url.split('@')[1] if '@' in database_url else 'local'}", file=sys.stderr)
    
    # Configure SQLAlchemy for serverless environment
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'poolclass': NullPool,
        'connect_args': {
            'connect_timeout': 30
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
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully!", file=sys.stderr)
        except Exception as e:
            print(f"Error creating database tables: {str(e)}", file=sys.stderr)
    
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
        return render_template('error.html', error=error), 500
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('error.html', error=error), 404
    
    return app