from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from os import path
import os

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
DB_NAME = "database.db"

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key-here'
    
    # Database configuration
    instance_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'instance')
    os.makedirs(instance_path, exist_ok=True)
    db_path = os.path.join(instance_path, DB_NAME)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    csrf = CSRFProtect(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    # Import models
    from .models import User, Category, Expense, Budget
    
    # Create database and initial user
    with app.app_context():
        db.create_all()
        try:
            # Check if admin user exists
            admin = User.query.filter_by(email='admin@example.com').first()
            if not admin:
                from werkzeug.security import generate_password_hash
                default_user = User(
                    email='admin@example.com',
                    first_name='Admin',
                    password_hash=generate_password_hash('Admin123!', method='pbkdf2:sha256'),
                    currency='INR'
                )
                db.session.add(default_user)
                db.session.commit()
                print("Default admin user created successfully!")
        except Exception as e:
            print(f"Error creating admin user: {e}")
    
    # Register blueprints
    from .views import views
    from .auth import auth
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    return app
