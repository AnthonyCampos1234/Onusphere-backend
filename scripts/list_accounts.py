import os
import sys
from pymongo import MongoClient

# Add the parent directory to Python path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def list_accounts():
    # Connect to MongoDB directly
    client = MongoClient('mongodb://localhost:27017/')
    db = client['customer_orders_db']
    accounts_collection = db['account']
    
    # Find all accounts
    accounts = accounts_collection.find({})
    
    print("\nBusiness Accounts:")
    print("-" * 50)
    for account in accounts:
        print(f"Company Name: {account.get('name', 'N/A')}")
        print(f"Company Email: {account.get('email', 'N/A')}")
        print(f"Company Code: {account.get('company_code', 'N/A')}")
        print("-" * 50)

if __name__ == "__main__":
    list_accounts() 