from website import create_app, db
from website.models import User, Expense
from datetime import datetime, timedelta
import random

app = create_app()

with app.app_context():
    # Create a test user if not exists
    user = User.query.filter_by(email='test@example.com').first()
    if not user:
        user = User(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            currency='USD'
        )
        user.set_password('test123')
        db.session.add(user)
        db.session.commit()
    
    # Add some expenses for the current month
    categories = ['food', 'transportation', 'utilities', 'entertainment', 'other']
    descriptions = {
        'food': ['Grocery shopping', 'Restaurant dinner', 'Coffee shop', 'Lunch'],
        'transportation': ['Gas', 'Bus ticket', 'Train pass', 'Taxi ride'],
        'utilities': ['Electricity bill', 'Water bill', 'Internet bill', 'Phone bill'],
        'entertainment': ['Movie tickets', 'Concert', 'Video games', 'Streaming service'],
        'other': ['Office supplies', 'Clothing', 'Books', 'Home decor']
    }
    
    # Get current month's start and end dates
    now = datetime.now()
    start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if now.month == 12:
        end_date = now.replace(year=now.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        end_date = now.replace(month=now.month + 1, day=1) - timedelta(days=1)
    
    # Add 20 random expenses for the current month
    for _ in range(20):
        category = random.choice(categories)
        expense = Expense(
            amount=round(random.uniform(10, 200), 2),
            original_amount=round(random.uniform(10, 200), 2),
            original_currency='USD',
            category=category,
            description=random.choice(descriptions[category]),
            date=start_date + timedelta(days=random.randint(0, (end_date - start_date).days)),
            user_id=user.id
        )
        db.session.add(expense)
    
    db.session.commit()
    print("Test data added successfully!") 