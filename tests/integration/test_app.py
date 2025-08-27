#!/usr/bin/env python3
"""
Comprehensive test script for the restaurant management system
Tests endpoints and E2E functionality
"""

#DATABASE_PATH=/Users/camiloleonel/Desktop/personal/14_mama/tests/test.db python app/app.py


import requests
import sqlite3
import json
import time
import sys
import os
from datetime import datetime


# Add the app directory to the Python path so we can import utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'app'))
from utils import init_database, get_db_connection


import os
BASE_URL = "http://127.0.0.1:5000"
os.environ["DATABASE_PATH"] = "/Users/camiloleonel/Desktop/personal/14_mama/tests/test.db"


def delete_database():
    """Completely delete the database file"""
    import os

    DATABASE = os.environ.get("DATABASE_PATH")
    if not DATABASE:
        assert False, "DATABASE_PATH environment variable not set"

    if os.path.exists(DATABASE):
        try:
            os.remove(DATABASE)
        except OSError as e:
            pass
        


class RestaurantTester:
    def __init__(self):
        self.session = requests.Session()
        self.database_status = {
            "menu_items": []   
        }

        delete_database()
        init_database()

    def log(self, message):
        """Log test messages with timestamp"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        
        
    def verify_response(self, response, expected_status=200, description=""):
        """Verify HTTP response status"""
        if response.status_code == expected_status:
            self.log(f"✅ {description} - Status: {response.status_code}")
            return True
        else:
            self.log(f"❌ {description} - Expected: {expected_status}, Got: {response.status_code}")
            if response.text:
                self.log(f"   Response: {response.text[:200]}")
            return False
            
    def test_endpoints(self):
        """Test basic GET endpoints"""
        self.log("=== TESTING BASIC GET ENDPOINTS ===")
        
        endpoints = [
            ("/", "Dashboard"),
            ("/menu", "Menu management"),
            ("/menu/audit", "Menu audit trail"),
            ("/movements", "Stock movements"), 
            ("/movements/add", "Add stock movement form"),
            ("/tables", "Restaurant tables"),
            ("/tables/add", "Add table form"),
            ("/orders", "Orders list")
        ]
        
        for endpoint, description in endpoints:
            response = self.session.get(f"{BASE_URL}{endpoint}")
            assert response.status_code == 200, f"Failed to access {endpoint}"
            self.log(f"✅ {description} - Status: 200")
            
    def create_test_menu_items(self):
        """Create test menu items - one stockable, one not"""
        self.log("=== CREATING TEST MENU ITEMS ===")
        
        # Stockable item (Pizza)
        pizza_data = {
            'name': 'Pizza Margherita Test',
            'description': 'Test pizza for automated testing',
            'category': 'food',
            'price': 15.99,
            'stockable': 'on'
        }
        
        response = self.session.post(f"{BASE_URL}/menu/add", data=pizza_data)
        assert response.status_code == 200, "Failed to create a pizza"
        self.log("✅ Create stockable menu item (Pizza) - Status: 200")
        # Get the created item ID
        conn = get_db_connection()
        pizza = conn.execute("SELECT * FROM menu_items WHERE name = ?", (pizza_data['name'],)).fetchone()
        
        pizza_data["stockable"] = 1
        pizza_data["id"] = 1
        assert pizza_data == dict(pizza)
        self.database_status["menu_items"].append(dict(pizza))
        
        conn.close()
            
        # Non-stockable item (Service)
        service_data = {
            'name': 'Table Service Test',
            'description': 'Test service for automated testing', 
            'category': 'food',
            'price': 5.00
            # No stockable checkbox = not stockable
        }
        
        response = self.session.post(f"{BASE_URL}/menu/add", data=service_data)
        assert response.status_code == 200, "Failed to create a service"
        self.log("✅ Create non-stockable menu item (Service) - Status: 200")
            
        # Check if item was created
        conn = get_db_connection()
        service = conn.execute("SELECT * FROM menu_items WHERE name = ?", (service_data['name'],)).fetchone()


        service_data["stockable"] = 0
        service_data["id"] = 2
        assert service_data == dict(service)
        self.database_status["menu_items"].append(service_data)
        conn.close()

    def test_menu_endpoints(self):
        """Test comprehensive menu endpoints"""
        self.log("=== TESTING MENU ENDPOINTS ===")
        
        # Test GET /menu/edit/<id> for created pizza
        pizza_id = self.database_status["menu_items"][0]["id"]
        response = self.session.get(f"{BASE_URL}/menu/edit/{pizza_id}")
        assert response.status_code == 200, "Failed to get menu edit form"
        self.log(f"✅ Get menu edit form for pizza (ID: {pizza_id}) - Status: 200")
        
        # Test POST /menu/edit/<id> - update pizza description
        edit_data = {
            'name': 'Pizza Margherita Test Updated',
            'description': 'Updated test pizza description',
            'category': 'food',
            'price': '16.99',
            'stockable': 'on'
        }
        
        response = self.session.post(f"{BASE_URL}/menu/edit/{pizza_id}", data=edit_data)
        assert response.status_code == 200, "Failed to edit menu item"
        self.log("✅ Update pizza menu item - Status: 200")
        
        # Verify the edit in database
        conn = get_db_connection()
        updated_pizza = conn.execute("SELECT * FROM menu_items WHERE id = ?", (pizza_id,)).fetchone()
        assert updated_pizza['name'] == 'Pizza Margherita Test Updated', "Pizza name not updated"
        assert float(updated_pizza['price']) == 16.99, "Pizza price not updated"
        self.log("✅ Menu item edit verified in database")
        
        # Check menu audit trail
        audit_entries = conn.execute("SELECT * FROM menu_audit WHERE menu_item_id = ?", (pizza_id,)).fetchall()
        assert len(audit_entries) > 0, "No audit entries found for menu edit"
        self.log(f"✅ Menu audit trail has {len(audit_entries)} entries")
        conn.close()
        
        # Update database_status with new data
        self.database_status["menu_items"][0].update({
            'name': 'Pizza Margherita Test Updated',
            'description': 'Updated test pizza description',
            'price': 16.99
        })
            
    def create_test_table(self):
        """Create test table"""
        self.log("=== CREATING TEST TABLE ===")
        
        table_data = {
            'table_number': 99,
            'capacity': 4
        }
        
        response = self.session.post(f"{BASE_URL}/tables/add", data=table_data)
        assert response.status_code == 200, "Bad status code"
        self.log("✅ Create test table- Status: 200")

        # Check if table was created
        conn = get_db_connection()
        table = conn.execute("SELECT * FROM restaurant_tables WHERE table_number = ?", (table_data['table_number'],)).fetchone()
        conn.commit()

        table_data["status"] = 'available'
        table_data["customer_name"] = None
        table_data["open_order_number"] = None
        
        assert table_data == dict(table)
        self.log(f"   Table ID: {table['table_number']}")
        conn.close()

    def test_tables_endpoints(self):
        """Test comprehensive tables endpoints"""
        self.log("=== TESTING TABLES ENDPOINTS ===")
        
        # Test creating an additional table
        new_table_data = {
            'table_number': '88',
            'capacity': '6'
        }
        
        response = self.session.post(f"{BASE_URL}/tables/add", data=new_table_data)
        assert response.status_code == 200, "Failed to create additional table"
        self.log("✅ Create additional table (88) - Status: 200")
        
        # Verify both tables exist
        conn = get_db_connection()
        tables = conn.execute("SELECT * FROM restaurant_tables ORDER BY table_number").fetchall()
        assert len(tables) == 2, f"Expected 2 tables, found {len(tables)}"
        
        table_88 = next((t for t in tables if t['table_number'] == 88), None)
        table_99 = next((t for t in tables if t['table_number'] == 99), None)
        
        assert table_88 is not None, "Table 88 not found"
        assert table_99 is not None, "Table 99 not found"
        assert table_88['capacity'] == 6, f"Expected capacity 6, got {table_88['capacity']}"
        assert table_99['capacity'] == 4, f"Expected capacity 4, got {table_99['capacity']}"
        
        self.log("✅ Both tables verified in database")
        self.log(f"   Table 88: capacity {table_88['capacity']}, status {table_88['status']}")
        self.log(f"   Table 99: capacity {table_99['capacity']}, status {table_99['status']}")
        conn.close()
            
    def add_stock(self):
        """Add stock to the stockable item"""
        self.log("=== ADDING STOCK ===")
        
        stock_data = {
            'menu_item_id': self.database_status["menu_items"][0]["id"],
            'quantity_change': '50',
            'notes': 'Initial stock for testing'
        }
        
        response = self.session.post(f"{BASE_URL}/movements/add", data=stock_data)
        assert response.status_code == 200, "Failed to add stock"
        self.log("✅ Add stock to pizza - Status: 200")
        
        # Verify stock level
        conn = get_db_connection()
        result = conn.execute(
            'SELECT SUM(quantity_change) as total FROM movements WHERE menu_item_id = ?', 
            (self.database_status["menu_items"][0]["id"],)
        ).fetchone()
        stock_level = result['total'] if result['total'] else 0
        assert stock_level == 50, f"Expected stock level 50, got {stock_level}"
        self.log(f"   Current pizza stock: {stock_level}")
        
        # Store initial stock for later tests
        self.database_status["initial_stock"] = stock_level
        conn.close()
            
    def create_test_order(self):
        """Create order and add items"""
        self.log("=== CREATING TEST ORDER ===")
        
        # Create new order
        order_data = {
            'customer_name': 'Test Customer E2E'
        }
        
        response = self.session.post(f"{BASE_URL}/orders/new/99", data=order_data, allow_redirects=False)
        assert response.status_code == 302, f"Failed to create order, got status {response.status_code}"
        self.log("✅ Create new order - Status: 302 (redirect)")
        
        # Get the created order ID from database
        conn = get_db_connection()
        order = conn.execute(
            "SELECT * FROM orders WHERE table_id = ? AND status = 'active' ORDER BY id DESC LIMIT 1", 
            (99,)
        ).fetchone()
        assert order is not None, "Order was not created"
        
        order_id = order['id']
        self.database_status["order_id"] = order_id
        self.log(f"   Order ID: {order_id}")
        conn.close()
        
        # Add pizza (stockable item)
        pizza_item_data = {
            'menu_item_id': self.database_status["menu_items"][0]["id"],  # Pizza
            'quantity': '3',
            'notes': 'Extra cheese please'
        }
        
        response = self.session.post(f"{BASE_URL}/orders/{order_id}/add_item", data=pizza_item_data, allow_redirects=False)
        assert response.status_code == 302, f"Failed to add pizza to order, got status {response.status_code}"
        self.log("✅ Add pizza to order - Status: 302 (redirect)")
        
        # Add service (non-stockable item)
        service_item_data = {
            'menu_item_id': self.database_status["menu_items"][1]["id"],  # Service
            'quantity': '1',
            'notes': 'Premium service'
        }
        
        response = self.session.post(f"{BASE_URL}/orders/{order_id}/add_item", data=service_item_data, allow_redirects=False)
        assert response.status_code == 302, f"Failed to add service to order, got status {response.status_code}"
        self.log("✅ Add service to order - Status: 302 (redirect)")
            
    def verify_order_state(self):
        """Verify order items before closing"""
        self.log("=== VERIFYING ORDER STATE (BEFORE CLOSING) ===")
        
        conn = get_db_connection()
        
        # Check order items
        order_items = conn.execute("""
            SELECT oi.*, mi.name, mi.stockable
            FROM order_items oi
            JOIN menu_items mi ON oi.menu_item_id = mi.id
            WHERE oi.order_id = ?
        """, (self.database_status["order_id"],)).fetchall()
        
        assert len(order_items) == 2, f"Expected 2 order items, got {len(order_items)}"
        self.log(f"   Order has {len(order_items)} items:")
        for item in order_items:
            self.log(f"   - {item['name']}: qty={item['quantity']}, stockable={item['stockable']}")
            
        # Verify order items details
        pizza_item = next((item for item in order_items if item['name'] == 'Pizza Margherita Test Updated'), None)
        service_item = next((item for item in order_items if item['name'] == 'Table Service Test'), None)
        
        assert pizza_item is not None, "Pizza item not found in order"
        assert service_item is not None, "Service item not found in order"
        assert pizza_item['quantity'] == 3, f"Expected pizza quantity 3, got {pizza_item['quantity']}"
        assert service_item['quantity'] == 1, f"Expected service quantity 1, got {service_item['quantity']}"
            
        # Check that stock hasn't changed yet (should only change when order is closed)
        current_stock = conn.execute(
            'SELECT SUM(quantity_change) as total FROM movements WHERE menu_item_id = ?', 
            (self.database_status["menu_items"][0]["id"],)
        ).fetchone()['total']
        
        # Use the updated stock level after movements test
        expected_current_stock = self.database_status.get('current_stock_before_order', self.database_status["initial_stock"])
        assert current_stock == expected_current_stock, f"Stock changed unexpectedly: {expected_current_stock} -> {current_stock}"
        self.log("✅ Stock unchanged before order completion (correct behavior)")
            
        conn.close()
        
    def close_order_and_verify(self):
        """Close order and verify stock movements"""
        self.log("=== CLOSING ORDER AND VERIFYING ===")
        
        # Close the order with payment information
        # First get the order total to calculate payment
        conn = get_db_connection()
        order_total_result = conn.execute('''
            SELECT SUM(oi.quantity * oi.unit_price) as total
            FROM order_items oi
            WHERE oi.order_id = ?
        ''', (self.database_status['order_id'],)).fetchone()
        order_total = order_total_result['total'] or 0
        conn.close()
        
        payment_data = {
            'payment_method[]': ['cash'],
            'amount[]': [str(order_total)]
        }
        
        response = self.session.post(f"{BASE_URL}/orders/{self.database_status['order_id']}/close", 
                                   data=payment_data, allow_redirects=False)
        assert response.status_code == 302, f"Failed to close order, got status {response.status_code}"
        self.log(f"✅ Close order with payment ${order_total} - Status: 302 (redirect)")
        
        conn = get_db_connection()
        
        # Verify order is closed
        order = conn.execute("SELECT * FROM orders WHERE id = ?", (self.database_status['order_id'],)).fetchone()
        assert order['status'] == 'closed', f"Order status should be 'closed', got: {order['status']}"
        assert order['closed_at'] is not None, "Order closed_at should not be None"
        self.log("✅ Order status is 'closed'")
        self.log(f"   Closed at: {order['closed_at']}")
            
        # Verify stock movement was created for stockable item
        movements = conn.execute("""
            SELECT * FROM movements 
            WHERE menu_item_id = ? AND notes LIKE ?
        """, (self.database_status["menu_items"][0]["id"], f'%Order #{self.database_status["order_id"]} closed%')).fetchall()
        
        assert len(movements) > 0, "No stock movement created for stockable item"
        movement = movements[0]
        assert movement['quantity_change'] == -3, f"Expected quantity change -3, got {movement['quantity_change']}"
        self.log(f"✅ Stock movement created: {movement['quantity_change']} units")
        self.log(f"   Movement notes: {movement['notes']}")
        
        # Verify final stock level
        final_stock = conn.execute(
            'SELECT SUM(quantity_change) as total FROM movements WHERE menu_item_id = ?', 
            (self.database_status["menu_items"][0]["id"],)
        ).fetchone()['total']
        
        # Use the current stock before order (65) minus the 3 pizzas ordered = 62
        expected_stock = self.database_status.get('current_stock_before_order', self.database_status['initial_stock']) - 3
        assert final_stock == expected_stock, f"Stock calculation error: expected {expected_stock}, got {final_stock}"
        self.log(f"✅ Stock correctly updated: {self.database_status.get('current_stock_before_order', self.database_status['initial_stock'])} -> {final_stock}")
            
        # Verify no stock movement for non-stockable item
        service_movements = conn.execute("""
            SELECT * FROM movements 
            WHERE menu_item_id = ?
        """, (self.database_status["menu_items"][1]["id"],)).fetchall()
        
        assert len(service_movements) == 0, "Stock movement created for non-stockable item (incorrect)"
        self.log("✅ No stock movement created for non-stockable item (correct)")
            
        conn.close()
            
    def test_order_history(self):
        """Verify order item history tracking"""
        self.log("=== VERIFYING ORDER HISTORY ===")
        
        conn = get_db_connection()
        history = conn.execute("""
            SELECT oih.*, mi.name
            FROM order_item_history oih
            JOIN menu_items mi ON oih.menu_item_id = mi.id
            WHERE oih.order_id = ?
            ORDER BY oih.timestamp
        """, (self.database_status['order_id'],)).fetchall()
        
        assert len(history) == 2, f"Expected 2 history entries, got {len(history)}"
        self.log(f"   Order history has {len(history)} entries:")
        for entry in history:
            self.log(f"   - {entry['timestamp'][:19]}: {entry['action']} {entry['name']} (qty: {entry['quantity']})")
            
        # Should have 2 'added' entries (pizza and service)
        added_entries = [h for h in history if h['action'] == 'added']
        assert len(added_entries) == 2, f"Expected 2 'added' entries, found {len(added_entries)}"
        
        # Verify specific entries
        pizza_entry = next((h for h in added_entries if h['name'] == 'Pizza Margherita Test Updated'), None)
        service_entry = next((h for h in added_entries if h['name'] == 'Table Service Test'), None)
        
        assert pizza_entry is not None, "Pizza history entry not found"
        assert service_entry is not None, "Service history entry not found"
        assert pizza_entry['quantity'] == 3, f"Expected pizza history quantity 3, got {pizza_entry['quantity']}"
        assert service_entry['quantity'] == 1, f"Expected service history quantity 1, got {service_entry['quantity']}"
        assert pizza_entry['action'] == 'added', f"Expected pizza action 'added', got {pizza_entry['action']}"
        assert service_entry['action'] == 'added', f"Expected service action 'added', got {service_entry['action']}"
        
        self.log("✅ Correct number of 'added' history entries")
        self.log("✅ History entries contain correct data")
            
        conn.close()

    def test_orders_endpoints(self):
        """Test comprehensive orders endpoints"""
        self.log("=== TESTING ORDERS ENDPOINTS ===")
        
        # Test GET /orders/new/<table_id> 
        response = self.session.get(f"{BASE_URL}/orders/new/88")
        assert response.status_code == 200, "Failed to get new order form"
        self.log("✅ Get new order form for table 88 - Status: 200")
        
        # Test creating a second order on table 88
        order_data = {
            'customer_name': 'Second Customer Test'
        }
        
        response = self.session.post(f"{BASE_URL}/orders/new/88", data=order_data, allow_redirects=False)
        assert response.status_code == 302, f"Failed to create second order, got status {response.status_code}"
        self.log("✅ Create second order on table 88 - Status: 302 (redirect)")
        
        # Get the new order ID
        conn = get_db_connection()
        second_order = conn.execute(
            "SELECT * FROM orders WHERE table_id = ? AND status = 'active' ORDER BY id DESC LIMIT 1", 
            (88,)
        ).fetchone()
        assert second_order is not None, "Second order was not created"
        second_order_id = second_order['id']
        self.log(f"   Second Order ID: {second_order_id}")
        
        # Test GET /orders/<order_id>
        response = self.session.get(f"{BASE_URL}/orders/{second_order_id}")
        assert response.status_code == 200, "Failed to get order detail page"
        self.log(f"✅ Get order detail page (Order {second_order_id}) - Status: 200")
        
        # Test POST /orders/<order_id>/add_item - Add pizza to second order
        add_item_data = {
            'menu_item_id': self.database_status["menu_items"][0]["id"],  # Updated pizza
            'quantity': '2',
            'notes': 'Less cheese this time'
        }
        
        response = self.session.post(f"{BASE_URL}/orders/{second_order_id}/add_item", data=add_item_data, allow_redirects=False)
        assert response.status_code == 302, f"Failed to add item to second order, got status {response.status_code}"
        self.log("✅ Add pizza to second order - Status: 302 (redirect)")
        
        # Verify item was added
        order_items = conn.execute(
            "SELECT * FROM order_items WHERE order_id = ?", 
            (second_order_id,)
        ).fetchall()
        assert len(order_items) == 1, f"Expected 1 item in second order, got {len(order_items)}"
        added_item = order_items[0]
        assert added_item['quantity'] == 2, f"Expected quantity 2, got {added_item['quantity']}"
        assert added_item['notes'] == 'Less cheese this time', "Item notes don't match"
        self.log("✅ Order item verified in database")
        
        # Test POST /orders/<order_id>/items/<item_id>/edit
        item_id = added_item['id']
        edit_item_data = {
            'quantity': '3',
            'notes': 'Changed to extra cheese'
        }
        
        response = self.session.post(f"{BASE_URL}/orders/{second_order_id}/items/{item_id}/edit", data=edit_item_data, allow_redirects=False)
        assert response.status_code == 302, f"Failed to edit order item, got status {response.status_code}"
        self.log("✅ Edit order item quantity and notes - Status: 302 (redirect)")
        
        # Verify edit
        edited_item = conn.execute("SELECT * FROM order_items WHERE id = ?", (item_id,)).fetchone()
        assert edited_item['quantity'] == 3, f"Expected quantity 3, got {edited_item['quantity']}"
        assert edited_item['notes'] == 'Changed to extra cheese', "Edited notes don't match"
        
        # Check order history for edit
        edit_history = conn.execute(
            "SELECT * FROM order_item_history WHERE order_id = ? AND action IN ('old_edited', 'new_edited')", 
            (second_order_id,)
        ).fetchall()
        assert len(edit_history) >= 2, "Expected old_edited and new_edited history entries"
        self.log("✅ Order item edit verified with history tracking")
        
        # Test POST /orders/<order_id>/items/<item_id>/remove
        response = self.session.post(f"{BASE_URL}/orders/{second_order_id}/items/{item_id}/remove", allow_redirects=False)
        assert response.status_code == 302, f"Failed to remove order item, got status {response.status_code}"
        self.log("✅ Remove order item - Status: 302 (redirect)")
        
        # Verify removal
        remaining_items = conn.execute("SELECT * FROM order_items WHERE order_id = ?", (second_order_id,)).fetchall()
        assert len(remaining_items) == 0, "Item was not removed from order"
        
        # Check removal history
        removal_history = conn.execute(
            "SELECT * FROM order_item_history WHERE order_id = ? AND action = 'removed'", 
            (second_order_id,)
        ).fetchall()
        assert len(removal_history) == 1, "Expected removal history entry"
        self.log("✅ Order item removal verified with history tracking")
        
        conn.close()

    def test_movements_endpoints(self):
        """Test comprehensive movements endpoints"""  
        self.log("=== TESTING MOVEMENTS ENDPOINTS ===")
        
        # Test adding negative stock movement (stock reduction)
        reduction_data = {
            'menu_item_id': self.database_status["menu_items"][0]["id"],  # Pizza
            'quantity_change': '-10',
            'notes': 'Manual stock reduction for testing'
        }
        
        response = self.session.post(f"{BASE_URL}/movements/add", data=reduction_data)
        assert response.status_code == 200, "Failed to add stock reduction"
        self.log("✅ Add stock reduction movement - Status: 200")
        
        # Verify the movement was recorded
        conn = get_db_connection()
        movements = conn.execute(
            "SELECT * FROM movements WHERE menu_item_id = ? AND notes LIKE '%Manual stock reduction%'", 
            (self.database_status["menu_items"][0]["id"],)
        ).fetchall()
        assert len(movements) == 1, "Stock reduction movement not found"
        
        reduction_movement = movements[0]
        assert reduction_movement['quantity_change'] == -10, f"Expected -10, got {reduction_movement['quantity_change']}"
        self.log("✅ Stock reduction movement verified in database")
        
        # Test adding positive stock movement (stock addition)  
        addition_data = {
            'menu_item_id': self.database_status["menu_items"][0]["id"],  # Pizza
            'quantity_change': '25',
            'notes': 'Additional stock delivery'
        }
        
        response = self.session.post(f"{BASE_URL}/movements/add", data=addition_data)
        assert response.status_code == 200, "Failed to add stock addition"
        self.log("✅ Add stock addition movement - Status: 200")
        
        # Verify current stock calculation includes all movements
        current_stock = conn.execute(
            'SELECT SUM(quantity_change) as total FROM movements WHERE menu_item_id = ?', 
            (self.database_status["menu_items"][0]["id"],)
        ).fetchone()['total']
        
        # At this point: Initial stock (50) + manual reduction (-10) + addition (25) = 65
        # Order consumption (-3) hasn't happened yet as it occurs in the main E2E flow
        expected_stock = 50 - 10 + 25
        assert current_stock == expected_stock, f"Expected stock {expected_stock}, got {current_stock}"
        self.log(f"✅ Stock calculation verified: {current_stock} units (before order consumption)")
        
        # Update our tracking for later tests
        self.database_status["current_stock_before_order"] = current_stock
        
        conn.close()
        


    def cleanup_test_data(self):
        """Clean up test data"""
        self.log("=== DELETING DATABASE ===")
        
        delete_database()
        self.log("✅ Test data cleaned up")
        

    def run_full_test(self):
        """Run complete E2E test suite"""
        self.log("🚀 STARTING COMPREHENSIVE E2E TEST")
        print("=" * 60)
        
        try:
            # Test basic GET endpoints
            self.test_endpoints()
            print()
            
            # Create test data
            self.create_test_menu_items()
            print()
            
            # Test comprehensive menu endpoints
            self.test_menu_endpoints()
            print()
            
            self.create_test_table() 
            print()
            
            # Test comprehensive tables endpoints
            self.test_tables_endpoints()
            print()
            
            self.add_stock()
            print()
            
            # Test comprehensive movements endpoints
            self.test_movements_endpoints()
            print()
            
            # Run main E2E order flow
            self.create_test_order()
            print()
            
            self.verify_order_state()
            print()
            
            self.close_order_and_verify()
            print()
            
            self.test_order_history()
            print()
            
            # Test comprehensive orders endpoints
            self.test_orders_endpoints()
            print()
            
            print("=" * 60)
            self.log("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
            
        except Exception as e:
            self.log(f"❌ TEST FAILED WITH ERROR: {str(e)}")
            raise
        finally:
            self.cleanup_test_data()

if __name__ == "__main__":
    # Quick connectivity test first
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"✅ Server is running at {BASE_URL}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print(f"   Make sure the Flask app is running: python app/app.py")
        exit(1)
        
    # Run the tests
    tester = RestaurantTester()
    tester.run_full_test()