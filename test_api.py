#!/usr/bin/env python3
"""
API Testing Script for FinSplit
Tests all REST API endpoints to ensure they're working correctly.
"""

import requests
import json
from requests.auth import HTTPBasicAuth

# Configuration
BASE_URL = 'http://localhost:8000/api'
USERNAME = 'alice'
PASSWORD = 'password123'

def test_api_endpoints():
    """Test all API endpoints."""
    print("🚀 Testing FinSplit API Endpoints")
    print("=" * 50)
    
    # Test authentication
    print("\n1. Testing Authentication...")
    auth = HTTPBasicAuth(USERNAME, PASSWORD)
    
    # Test pools endpoint
    print("\n2. Testing Pools API...")
    response = requests.get(f'{BASE_URL}/pools/', auth=auth)
    print(f"   GET /pools/ - Status: {response.status_code}")
    if response.status_code == 200:
        pools = response.json()
        print(f"   Found {len(pools.get('results', pools))} pools")
        pool_data = pools.get('results', pools)
        if pool_data:
            pool_id = pool_data[0]['id']
            print(f"   First pool: {pool_data[0]['name']}")
            
            # Test pool detail
            detail_response = requests.get(f'{BASE_URL}/pools/{pool_id}/', auth=auth)
            print(f"   GET /pools/{pool_id}/ - Status: {detail_response.status_code}")
    
    # Test expenses endpoint
    print("\n3. Testing Expenses API...")
    response = requests.get(f'{BASE_URL}/expenses/', auth=auth)
    print(f"   GET /expenses/ - Status: {response.status_code}")
    if response.status_code == 200:
        expenses = response.json()
        print(f"   Found {len(expenses.get('results', expenses))} expenses")
        expense_data = expenses.get('results', expenses)
        if expense_data:
            expense_id = expense_data[0]['id']
            print(f"   First expense: {expense_data[0]['title']}")
            
            # Test expense detail
            detail_response = requests.get(f'{BASE_URL}/expenses/{expense_id}/', auth=auth)
            print(f"   GET /expenses/{expense_id}/ - Status: {detail_response.status_code}")
    
    # Test members endpoint
    print("\n4. Testing Members API...")
    response = requests.get(f'{BASE_URL}/members/', auth=auth)
    print(f"   GET /members/ - Status: {response.status_code}")
    if response.status_code == 200:
        members = response.json()
        print(f"   Found {len(members.get('results', members))} members")
    
    # Test transactions endpoint
    print("\n5. Testing Transactions API...")
    response = requests.get(f'{BASE_URL}/transactions/', auth=auth)
    print(f"   GET /transactions/ - Status: {response.status_code}")
    if response.status_code == 200:
        transactions = response.json()
        print(f"   Found {len(transactions.get('results', transactions))} transactions")
    
    # Test creating a new pool
    print("\n6. Testing Pool Creation...")
    new_pool_data = {
        'name': 'API Test Pool',
        'description': 'Created via API test',
        'default_split_method': 'equal'
    }
    response = requests.post(f'{BASE_URL}/pools/', 
                           json=new_pool_data, 
                           auth=auth,
                           headers={'Content-Type': 'application/json'})
    print(f"   POST /pools/ - Status: {response.status_code}")
    if response.status_code == 201:
        new_pool = response.json()
        print(f"   Created pool: {new_pool['name']}")
        
        # Test adding an expense to the new pool
        print("\n7. Testing Expense Creation...")
        new_expense_data = {
            'pool': new_pool['id'],
            'title': 'API Test Expense',
            'description': 'Created via API test',
            'amount': '100.00',
            'split_method': 'equal'
        }
        expense_response = requests.post(f'{BASE_URL}/expenses/', 
                                       json=new_expense_data, 
                                       auth=auth,
                                       headers={'Content-Type': 'application/json'})
        print(f"   POST /expenses/ - Status: {expense_response.status_code}")
        if expense_response.status_code == 201:
            new_expense = expense_response.json()
            print(f"   Created expense: {new_expense['title']}")
    
    print("\n" + "=" * 50)
    print("✅ API Testing Complete!")

if __name__ == '__main__':
    try:
        test_api_endpoints()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the API server.")
        print("   Make sure the Django development server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

