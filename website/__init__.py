from flask import Flask, jsonify, render_template, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from datetime import datetime
import os
import sys
import traceback
from dotenv import load_dotenv
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
    
    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
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
            db.session.execute('SELECT 1')
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