# expense_tracker.py - Day 2
# Added automatic date tracking for each expense

from datetime import datetime  # NEW: Import datetime module

def main():
    expenses = []
    
    print("=== Welcome to Expense Tracker ===")
    print()
    
    while True:
        print("\nWhat would you like to do?")
        print("1. Add an expense")
        print("2. View all expenses")
        print("3. View total")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ")
        
        if choice == "1":
            # Add expense
            amount = float(input("Enter amount: $"))
            description = input("Enter description: ")
            
            # NEW: Get current date and time
            current_date = datetime.now()
            
            expense = {
                "amount": amount,
                "description": description,
                "date": current_date  # NEW: Store the date
            }
            expenses.append(expense)
            
            # NEW: Show formatted date when confirming
            formatted_date = current_date.strftime("%Y-%m-%d %H:%M")
            print(f"✓ Added: ${amount} - {description} on {formatted_date}")
            
        elif choice == "2":
            # View all expenses
            if len(expenses) == 0:
                print("\nNo expenses yet!")
            else:
                print("\n=== All Expenses ===")
                for i, expense in enumerate(expenses, 1):
                    # NEW: Format and display the date
                    date_str = expense['date'].strftime("%Y-%m-%d %H:%M")
                    print(f"{i}. ${expense['amount']:.2f} - {expense['description']} ({date_str})")
                    
        elif choice == "3":
            # View total
            total = sum(expense['amount'] for expense in expenses)
            print(f"\nTotal expenses: ${total:.2f}")
            
        elif choice == "4":
            print("\nGoodbye! 👋")
            break
        else:
            print("\nInvalid choice. Please try again.")

if __name__ == "__main__":
    main()