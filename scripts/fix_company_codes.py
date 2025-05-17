import os
import sys
import string
import random
from pymongo import MongoClient

# Add the parent directory to Python path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def generate_company_code():
    return ''.join(random.choices(string.ascii_uppercase, k=6))

def fix_company_codes():
    # Connect to MongoDB directly
    client = MongoClient('mongodb://localhost:27017/')
    db = client['customer_orders_db']
    accounts_collection = db['account']
    
    try:
        # Drop the existing index
        accounts_collection.drop_index('company_code_1')
    except Exception as e:
        print(f"Note: Could not drop index (this is okay if it doesn't exist): {e}")
    
    # Find all accounts with null or missing company codes
    accounts_without_code = accounts_collection.find({
        '$or': [
            {'company_code': None},
            {'company_code': {'$exists': False}}
        ]
    })
    
    # Generate and assign new company codes
    for account in accounts_without_code:
        new_code = generate_company_code()
        accounts_collection.update_one(
            {'_id': account['_id']},
            {'$set': {'company_code': new_code}}
        )
        print(f"Updated account {account['_id']} with code {new_code}")
    
    # Create the unique index
    accounts_collection.create_index('company_code', unique=True)
    
    print("Company code index has been fixed!")

if __name__ == "__main__":
    fix_company_codes() 