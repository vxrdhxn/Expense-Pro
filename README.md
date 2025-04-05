# ExpensePro - Personal Expense Tracker

ExpensePro is a modern, feature-rich expense tracking application built with Flask and Tailwind CSS. It helps users manage their personal finances with an intuitive interface and powerful features.

## Features

### Core Features
- User authentication and account management
- Expense tracking with categories and tags
- Monthly budget tracking and alerts
- Data visualization with charts and statistics
- Multi-currency support
- Export data to CSV and PDF formats

### Dashboard
- Overview of monthly expenses
- Category-wise expense distribution
- Monthly trend analysis
- Recent transactions list
- Quick expense addition

### Budget Management
- Set and track monthly budgets
- Budget progress visualization
- Overspending alerts
- Category-wise budget allocation

### Data Analysis
- Interactive charts and graphs
- Expense trends over time
- Category distribution analysis
- Monthly and yearly comparisons

### Settings & Preferences
- Profile management
- Currency preferences
- Notification settings
- Monthly report subscriptions
- Data export options

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/expensepro.git
cd expensepro
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with the following variables:
```env
FLASK_SECRET_KEY=your-secret-key
FLASK_ENV=development
DATABASE_URL=sqlite:///database.db
```

5. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

6. Run the application:
```bash
flask run
```

## Usage

1. Register a new account or log in
2. Set up your monthly budget and currency preferences
3. Start adding expenses with descriptions and categories
4. View your spending patterns in the dashboard
5. Export your data as needed

## Development

### Project Structure
```
expensepro/
├── website/
│   ├── __init__.py
│   ├── auth.py
│   ├── models.py
│   ├── routes.py
│   ├── settings.py
│   ├── utils.py
│   └── templates/
│       ├── base.html
│       ├── home.html
│       ├── login.html
│       ├── settings.html
│       └── sign_up.html
├── instance/
├── requirements.txt
├── .env
└── README.md
```

### Technology Stack
- **Backend**: Flask (Python)
- **Database**: SQLite/PostgreSQL
- **Frontend**: Tailwind CSS, Chart.js
- **Authentication**: Flask-Login
- **ORM**: SQLAlchemy

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/improvement`)
3. Make your changes
4. Commit your changes (`git commit -am 'Add new feature'`)
5. Push to the branch (`git push origin feature/improvement`)
6. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Flask documentation and community
- Tailwind CSS team
- Chart.js contributors
- All open-source packages used in this project 