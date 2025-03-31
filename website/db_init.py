from . import db
from .models import User, Expense
import sys
import os

def init_db(app):
    """Initialize the database and create all tables."""
    try:
        with app.app_context():
            # Only drop tables if explicitly set
            if os.getenv('FLASK_ENV') == 'development':
                db.drop_all()
                print("Development mode: Dropped all existing tables.", file=sys.stderr)
            
            # Create all tables if they don't exist
            db.create_all()
            print("Created/Updated database tables successfully!", file=sys.stderr)
            
            # Verify database connection
            db.session.execute('SELECT 1')
            db.session.commit()
            print("Database connection verified.", file=sys.stderr)
            
            return True
    except Exception as e:
        print(f"Error initializing database: {str(e)}", file=sys.stderr)
        return False 