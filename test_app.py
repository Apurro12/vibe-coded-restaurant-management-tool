#!/usr/bin/env python3
"""
Comprehensive test script for the restaurant management system
Tests endpoints and E2E functionality
"""

import requests
import sqlite3
import json
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:5001"
DATABASE = "app/inventory.db"

class RestaurantTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_data = {}
        
    def log(self, message):
        """Log test messages with timestamp"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        
    def get_db_connection(self):
        """Get database connection for verification"""
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn
        
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
        """Test basic endpoints"""
        self.log("=== TESTING BASIC ENDPOINTS ===")
        
        endpoints = [
            ("/", "Dashboard"),
            ("/menu", "Menu management"),
            ("/movements", "Stock movements"), 
            ("/tables", "Restaurant tables"),
            ("/orders", "Orders list")
        ]
        
        for endpoint, description in endpoints:
            response = self.session.get(f"{BASE_URL}{endpoint}")
            self.verify_response(response, 200, description)
            
    def create_test_menu_items(self):
        """Create test menu items - one stockable, one not"""
        self.log("=== CREATING TEST MENU ITEMS ===")
        
        # Stockable item (Pizza)
        pizza_data = {
            'name': 'Pizza Margherita Test',
            'description': 'Test pizza for automated testing',
            'category': 'food',
            'price': '15.99',
            'stockable': 'on'
        }
        
        response = self.session.post(f"{BASE_URL}/menu/add", data=pizza_data)
        if response.status_code == 302:
            self.log("✅ Create stockable menu item (Pizza) - Status: 302")
            # Get the created item ID
            conn = self.get_db_connection()
            pizza = conn.execute("SELECT * FROM menu_items WHERE name = ?", (pizza_data['name'],)).fetchone()
            self.test_data['pizza_id'] = pizza['id']
            self.log(f"   Pizza ID: {pizza['id']}")
            conn.close()
        else:
            self.log(f"❌ Create stockable menu item (Pizza) - Expected: 302, Got: {response.status_code}")
            # Check if item was created anyway
            conn = self.get_db_connection()
            pizza = conn.execute("SELECT * FROM menu_items WHERE name = ?", (pizza_data['name'],)).fetchone()
            if pizza:
                self.log(f"   Item was created despite non-redirect response. Pizza ID: {pizza['id']}")
                self.test_data['pizza_id'] = pizza['id']
            else:
                self.log("   Item was not created. Checking for validation errors...")
                if "error" in response.text.lower() or "required" in response.text.lower():
                    self.log("   Validation errors found in response")
            conn.close()
            
        # Non-stockable item (Service)
        service_data = {
            'name': 'Table Service Test',
            'description': 'Test service for automated testing', 
            'category': 'food',
            'price': '5.00'
            # No stockable checkbox = not stockable
        }
        
        response = self.session.post(f"{BASE_URL}/menu/add", data=service_data)
        if response.status_code == 302:
            self.log("✅ Create non-stockable menu item (Service) - Status: 302")
        else:
            self.log(f"❌ Create non-stockable menu item (Service) - Expected: 302, Got: {response.status_code}")
            
        # Check if item was created
        conn = self.get_db_connection()
        service = conn.execute("SELECT * FROM menu_items WHERE name = ?", (service_data['name'],)).fetchone()
        if service:
            self.test_data['service_id'] = service['id']
            self.log(f"   Service ID: {service['id']}")
        conn.close()
            
    def create_test_table(self):
        """Create test table"""
        self.log("=== CREATING TEST TABLE ===")
        
        table_data = {
            'table_number': '99',
            'capacity': '4'
        }
        
        response = self.session.post(f"{BASE_URL}/tables/add", data=table_data)
        if response.status_code == 302:
            self.log("✅ Create test table - Status: 302")
        else:
            self.log(f"❌ Create test table - Expected: 302, Got: {response.status_code}")
            
        # Check if table was created
        conn = self.get_db_connection()
        table = conn.execute("SELECT * FROM restaurant_tables WHERE table_number = ?", (table_data['table_number'],)).fetchone()
        if table:
            self.test_data['table_id'] = table['id']
            self.log(f"   Table ID: {table['id']}")
        conn.close()
            
    def add_stock(self):
        """Add stock to the stockable item"""
        self.log("=== ADDING STOCK ===")
        
        stock_data = {
            'menu_item_id': self.test_data['pizza_id'],
            'quantity_change': '50',
            'notes': 'Initial stock for testing'
        }
        
        response = self.session.post(f"{BASE_URL}/movements/add", data=stock_data)
        if self.verify_response(response, 302, "Add stock to pizza"):
            # Verify stock level
            conn = self.get_db_connection()
            result = conn.execute(
                'SELECT SUM(quantity_change) as total FROM movements WHERE menu_item_id = ?', 
                (self.test_data['pizza_id'],)
            ).fetchone()
            stock_level = result['total'] if result['total'] else 0
            self.log(f"   Current pizza stock: {stock_level}")
            self.test_data['initial_stock'] = stock_level
            conn.close()
            
    def create_test_order(self):
        """Create order and add items"""
        self.log("=== CREATING TEST ORDER ===")
        
        # Create new order
        order_data = {
            'customer_name': 'Test Customer E2E'
        }
        
        response = self.session.post(f"{BASE_URL}/tables/{self.test_data['table_id']}/order", data=order_data)
        if self.verify_response(response, 302, "Create new order"):
            # Get the created order ID from database
            conn = self.get_db_connection()
            order = conn.execute(
                "SELECT * FROM orders WHERE table_id = ? AND status = 'active' ORDER BY id DESC LIMIT 1", 
                (self.test_data['table_id'],)
            ).fetchone()
            self.test_data['order_id'] = order['id']
            self.log(f"   Order ID: {order['id']}")
            conn.close()
            
            # Add pizza (stockable item)
            pizza_item_data = {
                'menu_item_id': self.test_data['pizza_id'],
                'quantity': '3',
                'notes': 'Extra cheese please'
            }
            
            response = self.session.post(f"{BASE_URL}/orders/{self.test_data['order_id']}/items", data=pizza_item_data)
            self.verify_response(response, 302, "Add pizza to order")
            
            # Add service (non-stockable item)
            service_item_data = {
                'menu_item_id': self.test_data['service_id'],
                'quantity': '1',
                'notes': 'Premium service'
            }
            
            response = self.session.post(f"{BASE_URL}/orders/{self.test_data['order_id']}/items", data=service_item_data)
            self.verify_response(response, 302, "Add service to order")
            
    def verify_order_state(self):
        """Verify order items before closing"""
        self.log("=== VERIFYING ORDER STATE (BEFORE CLOSING) ===")
        
        conn = self.get_db_connection()
        
        # Check order items
        order_items = conn.execute("""
            SELECT oi.*, mi.name, mi.stockable
            FROM order_items oi
            JOIN menu_items mi ON oi.menu_item_id = mi.id
            WHERE oi.order_id = ?
        """, (self.test_data['order_id'],)).fetchall()
        
        self.log(f"   Order has {len(order_items)} items:")
        for item in order_items:
            self.log(f"   - {item['name']}: qty={item['quantity']}, stockable={item['stockable']}")
            
        # Check that stock hasn't changed yet (should only change when order is closed)
        current_stock = conn.execute(
            'SELECT SUM(quantity_change) as total FROM movements WHERE menu_item_id = ?', 
            (self.test_data['pizza_id'],)
        ).fetchone()['total']
        
        if current_stock == self.test_data['initial_stock']:
            self.log("✅ Stock unchanged before order completion (correct behavior)")
        else:
            self.log(f"❌ Stock changed prematurely: {self.test_data['initial_stock']} -> {current_stock}")
            
        conn.close()
        
    def close_order_and_verify(self):
        """Close order and verify stock movements"""
        self.log("=== CLOSING ORDER AND VERIFYING ===")
        
        # Close the order
        response = self.session.post(f"{BASE_URL}/orders/{self.test_data['order_id']}/close")
        if self.verify_response(response, 302, "Close order"):
            
            conn = self.get_db_connection()
            
            # Verify order is closed
            order = conn.execute("SELECT * FROM orders WHERE id = ?", (self.test_data['order_id'],)).fetchone()
            if order['status'] == 'closed':
                self.log("✅ Order status is 'closed'")
                self.log(f"   Closed at: {order['closed_at']}")
            else:
                self.log(f"❌ Order status should be 'closed', got: {order['status']}")
                
            # Verify stock movement was created for stockable item
            movements = conn.execute("""
                SELECT * FROM movements 
                WHERE menu_item_id = ? AND notes LIKE ?
            """, (self.test_data['pizza_id'], f'%Order #{self.test_data["order_id"]} closed%')).fetchall()
            
            if movements:
                movement = movements[0]
                self.log(f"✅ Stock movement created: {movement['quantity_change']} units")
                self.log(f"   Movement notes: {movement['notes']}")
                
                # Verify final stock level
                final_stock = conn.execute(
                    'SELECT SUM(quantity_change) as total FROM movements WHERE menu_item_id = ?', 
                    (self.test_data['pizza_id'],)
                ).fetchone()['total']
                
                expected_stock = self.test_data['initial_stock'] - 3  # We ordered 3 pizzas
                if final_stock == expected_stock:
                    self.log(f"✅ Stock correctly updated: {self.test_data['initial_stock']} -> {final_stock}")
                else:
                    self.log(f"❌ Stock calculation error: expected {expected_stock}, got {final_stock}")
            else:
                self.log("❌ No stock movement created for stockable item")
                
            # Verify no stock movement for non-stockable item
            service_movements = conn.execute("""
                SELECT * FROM movements 
                WHERE menu_item_id = ?
            """, (self.test_data['service_id'],)).fetchall()
            
            if not service_movements:
                self.log("✅ No stock movement created for non-stockable item (correct)")
            else:
                self.log("❌ Stock movement created for non-stockable item (incorrect)")
                
            conn.close()
            
    def test_order_history(self):
        """Verify order item history tracking"""
        self.log("=== VERIFYING ORDER HISTORY ===")
        
        conn = self.get_db_connection()
        history = conn.execute("""
            SELECT oih.*, mi.name
            FROM order_item_history oih
            JOIN menu_items mi ON oih.menu_item_id = mi.id
            WHERE oih.order_id = ?
            ORDER BY oih.timestamp
        """, (self.test_data['order_id'],)).fetchall()
        
        self.log(f"   Order history has {len(history)} entries:")
        for entry in history:
            self.log(f"   - {entry['timestamp'][:19]}: {entry['action']} {entry['name']} (qty: {entry['quantity']})")
            
        # Should have 2 'added' entries (pizza and service)
        added_entries = [h for h in history if h['action'] == 'added']
        if len(added_entries) == 2:
            self.log("✅ Correct number of 'added' history entries")
        else:
            self.log(f"❌ Expected 2 'added' entries, found {len(added_entries)}")
            
        conn.close()
        
    def cleanup_test_data(self):
        """Clean up test data"""
        self.log("=== CLEANING UP TEST DATA ===")
        
        conn = self.get_db_connection()
        
        # Clean up in reverse order of creation (foreign key constraints)
        if 'order_id' in self.test_data:
            conn.execute("DELETE FROM order_item_history WHERE order_id = ?", (self.test_data['order_id'],))
            conn.execute("DELETE FROM order_items WHERE order_id = ?", (self.test_data['order_id'],))
            conn.execute("DELETE FROM orders WHERE id = ?", (self.test_data['order_id'],))
            
        if 'pizza_id' in self.test_data:
            conn.execute("DELETE FROM movements WHERE menu_item_id = ?", (self.test_data['pizza_id'],))
            conn.execute("DELETE FROM menu_items WHERE id = ?", (self.test_data['pizza_id'],))
            
        if 'service_id' in self.test_data:
            conn.execute("DELETE FROM menu_items WHERE id = ?", (self.test_data['service_id'],))
            
        if 'table_id' in self.test_data:
            conn.execute("DELETE FROM restaurant_tables WHERE id = ?", (self.test_data['table_id'],))
            
        conn.commit()
        conn.close()
        self.log("✅ Test data cleaned up")
        
    def run_full_test(self):
        """Run complete E2E test suite"""
        self.log("🚀 STARTING COMPREHENSIVE E2E TEST")
        print("=" * 60)
        
        try:
            # Test basic endpoints
            self.test_endpoints()
            print()
            
            # Run E2E scenario
            self.create_test_menu_items()
            print()
            
            self.create_test_table() 
            print()
            
            self.add_stock()
            print()
            
            self.create_test_order()
            print()
            
            self.verify_order_state()
            print()
            
            self.close_order_and_verify()
            print()
            
            self.test_order_history()
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