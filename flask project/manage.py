import os
from flask_migrate import Migrate, upgrade, init, migrate as create_migration, stamp
from website import create_app, db
from website.models import User, Category, Expense, Budget

app = create_app()
migrate_manager = Migrate(app, db)

def init_db():
    with app.app_context():
        # Check if migrations/versions directory exists and is empty
        versions_dir = os.path.join('migrations', 'versions')
        if os.path.exists(versions_dir) and not os.listdir(versions_dir):
            # If migrations directory exists but versions is empty, stamp the database
            # and create a new migration
            print("Migrations directory exists but is empty. Creating new migration...")
            stamp()  # Mark the database as being at the base revision
            create_migration(message="Initial migration")
            upgrade()
        elif not os.path.exists('migrations'):
            # If migrations directory doesn't exist, initialize it
            print("Initializing migrations...")
            init()
            create_migration(message="Initial migration")
            upgrade()
        else:
            # Just create the tables directly as a fallback
            print("Creating database tables directly...")
            db.create_all()
        
        print("Database initialized successfully!")

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
