# web_app.py - Day 18
# Flask web interface with user authentication

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, make_response
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import sqlite3
import os
import csv
import json
from io import StringIO

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'error'

DB_FILE = "expenses.db"
CATEGORIES = ["Food", "Transport", "Entertainment", "Shopping", "Bills", "Other"]

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    user = cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    if user:
        return User(user['id'], user['username'], user['email'])
    return None

# Database helper functions
def get_db_connection():
    """Create database connection"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            user_obj = User(user['id'], user['username'], user['email'])
            login_user(user_obj, remember=True)
            flash(f'Welcome back, {username}!', 'success')
            
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long!', 'error')
            return render_template('register.html')
        
        conn = get_db_connection()
        
        # Check if username exists
        existing = conn.execute('SELECT * FROM users WHERE username = ? OR email = ?', 
                               (username, email)).fetchone()
        
        if existing:
            flash('Username or email already exists!', 'error')
            conn.close()
            return render_template('register.html')
        
        # Create user
        password_hash = generate_password_hash(password)
        conn.execute('''
            INSERT INTO users (username, email, password_hash, created_at)
            VALUES (?, ?, ?, ?)
        ''', (username, email, password_hash, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))

# Protected Routes (require login)
@app.route('/')
@login_required
def index():
    """Home page - Dashboard"""
    conn = get_db_connection()
    
    # Get total expenses for current user
    total = conn.execute('SELECT SUM(amount) as total FROM expenses WHERE user_id = ?', 
                        (current_user.id,)).fetchone()['total']
    total = total if total else 0
    
    # Get expense count
    count = conn.execute('SELECT COUNT(*) as count FROM expenses WHERE user_id = ?', 
                        (current_user.id,)).fetchone()['count']
    
    # Get this month's total
    this_month = conn.execute('''
        SELECT SUM(amount) as total FROM expenses
        WHERE user_id = ? AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
    ''', (current_user.id,)).fetchone()['total']
    this_month = this_month if this_month else 0
    
    # Get category breakdown
    categories = conn.execute('''
        SELECT category, SUM(amount) as total, COUNT(*) as count
        FROM expenses
        WHERE user_id = ?
        GROUP BY category
        ORDER BY total DESC
    ''', (current_user.id,)).fetchall()
    
    # Get recent expenses (last 10)
    recent_expenses = conn.execute('''
        SELECT * FROM expenses
        WHERE user_id = ?
        ORDER BY date DESC
        LIMIT 10
    ''', (current_user.id,)).fetchall()
    
    conn.close()
    
    return render_template('index.html',
                         total=total,
                         count=count,
                         this_month=this_month,
                         categories=categories,
                         recent_expenses=recent_expenses,
                         category_list=CATEGORIES,
                         datetime=datetime)

@app.route('/expenses')
@login_required
def expenses():
    """View all expenses"""
    conn = get_db_connection()
    
    # Get filter parameters
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    
    # Build query
    query = 'SELECT * FROM expenses WHERE user_id = ?'
    params = [current_user.id]
    
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
@login_required
def add_expense():
    """Add new expense"""
    if request.method == 'POST':
        amount = float(request.form['amount'])
        description = request.form['description']
        category = request.form['category']
        date = request.form.get('date', '')
        
        if date:
            date = date + ' ' + datetime.now().strftime('%H:%M:%S')
        else:
            date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO expenses (amount, description, category, date, user_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (amount, description, category, date, current_user.id))
        conn.commit()
        conn.close()
        
        flash(f'Expense added: ${amount:.2f} - {description}', 'success')
        return redirect(url_for('index'))
    
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('add.html', categories=CATEGORIES, today=today)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_expense(id):
    """Edit existing expense"""
    conn = get_db_connection()
    
    # Check if expense belongs to current user
    expense = conn.execute('SELECT * FROM expenses WHERE id = ? AND user_id = ?', 
                          (id, current_user.id)).fetchone()
    
    if expense is None:
        flash('Expense not found or you do not have permission to edit it!', 'error')
        conn.close()
        return redirect(url_for('expenses'))
    
    if request.method == 'POST':
        amount = float(request.form['amount'])
        description = request.form['description']
        category = request.form['category']
        
        conn.execute('''
            UPDATE expenses
            SET amount = ?, description = ?, category = ?
            WHERE id = ? AND user_id = ?
        ''', (amount, description, category, id, current_user.id))
        conn.commit()
        conn.close()
        
        flash('Expense updated successfully!', 'success')
        return redirect(url_for('expenses'))
    
    conn.close()
    return render_template('edit.html', expense=expense, categories=CATEGORIES)

@app.route('/delete/<int:id>')
@login_required
def delete_expense(id):
    """Delete expense"""
    conn = get_db_connection()
    
    # Check if expense belongs to current user
    expense = conn.execute('SELECT * FROM expenses WHERE id = ? AND user_id = ?', 
                          (id, current_user.id)).fetchone()
    
    if expense:
        conn.execute('DELETE FROM expenses WHERE id = ? AND user_id = ?', 
                    (id, current_user.id))
        conn.commit()
        flash('Expense deleted successfully!', 'success')
    else:
        flash('Expense not found or you do not have permission to delete it!', 'error')
    
    conn.close()
    return redirect(url_for('expenses'))

@app.route('/reports')
@login_required
def reports():
    """Reports dashboard"""
    return render_template('reports.html')

@app.route('/reports/monthly')
@login_required
def monthly_report():
    """Monthly report page"""
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)
    
    conn = get_db_connection()
    
    start_date = f"{year}-{month:02d}-01 00:00:00"
    
    if month == 12:
        end_date = f"{year + 1}-01-01 00:00:00"
    else:
        end_date = f"{year}-{month + 1:02d}-01 00:00:00"
    
    category_stats = conn.execute('''
        SELECT category, SUM(amount) as total, COUNT(*) as count, AVG(amount) as average
        FROM expenses
        WHERE user_id = ? AND date >= ? AND date < ?
        GROUP BY category
        ORDER BY total DESC
    ''', (current_user.id, start_date, end_date)).fetchall()
    
    overall = conn.execute('''
        SELECT 
            SUM(amount) as total,
            COUNT(*) as count,
            AVG(amount) as average,
            MIN(amount) as minimum,
            MAX(amount) as maximum
        FROM expenses
        WHERE user_id = ? AND date >= ? AND date < ?
    ''', (current_user.id, start_date, end_date)).fetchone()
    
    conn.close()
    
    month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December']
    
    return render_template('monthly_report.html',
                         year=year,
                         month=month,
                         month_name=month_names[month],
                         category_stats=category_stats,
                         overall=overall)

@app.route('/reports/category')
@login_required
def category_report():
    """Category analysis page"""
    conn = get_db_connection()
    
    categories = conn.execute('''
        SELECT 
            category,
            SUM(amount) as total,
            COUNT(*) as count,
            AVG(amount) as average,
            MIN(amount) as minimum,
            MAX(amount) as maximum
        FROM expenses
        WHERE user_id = ?
        GROUP BY category
        ORDER BY total DESC
    ''', (current_user.id,)).fetchall()
    
    total = conn.execute('SELECT SUM(amount) as total FROM expenses WHERE user_id = ?', 
                        (current_user.id,)).fetchone()['total']
    
    conn.close()
    
    return render_template('category_report.html',
                         categories=categories,
                         total=total if total else 0)

@app.route('/reports/yearly')
@login_required
def yearly_report():
    """Yearly summary page"""
    year = request.args.get('year', datetime.now().year, type=int)
    
    conn = get_db_connection()
    
    monthly_data = []
    for month in range(1, 13):
        start_date = f"{year}-{month:02d}-01 00:00:00"
        
        if month == 12:
            end_date = f"{year + 1}-01-01 00:00:00"
        else:
            end_date = f"{year}-{month + 1:02d}-01 00:00:00"
        
        result = conn.execute('''
            SELECT SUM(amount) as total, COUNT(*) as count
            FROM expenses
            WHERE user_id = ? AND date >= ? AND date < ?
        ''', (current_user.id, start_date, end_date)).fetchone()
        
        monthly_data.append({
            'month': month,
            'total': result['total'] if result['total'] else 0,
            'count': result['count'] if result['count'] else 0
        })
    
    conn.close()
    
    month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December']
    
    yearly_total = sum(m['total'] for m in monthly_data)
    yearly_count = sum(m['count'] for m in monthly_data)
    
    return render_template('yearly_report.html',
                         year=year,
                         monthly_data=monthly_data,
                         month_names=month_names,
                         yearly_total=yearly_total,
                         yearly_count=yearly_count)

@app.route('/reports/trends')
@login_required
def trends_report():
    """Spending trends page"""
    return render_template('trends_report.html')

@app.route('/api/stats')
@login_required
def api_stats():
    """API endpoint for statistics"""
    conn = get_db_connection()
    
    categories = conn.execute('''
        SELECT category, SUM(amount) as total
        FROM expenses
        WHERE user_id = ?
        GROUP BY category
        ORDER BY total DESC
    ''', (current_user.id,)).fetchall()
    
    monthly = conn.execute('''
        SELECT strftime('%Y-%m', date) as month, SUM(amount) as total
        FROM expenses
        WHERE user_id = ? AND date >= date('now', '-180 days')
        GROUP BY strftime('%Y-%m', date)
        ORDER BY month
    ''', (current_user.id,)).fetchall()
    
    conn.close()
    
    return jsonify({
        'categories': [dict(row) for row in categories],
        'monthly': [dict(row) for row in monthly]
    })

@app.route('/export/csv')
@login_required
def export_csv():
    """Export expenses to CSV"""
    conn = get_db_connection()
    expenses = conn.execute('SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC', 
                           (current_user.id,)).fetchall()
    conn.close()
    
    si = StringIO()
    writer = csv.writer(si)
    
    writer.writerow(['ID', 'Amount', 'Description', 'Category', 'Date'])
    
    for expense in expenses:
        writer.writerow([expense['id'], expense['amount'], expense['description'], 
                        expense['category'], expense['date']])
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename=expenses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    output.headers["Content-type"] = "text/csv"
    
    return output

@app.route('/export/json')
@login_required
def export_json():
    """Export expenses to JSON"""
    conn = get_db_connection()
    expenses = conn.execute('SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC', 
                           (current_user.id,)).fetchall()
    conn.close()
    
    expenses_list = [dict(expense) for expense in expenses]
    
    output = make_response(json.dumps(expenses_list, indent=2))
    output.headers["Content-Disposition"] = f"attachment; filename=expenses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output.headers["Content-type"] = "application/json"
    
    return output

@app.route('/about')
def about():
    """About page (public)"""
    return render_template('about.html')

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🌐 Expense Tracker Web Interface")
    print("="*50)
    print("\n📍 Server starting at: http://127.0.0.1:5000")
    print("📍 Press Ctrl+C to stop the server")
    print("\n🔐 Default Login:")
    print("   Username: admin")
    print("   Password: admin123\n")
    app.run(debug=True)