from . import db
from .models import User, Expense
import sys

def init_db(app):
    """Initialize the database and create all tables."""
    try:
        with app.app_context():
            # Drop all tables
            db.drop_all()
            print("Dropped all existing tables.", file=sys.stderr)
            
            # Create all tables
            db.create_all()
            print("Created all tables successfully!", file=sys.stderr)
            
            return True
    except Exception as e:
        print(f"Error initializing database: {str(e)}", file=sys.stderr)
        return False 