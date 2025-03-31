from . import db
from .models import User, Expense
import sys
import os
from sqlalchemy import create_engine, text
import time

def init_db_with_retry(db_url, max_retries=5, retry_delay=2):
    """Initialize database with retry mechanism"""
    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1} to initialize database...")
            engine = create_engine(db_url)
            
            # Test connection
            with engine.connect() as conn:
                print("Successfully connected to database")
                
                # Create tables if they don't exist
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        email VARCHAR(150) UNIQUE NOT NULL,
                        password_hash VARCHAR(150) NOT NULL,
                        first_name VARCHAR(150) NOT NULL,
                        last_name VARCHAR(150) NOT NULL,
                        currency VARCHAR(3) DEFAULT 'USD' NOT NULL,
                        email_notifications BOOLEAN DEFAULT FALSE NOT NULL,
                        monthly_report BOOLEAN DEFAULT FALSE NOT NULL,
                        default_view VARCHAR(10) DEFAULT 'monthly' NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                    )
                """))
                
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS expenses (
                        id SERIAL PRIMARY KEY,
                        amount FLOAT NOT NULL,
                        original_amount FLOAT NOT NULL,
                        original_currency VARCHAR(3) DEFAULT 'USD' NOT NULL,
                        category VARCHAR(50) NOT NULL,
                        description VARCHAR(200) NOT NULL,
                        date TIMESTAMP NOT NULL,
                        user_id INTEGER NOT NULL REFERENCES users(id),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                    )
                """))
                
                # Commit the transaction
                conn.commit()
                print("Database tables created successfully")
                return True
                
        except Exception as e:
            print(f"Database initialization attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Max retries reached. Database initialization failed.")
                raise

def init_db():
    """Main database initialization function"""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
        
    try:
        success = init_db_with_retry(db_url)
        if success:
            print("Database initialization completed successfully")
        return success
    except Exception as e:
        print(f"Database initialization failed: {str(e)}")
        return False

if __name__ == '__main__':
    init_db() 