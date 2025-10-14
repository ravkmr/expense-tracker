# web_app.py - Day 15
# Flask web interface for expense tracker

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, timedelta
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-this'  # Change this to a random string

DB_FILE = "expenses.db"
CATEGORIES = ["Food", "Transport", "Entertainment", "Shopping", "Bills", "Other"]

# Database helper functions
def get_db_connection():
    """Create database connection"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

def init_database():
    """Initialize database if it doesn't exist"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL
        )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON expenses(date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON expenses(category)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_amount ON expenses(amount)')
    
    conn.commit()
    conn.close()

# Routes
@app.route('/')
def index():
    """Home page - Dashboard"""
    conn = get_db_connection()
    
    # Get total expenses
    total = conn.execute('SELECT SUM(amount) as total FROM expenses').fetchone()['total']
    total = total if total else 0
    
    # Get expense count
    count = conn.execute('SELECT COUNT(*) as count FROM expenses').fetchone()['count']
    
    # Get this month's total
    this_month = conn.execute('''
        SELECT SUM(amount) as total FROM expenses
        WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
    ''').fetchone()['total']
    this_month = this_month if this_month else 0
    
    # Get category breakdown
    categories = conn.execute('''
        SELECT category, SUM(amount) as total, COUNT(*) as count
        FROM expenses
        GROUP BY category
        ORDER BY total DESC
    ''').fetchall()
    
    # Get recent expenses (last 10)
    recent_expenses = conn.execute('''
        SELECT * FROM expenses
        ORDER BY date DESC
        LIMIT 10
    ''').fetchall()
    
    conn.close()
    
    return render_template('index.html',
                         total=total,
                         count=count,
                         this_month=this_month,
                         categories=categories,
                         recent_expenses=recent_expenses,
                         category_list=CATEGORIES)

@app.route('/expenses')
def expenses():
    """View all expenses"""
    conn = get_db_connection()
    
    # Get filter parameters
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    
    # Build query
    query = 'SELECT * FROM expenses WHERE 1=1'
    params = []
    
    if category:
        query += ' AND category = ?'
        params.append(category)
    
    if search:
        query += ' AND (description LIKE ? OR category LIKE ?)'
        params.append(f'%{search}%')
        params.append(f'%{search}%')
    
    query += ' ORDER BY date DESC'
    
    all_expenses = conn.execute(query, params).fetchall()
    conn.close()
    
    return render_template('expenses.html',
                         expenses=all_expenses,
                         categories=CATEGORIES,
                         selected_category=category,
                         search_term=search)

@app.route('/add', methods=['GET', 'POST'])
def add_expense():
    """Add new expense"""
    if request.method == 'POST':
        amount = float(request.form['amount'])
        description = request.form['description']
        category = request.form['category']
        date = request.form.get('date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        # If no time provided, add current time
        if len(date) == 10:  # Only date, no time
            date += ' ' + datetime.now().strftime('%H:%M:%S')
        
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO expenses (amount, description, category, date)
            VALUES (?, ?, ?, ?)
        ''', (amount, description, category, date))
        conn.commit()
        conn.close()
        
        flash(f'Expense added: ${amount:.2f} - {description}', 'success')
        return redirect(url_for('index'))
    
    return render_template('add.html', categories=CATEGORIES)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_expense(id):
    """Edit existing expense"""
    conn = get_db_connection()
    
    if request.method == 'POST':
        amount = float(request.form['amount'])
        description = request.form['description']
        category = request.form['category']
        
        conn.execute('''
            UPDATE expenses
            SET amount = ?, description = ?, category = ?
            WHERE id = ?
        ''', (amount, description, category, id))
        conn.commit()
        conn.close()
        
        flash('Expense updated successfully!', 'success')
        return redirect(url_for('expenses'))
    
    expense = conn.execute('SELECT * FROM expenses WHERE id = ?', (id,)).fetchone()
    conn.close()
    
    if expense is None:
        flash('Expense not found!', 'error')
        return redirect(url_for('expenses'))
    
    return render_template('edit.html', expense=expense, categories=CATEGORIES)

@app.route('/delete/<int:id>')
def delete_expense(id):
    """Delete expense"""
    conn = get_db_connection()
    conn.execute('DELETE FROM expenses WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    flash('Expense deleted successfully!', 'success')
    return redirect(url_for('expenses'))

@app.route('/api/stats')
def api_stats():
    """API endpoint for statistics (for charts)"""
    conn = get_db_connection()
    
    # Category data
    categories = conn.execute('''
        SELECT category, SUM(amount) as total
        FROM expenses
        GROUP BY category
        ORDER BY total DESC
    ''').fetchall()
    
    # Monthly data (last 6 months)
    monthly = conn.execute('''
        SELECT strftime('%Y-%m', date) as month, SUM(amount) as total
        FROM expenses
        WHERE date >= date('now', '-180 days')
        GROUP BY strftime('%Y-%m', date)
        ORDER BY month
    ''').fetchall()
    
    conn.close()
    
    return jsonify({
        'categories': [dict(row) for row in categories],
        'monthly': [dict(row) for row in monthly]
    })

if __name__ == '__main__':
    init_database()
    print("\n" + "="*50)
    print("🌐 Expense Tracker Web Interface")
    print("="*50)
    print("\n📍 Server starting at: http://127.0.0.1:5000")
    print("📍 Press Ctrl+C to stop the server\n")
    app.run(debug=True)