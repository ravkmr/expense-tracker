# expense_tracker.py - Day 9
# Added search functionality with advanced SQL queries

from datetime import datetime, timedelta
import sqlite3
import os

CATEGORIES = ["Food", "Transport", "Entertainment", "Shopping", "Bills", "Other"]
DB_FILE = "expenses.db"

def init_database():
    """Create database and expenses table if they don't exist"""
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
    
    conn.commit()
    conn.close()
    print("✓ Database initialized")

def display_categories():
    """Display available categories"""
    print("\nCategories:")
    for i, category in enumerate(CATEGORIES, 1):
        print(f"{i}. {category}")

def get_category():
    """Get a valid category from user"""
    display_categories()
    
    while True:
        try:
            choice = int(input("\nSelect category (1-6): "))
            if 1 <= choice <= len(CATEGORIES):
                return CATEGORIES[choice - 1]
            else:
                print(f"Please enter a number between 1 and {len(CATEGORIES)}")
        except ValueError:
            print("Please enter a valid number")

def load_expenses():
    """Load all expenses from database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, amount, description, category, date FROM expenses ORDER BY date DESC')
    rows = cursor.fetchall()
    
    expenses = []
    for row in rows:
        expense = {
            "id": row[0],
            "amount": row[1],
            "description": row[2],
            "category": row[3],
            "date": datetime.strptime(row[4], "%Y-%m-%d %H:%M:%S")
        }
        expenses.append(expense)
    
    conn.close()
    
    if len(expenses) > 0:
        print(f"✓ Loaded {len(expenses)} expenses from database")
    
    return expenses

def add_expense_to_db(amount, description, category, date):
    """Add a new expense to the database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO expenses (amount, description, category, date)
        VALUES (?, ?, ?, ?)
    ''', (amount, description, category, date.strftime("%Y-%m-%d %H:%M:%S")))
    
    conn.commit()
    expense_id = cursor.lastrowid
    conn.close()
    
    return expense_id

def delete_expense_from_db(expense_id):
    """Delete an expense from the database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
    
    conn.commit()
    conn.close()

def update_expense_in_db(expense_id, amount, description, category):
    """Update an expense in the database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE expenses 
        SET amount = ?, description = ?, category = ?
        WHERE id = ?
    ''', (amount, description, category, expense_id))
    
    conn.commit()
    conn.close()

# NEW: Search expenses in database
def search_expenses_in_db(search_term):
    """Search expenses by description or category"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Use LIKE for partial matching, % is wildcard
    # LOWER() for case-insensitive search
    cursor.execute('''
        SELECT id, amount, description, category, date 
        FROM expenses 
        WHERE LOWER(description) LIKE LOWER(?) 
           OR LOWER(category) LIKE LOWER(?)
        ORDER BY date DESC
    ''', (f'%{search_term}%', f'%{search_term}%'))
    
    rows = cursor.fetchall()
    
    expenses = []
    for row in rows:
        expense = {
            "id": row[0],
            "amount": row[1],
            "description": row[2],
            "category": row[3],
            "date": datetime.strptime(row[4], "%Y-%m-%d %H:%M:%S")
        }
        expenses.append(expense)
    
    conn.close()
    
    return expenses

# NEW: Advanced search with amount range
def advanced_search(min_amount=None, max_amount=None, category=None, search_term=None):
    """Advanced search with multiple filters"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Build dynamic query
    query = 'SELECT id, amount, description, category, date FROM expenses WHERE 1=1'
    params = []
    
    if min_amount is not None:
        query += ' AND amount >= ?'
        params.append(min_amount)
    
    if max_amount is not None:
        query += ' AND amount <= ?'
        params.append(max_amount)
    
    if category is not None:
        query += ' AND category = ?'
        params.append(category)
    
    if search_term is not None:
        query += ' AND LOWER(description) LIKE LOWER(?)'
        params.append(f'%{search_term}%')
    
    query += ' ORDER BY date DESC'
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    expenses = []
    for row in rows:
        expense = {
            "id": row[0],
            "amount": row[1],
            "description": row[2],
            "category": row[3],
            "date": datetime.strptime(row[4], "%Y-%m-%d %H:%M:%S")
        }
        expenses.append(expense)
    
    conn.close()
    
    return expenses

def delete_expense(expenses):
    """Delete an expense from the list"""
    if len(expenses) == 0:
        print("\nNo expenses to delete!")
        return expenses
    
    print("\n" + "="*40)
    print("=== Select Expense to Delete ===")
    for i, expense in enumerate(expenses, 1):
        date_str = expense['date'].strftime("%Y-%m-%d %H:%M")
        print(f"{i}. ${expense['amount']:.2f} - {expense['description']} [{expense['category']}] ({date_str})")
    
    try:
        choice = int(input("\nEnter expense number to delete (0 to cancel): "))
        
        if choice == 0:
            print("Delete cancelled")
            return expenses
        
        if 1 <= choice <= len(expenses):
            deleted = expenses[choice - 1]
            
            delete_expense_from_db(deleted['id'])
            
            expenses.pop(choice - 1)
            
            print(f"✓ Deleted: ${deleted['amount']:.2f} - {deleted['description']}")
        else:
            print(f"Invalid number. Please enter 1-{len(expenses)}")
    except ValueError:
        print("Please enter a valid number")
    
    return expenses

def edit_expense(expenses):
    """Edit an existing expense"""
    if len(expenses) == 0:
        print("\nNo expenses to edit!")
        return expenses
    
    print("\n" + "="*40)
    print("=== Select Expense to Edit ===")
    for i, expense in enumerate(expenses, 1):
        date_str = expense['date'].strftime("%Y-%m-%d %H:%M")
        print(f"{i}. ${expense['amount']:.2f} - {expense['description']} [{expense['category']}] ({date_str})")
    
    try:
        choice = int(input("\nEnter expense number to edit (0 to cancel): "))
        
        if choice == 0:
            print("Edit cancelled")
            return expenses
        
        if 1 <= choice <= len(expenses):
            expense = expenses[choice - 1]
            
            print("\n" + "="*40)
            print("=== Current Expense Details ===")
            print(f"Amount: ${expense['amount']:.2f}")
            print(f"Description: {expense['description']}")
            print(f"Category: {expense['category']}")
            print(f"Date: {expense['date'].strftime('%Y-%m-%d %H:%M')}")
            
            print("\nWhat would you like to edit?")
            print("1. Amount")
            print("2. Description")
            print("3. Category")
            print("4. All of the above")
            print("0. Cancel")
            
            edit_choice = input("\nEnter your choice (0-4): ")
            
            if edit_choice == "0":
                print("Edit cancelled")
                return expenses
            
            new_amount = expense['amount']
            new_description = expense['description']
            new_category = expense['category']
            
            if edit_choice in ["1", "4"]:
                try:
                    amount_input = input(f"Enter new amount (current: ${expense['amount']:.2f}): $")
                    if amount_input.strip():
                        new_amount = float(amount_input)
                except ValueError:
                    print("Invalid amount, keeping original")
            
            if edit_choice in ["2", "4"]:
                desc_input = input(f"Enter new description (current: {expense['description']}): ")
                if desc_input.strip():
                    new_description = desc_input
            
            if edit_choice in ["3", "4"]:
                print(f"\nCurrent category: {expense['category']}")
                new_category = get_category()
            
            update_expense_in_db(expense['id'], new_amount, new_description, new_category)
            
            expense['amount'] = new_amount
            expense['description'] = new_description
            expense['category'] = new_category
            
            print(f"✓ Expense updated successfully!")
            date_str = expense['date'].strftime("%Y-%m-%d %H:%M")
            print(f"   ${expense['amount']:.2f} - {expense['description']} [{expense['category']}] ({date_str})")
        else:
            print(f"Invalid number. Please enter 1-{len(expenses)}")
    except ValueError:
        print("Please enter a valid number")
    
    return expenses

# NEW: Simple search function
def search_expenses():
    """Search expenses by keyword"""
    search_term = input("\nEnter search term (description or category): ").strip()
    
    if not search_term:
        print("Search cancelled")
        return
    
    results = search_expenses_in_db(search_term)
    
    if len(results) == 0:
        print(f"\nNo expenses found matching '{search_term}'")
    else:
        print("\n" + "="*40)
        print(f"=== Search Results for '{search_term}' ===")
        print(f"Found {len(results)} expense(s)")
        print()
        
        total = 0
        for i, expense in enumerate(results, 1):
            date_str = expense['date'].strftime("%Y-%m-%d %H:%M")
            print(f"{i}. ${expense['amount']:.2f} - {expense['description']} [{expense['category']}] ({date_str})")
            total += expense['amount']
        
        print(f"\nTotal: ${total:.2f}")

# NEW: Advanced search function
def advanced_search_menu():
    """Advanced search with multiple filters"""
    print("\n" + "="*40)
    print("=== Advanced Search ===")
    
    # Get filters
    min_amount = None
    max_amount = None
    category = None
    search_term = None
    
    # Amount range
    amount_filter = input("\nFilter by amount range? (y/n): ").lower()
    if amount_filter == 'y':
        try:
            min_input = input("Minimum amount (press Enter to skip): $")
            if min_input.strip():
                min_amount = float(min_input)
            
            max_input = input("Maximum amount (press Enter to skip): $")
            if max_input.strip():
                max_amount = float(max_input)
        except ValueError:
            print("Invalid amount, skipping amount filter")
    
    # Category filter
    cat_filter = input("Filter by category? (y/n): ").lower()
    if cat_filter == 'y':
        category = get_category()
    
    # Keyword filter
    keyword_filter = input("Search in description? (y/n): ").lower()
    if keyword_filter == 'y':
        search_term = input("Enter keyword: ").strip()
    
    # Perform search
    results = advanced_search(min_amount, max_amount, category, search_term)
    
    if len(results) == 0:
        print("\nNo expenses found matching your criteria")
    else:
        print("\n" + "="*40)
        print("=== Search Results ===")
        print(f"Found {len(results)} expense(s)")
        print()
        
        total = 0
        for i, expense in enumerate(results, 1):
            date_str = expense['date'].strftime("%Y-%m-%d %H:%M")
            print(f"{i}. ${expense['amount']:.2f} - {expense['description']} [{expense['category']}] ({date_str})")
            total += expense['amount']
        
        print(f"\nTotal: ${total:.2f}")

def view_expenses_by_date(expenses):
    """View expenses filtered by date range"""
    if len(expenses) == 0:
        print("\nNo expenses yet!")
        return
    
    print("\n" + "="*40)
    print("=== Date Range Filter ===")
    print("1. Last 7 days")
    print("2. Last 30 days")
    print("3. This month")
    print("4. Custom date range")
    print("0. Cancel")
    
    choice = input("\nEnter your choice (0-4): ")
    
    now = datetime.now()
    filtered = []
    title = ""
    
    if choice == "1":
        start_date = now - timedelta(days=7)
        filtered = [e for e in expenses if e['date'] >= start_date]
        title = "Last 7 Days"
        
    elif choice == "2":
        start_date = now - timedelta(days=30)
        filtered = [e for e in expenses if e['date'] >= start_date]
        title = "Last 30 Days"
        
    elif choice == "3":
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        filtered = [e for e in expenses if e['date'] >= start_date]
        title = "This Month"
        
    elif choice == "4":
        try:
            print("\nEnter start date (YYYY-MM-DD):")
            start_input = input("Start date: ")
            start_date = datetime.strptime(start_input, "%Y-%m-%d")
            
            print("Enter end date (YYYY-MM-DD):")
            end_input = input("End date: ")
            end_date = datetime.strptime(end_input, "%Y-%m-%d")
            end_date = end_date.replace(hour=23, minute=59, second=59)
            
            if start_date > end_date:
                print("Error: Start date must be before end date!")
                return
            
            filtered = [e for e in expenses if start_date <= e['date'] <= end_date]
            title = f"From {start_input} to {end_input}"
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD (e.g., 2025-10-01)")
            return
    
    elif choice == "0":
        print("Cancelled")
        return
    else:
        print("Invalid choice")
        return
    
    if len(filtered) == 0:
        print(f"\nNo expenses found for: {title}")
    else:
        print("\n" + "="*40)
        print(f"=== Expenses: {title} ===")
        total = 0
        for i, expense in enumerate(filtered, 1):
            date_str = expense['date'].strftime("%Y-%m-%d %H:%M")
            print(f"{i}. ${expense['amount']:.2f} - {expense['description']} [{expense['category']}] ({date_str})")
            total += expense['amount']
        
        print(f"\nTotal for {title}: ${total:.2f}")
        
        print("\nCategory Breakdown:")
        for category in CATEGORIES:
            cat_expenses = [e for e in filtered if e['category'] == category]
            if len(cat_expenses) > 0:
                cat_total = sum(e['amount'] for e in cat_expenses)
                percentage = (cat_total / total) * 100
                print(f"  {category}: ${cat_total:.2f} ({percentage:.1f}%)")

def main():
    init_database()
    
    expenses = load_expenses()
    
    print("=== Welcome to Expense Tracker ===")
    print()
    
    while True:
        print("\n" + "="*40)
        print("What would you like to do?")
        print("1. Add an expense")
        print("2. View all expenses")
        print("3. View expenses by category")
        print("4. View expenses by date range")
        print("5. Search expenses")              # NEW option
        print("6. Advanced search")               # NEW option
        print("7. View total")
        print("8. Delete an expense")
        print("9. Edit an expense")
        print("10. Exit")
        
        choice = input("\nEnter your choice (1-10): ")
        
        if choice == "1":
            # Add expense
            amount = float(input("Enter amount: $"))
            description = input("Enter description: ")
            category = get_category()
            
            current_date = datetime.now()
            
            expense_id = add_expense_to_db(amount, description, category, current_date)
            
            expense = {
                "id": expense_id,
                "amount": amount,
                "description": description,
                "category": category,
                "date": current_date
            }
            expenses.insert(0, expense)
            
            formatted_date = current_date.strftime("%Y-%m-%d %H:%M")
            print(f"✓ Added and saved: ${amount} - {description} [{category}] on {formatted_date}")
            
        elif choice == "2":
            # View all expenses
            if len(expenses) == 0:
                print("\nNo expenses yet!")
            else:
                print("\n" + "="*40)
                print("=== All Expenses ===")
                for i, expense in enumerate(expenses, 1):
                    date_str = expense['date'].strftime("%Y-%m-%d %H:%M")
                    print(f"{i}. ${expense['amount']:.2f} - {expense['description']} [{expense['category']}] ({date_str})")
                    
        elif choice == "3":
            # View expenses by category
            if len(expenses) == 0:
                print("\nNo expenses yet!")
            else:
                display_categories()
                try:
                    cat_choice = int(input("\nSelect category to view (1-6): "))
                    if 1 <= cat_choice <= len(CATEGORIES):
                        selected_category = CATEGORIES[cat_choice - 1]
                        
                        filtered = [e for e in expenses if e['category'] == selected_category]
                        
                        if len(filtered) == 0:
                            print(f"\nNo expenses in '{selected_category}' category yet!")
                        else:
                            print(f"\n=== {selected_category} Expenses ===")
                            category_total = 0
                            for i, expense in enumerate(filtered, 1):
                                date_str = expense['date'].strftime("%Y-%m-%d %H:%M")
                                print(f"{i}. ${expense['amount']:.2f} - {expense['description']} ({date_str})")
                                category_total += expense['amount']
                            print(f"\n{selected_category} Total: ${category_total:.2f}")
                    else:
                        print(f"Please enter a number between 1 and {len(CATEGORIES)}")
                except ValueError:
                    print("Please enter a valid number")
        
        elif choice == "4":
            # View expenses by date range
            view_expenses_by_date(expenses)
        
        elif choice == "5":
            # NEW: Simple search
            search_expenses()
        
        elif choice == "6":
            # NEW: Advanced search
            advanced_search_menu()
                    
        elif choice == "7":
            # View total
            if len(expenses) == 0:
                print("\nNo expenses yet!")
            else:
                total = sum(expense['amount'] for expense in expenses)
                print(f"\nTotal expenses: ${total:.2f}")
                
                print("\nBreakdown by category:")
                for category in CATEGORIES:
                    cat_expenses = [e for e in expenses if e['category'] == category]
                    if len(cat_expenses) > 0:
                        cat_total = sum(e['amount'] for e in cat_expenses)
                        percentage = (cat_total / total) * 100
                        print(f"  {category}: ${cat_total:.2f} ({percentage:.1f}%)")
        
        elif choice == "8":
            # Delete expense
            expenses = delete_expense(expenses)
        
        elif choice == "9":
            # Edit expense
            expenses = edit_expense(expenses)
            
        elif choice == "10":
            print("\nGoodbye! 👋")
            break
        else:
            print("\nInvalid choice. Please try again.")

if __name__ == "__main__":
    main()