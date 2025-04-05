-- Users table
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(150) UNIQUE NOT NULL,
    password VARCHAR(150) NOT NULL,
    first_name VARCHAR(150) NOT NULL,
    last_name VARCHAR(150) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    monthly_budget FLOAT DEFAULT 1000.0,
    notification_preferences TEXT DEFAULT '{}',
    monthly_report BOOLEAN DEFAULT FALSE,
    default_view VARCHAR(10) DEFAULT 'monthly',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Expenses table
CREATE TABLE IF NOT EXISTS expense (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount FLOAT NOT NULL,
    description VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,
    date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    tags TEXT,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_expense_user_id ON expense(user_id);
CREATE INDEX IF NOT EXISTS idx_expense_date ON expense(date);
CREATE INDEX IF NOT EXISTS idx_expense_category ON expense(category);

-- Create trigger to update the updated_at timestamp
CREATE TRIGGER IF NOT EXISTS expense_updated_at
    AFTER UPDATE ON expense
    FOR EACH ROW
BEGIN
    UPDATE expense SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END; 