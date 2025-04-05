from flask import Flask, jsonify, render_template, flash
from flask_login import LoginManager, current_user
from datetime import datetime
import os
import sys
import json
import traceback
from dotenv import load_dotenv

load_dotenv()

# Simple storage setup
STORAGE_DIR = '/tmp'
USERS_FILE = os.path.join(STORAGE_DIR, 'users.json')
EXPENSES_FILE = os.path.join(STORAGE_DIR, 'expenses.json')

def save_data(file_path, data):
    os.makedirs(STORAGE_DIR, exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(data, f)

def load_data(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def create_app():
    app = Flask(__name__)
    
    # Basic configuration
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev')
    app.config['STATIC_FOLDER'] = None  # Disable automatic static serving
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        status = {
            'status': 'healthy',
            'checks': {
                'storage': 'unknown'
            }
        }
        
        # Check storage
        try:
            # Try to write and read from storage
            test_file = os.path.join(STORAGE_DIR, 'test.json')
            save_data(test_file, {'test': 'data'})
            test_data = load_data(test_file)
            if test_data.get('test') == 'data':
                status['checks']['storage'] = 'working'
            else:
                status['checks']['storage'] = 'error'
                status['status'] = 'unhealthy'
            os.remove(test_file)
        except Exception as e:
            print(f"Health check - Storage failed: {str(e)}", file=sys.stderr)
            status['checks']['storage'] = 'error'
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
    from .models import User
    
    # Setup login manager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        try:
            users = load_data(USERS_FILE)
            user_data = users.get(str(user_id))
            if user_data:
                return User.from_dict(user_data)
            return None
        except Exception as e:
            print(f"Error loading user {user_id}: {str(e)}", file=sys.stderr)
            print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
            return None
    
    @app.context_processor
    def utility_processor():
        def format_datetime(dt):
            if dt is None:
                return ""
            if isinstance(dt, str):
                return dt
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        return dict(format_datetime=format_datetime, now=datetime.utcnow)
    
    # Error handlers
    @app.errorhandler(500)
    def internal_error(error):
        print(f"500 error occurred: {str(error)}", file=sys.stderr)
        print(f"Error type: {type(error).__name__}", file=sys.stderr)
        print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
        
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