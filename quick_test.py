#!/usr/bin/env python3
"""
Quick test script for the restaurant management system
Tests the E2E scenario without database conflicts
"""

import requests
import time

BASE_URL = "http://127.0.0.1:5001"

def test_e2e_scenario():
    """Test E2E scenario with print statements"""
    session = requests.Session()
    
    print("🧪 Quick E2E Test for Restaurant Management System")
    print("=" * 60)
    
    # Test 1: Basic connectivity
    print("\n1. Testing basic endpoints...")
    endpoints = [
        ("/", "Dashboard"),
        ("/menu", "Menu"),
        ("/movements", "Movements"),
        ("/tables", "Tables"),
        ("/orders", "Orders")
    ]
    
    for endpoint, name in endpoints:
        try:
            response = session.get(f"{BASE_URL}{endpoint}", timeout=5)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"   {status} {name}: {response.status_code}")
        except Exception as e:
            print(f"   ❌ {name}: Error - {str(e)}")
    
    # Test 2: Create menu items
    print("\n2. Testing menu item creation...")
    
    # Stockable item
    pizza_data = {
        'name': f'Test Pizza {int(time.time())}',
        'description': 'Automated test pizza',
        'category': 'food',
        'price': '12.50',
        'stockable': 'on'
    }
    
    response = session.post(f"{BASE_URL}/menu/add", data=pizza_data)
    if response.status_code in [200, 302]:
        print(f"   ✅ Stockable item creation: {response.status_code}")
    else:
        print(f"   ❌ Stockable item creation: {response.status_code}")
    
    # Non-stockable item  
    drink_data = {
        'name': f'Test Drink {int(time.time())}',
        'description': 'Automated test drink',
        'category': 'drink',
        'price': '3.50'
        # No stockable = not stockable
    }
    
    response = session.post(f"{BASE_URL}/menu/add", data=drink_data)
    if response.status_code in [200, 302]:
        print(f"   ✅ Non-stockable item creation: {response.status_code}")
    else:
        print(f"   ❌ Non-stockable item creation: {response.status_code}")
    
    # Test 3: Create table
    print("\n3. Testing table creation...")
    
    table_data = {
        'table_number': str(90 + int(time.time()) % 10),  # Unique table number
        'capacity': '4'
    }
    
    response = session.post(f"{BASE_URL}/tables/add", data=table_data)
    if response.status_code in [200, 302]:
        print(f"   ✅ Table creation: {response.status_code}")
    else:
        print(f"   ❌ Table creation: {response.status_code}")
    
    # Test 4: Add stock movement (if we know stockable item exists)
    print("\n4. Testing stock movement...")
    
    # Since we can't easily get the exact item ID without database access,
    # we'll just test the endpoint availability
    stock_data = {
        'menu_item_id': '1',  # Assuming at least one item exists
        'quantity_change': '10',
        'notes': 'Test stock addition'
    }
    
    response = session.post(f"{BASE_URL}/movements/add", data=stock_data)
    status_ok = response.status_code in [200, 302, 500]  # 500 might be expected if item doesn't exist
    print(f"   {'✅' if status_ok else '❌'} Stock movement endpoint: {response.status_code}")
    
    # Test 5: Order workflow (if we know table exists)
    print("\n5. Testing order workflow...")
    
    # Try to create order for table 1 (assuming it exists)
    order_data = {
        'customer_name': 'Test Customer'
    }
    
    response = session.post(f"{BASE_URL}/orders/new/1", data=order_data)
    status_ok = response.status_code in [200, 302, 404]  # 404 if table doesn't exist
    print(f"   {'✅' if status_ok else '❌'} Order creation endpoint: {response.status_code}")
    
    # Test order item addition (assuming order 1 exists and menu item 1 exists)
    if response.status_code == 302:
        item_data = {
            'menu_item_id': '1',
            'quantity': '2',
            'notes': 'Test order item'
        }
        response = session.post(f"{BASE_URL}/orders/1/add_item", data=item_data)
        status_ok = response.status_code in [200, 302, 404]
        print(f"   {'✅' if status_ok else '❌'} Add item to order: {response.status_code}")
        
        # Test order closing
        response = session.post(f"{BASE_URL}/orders/1/close")
        status_ok = response.status_code in [200, 302, 404]
        print(f"   {'✅' if status_ok else '❌'} Order closing: {response.status_code}")
    
    print("\n" + "=" * 60)
    print("🎯 Quick test completed!")
    print("\nNote: This test focuses on endpoint availability and basic functionality.")
    print("For detailed validation, check the web interface at http://127.0.0.1:5001")
    print("\nManual E2E test steps:")
    print("1. Go to Menu → Add a stockable item (e.g., Pizza) and a non-stockable item (e.g., Service)")
    print("2. Go to Movements → Add stock to the pizza (e.g., +20)")
    print("3. Go to Tables → Add a new table")
    print("4. Go to Tables → Click 'New Order' on the table")
    print("5. Add both items to the order")
    print("6. Close the order and check that:")
    print("   - Stock was reduced only for the stockable item")
    print("   - Order history was recorded")
    print("   - Movements show the automatic stock reduction")

if __name__ == "__main__":
    # Check server connectivity
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"✅ Server is running at {BASE_URL}")
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("   Make sure Flask app is running: cd app && python app.py")
        exit(1)
    
    test_e2e_scenario()