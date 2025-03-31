-- Create users table
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
);

-- Create expenses table
CREATE TABLE IF NOT EXISTS expenses (
    id SERIAL PRIMARY KEY,
    amount FLOAT NOT NULL,
    original_amount FLOAT NOT NULL,
    original_currency VARCHAR(3) DEFAULT 'USD' NOT NULL,
    category VARCHAR(50) NOT NULL,
    description VARCHAR(200) NOT NULL,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
); 