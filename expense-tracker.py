# expense_tracker.py - Day 5
# Added delete expense functionality

from datetime import datetime
import csv
import os

CATEGORIES = ["Food", "Transport", "Entertainment", "Shopping", "Bills", "Other"]
CSV_FILE = "expenses.csv"

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
    """Load expenses from CSV file"""
    expenses = []
    
    if not os.path.exists(CSV_FILE):
        return expenses
    
    try:
        with open(CSV_FILE, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                expense = {
                    "amount": float(row['amount']),
                    "description": row['description'],
                    "category": row['category'],
                    "date": datetime.strptime(row['date'], "%Y-%m-%d %H:%M:%S")
                }
                expenses.append(expense)
        print(f"✓ Loaded {len(expenses)} expenses from file")
    except Exception as e:
        print(f"Error loading expenses: {e}")
    
    return expenses

def save_expenses(expenses):
    """Save expenses to CSV file"""
    try:
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as file:
            fieldnames = ['amount', 'description', 'category', 'date']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            writer.writeheader()
            for expense in expenses:
                writer.writerow({
                    'amount': expense['amount'],
                    'description': expense['description'],
                    'category': expense['category'],
                    'date': expense['date'].strftime("%Y-%m-%d %H:%M:%S")
                })
        return True
    except Exception as e:
        print(f"Error saving expenses: {e}")
        return False

# NEW: Function to delete an expense
def delete_expense(expenses):
    """Delete an expense from the list"""
    if len(expenses) == 0:
        print("\nNo expenses to delete!")
        return expenses
    
    # Display all expenses with numbers
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
            expenses.pop(choice - 1)  # Remove from list
            
            # Save updated list
            if save_expenses(expenses):
                print(f"✓ Deleted: ${deleted['amount']:.2f} - {deleted['description']}")
            else:
                print("Error: Failed to save after deletion")
        else:
            print(f"Invalid number. Please enter 1-{len(expenses)}")
    except ValueError:
        print("Please enter a valid number")
    
    return expenses

def main():
    expenses = load_expenses()
    
    print("=== Welcome to Expense Tracker ===")
    print()
    
    while True:
        print("\n" + "="*40)
        print("What would you like to do?")
        print("1. Add an expense")
        print("2. View all expenses")
        print("3. View expenses by category")
        print("4. View total")
        print("5. Delete an expense")  # NEW option
        print("6. Exit")
        
        choice = input("\nEnter your choice (1-6): ")
        
        if choice == "1":
            # Add expense
            amount = float(input("Enter amount: $"))
            description = input("Enter description: ")
            category = get_category()
            
            current_date = datetime.now()
            
            expense = {
                "amount": amount,
                "description": description,
                "category": category,
                "date": current_date
            }
            expenses.append(expense)
            
            if save_expenses(expenses):
                formatted_date = current_date.strftime("%Y-%m-%d %H:%M")
                print(f"✓ Added and saved: ${amount} - {description} [{category}] on {formatted_date}")
            else:
                print("✓ Added but failed to save to file")
            
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
        
        elif choice == "5":
            # NEW: Delete expense
            expenses = delete_expense(expenses)
            
        elif choice == "6":
            print("\nGoodbye! 👋")
            break
        else:
            print("\nInvalid choice. Please try again.")

if __name__ == "__main__":
    main()