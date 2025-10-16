# init_users_db.py
# Script to add user authentication to existing database

import sqlite3
from werkzeug.security import generate_password_hash

DB_FILE = "expenses.db"

def upgrade_database():
    """Add users table and update expenses table"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    
    # Check if user_id column exists in expenses
    cursor.execute("PRAGMA table_info(expenses)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'user_id' not in columns:
        # Add user_id column to expenses
        cursor.execute('ALTER TABLE expenses ADD COLUMN user_id INTEGER DEFAULT 1')
        print("✅ Added user_id column to expenses table")
    
    # Create default admin user
    try:
        from datetime import datetime
        password_hash = generate_password_hash('admin123')
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, created_at)
            VALUES (?, ?, ?, ?)
        ''', ('admin', 'admin@expense-tracker.com', password_hash, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        print("✅ Created default admin user")
        print("   Username: admin")
        print("   Password: admin123")
        print("   ⚠️  Please change this password after first login!")
    except sqlite3.IntegrityError:
        print("ℹ️  Admin user already exists")
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON expenses(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_username ON users(username)')
    
    conn.commit()
    conn.close()
    
    print("\n✅ Database upgrade complete!")

if __name__ == '__main__':
    print("🔧 Upgrading database for multi-user support...")
    upgrade_database()