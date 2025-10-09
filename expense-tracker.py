# expense_tracker.py - Day 1
# Simple expense tracker that stores expenses in a list

def main():
    expenses = []  # List to store all expenses
    
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
            
            expense = {
                "amount": amount,
                "description": description
            }
            expenses.append(expense)
            print(f"✓ Added: ${amount} - {description}")
            
        elif choice == "2":
            # View all expenses
            if len(expenses) == 0:
                print("\nNo expenses yet!")
            else:
                print("\n=== All Expenses ===")
                for i, expense in enumerate(expenses, 1):
                    print(f"{i}. ${expense['amount']:.2f} - {expense['description']}")
                    
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