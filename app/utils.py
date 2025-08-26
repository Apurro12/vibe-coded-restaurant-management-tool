import sqlite3
import os
from datetime import datetime

DATABASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'inventory.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# TODO: this logic should be updated, I need to save the partial changes
def get_current_stock_for_menu_item(menu_item_id):
    """Calculate current stock for a menu item based on movements"""
    conn = get_db_connection()
    result = conn.execute(
        'SELECT SUM(quantity_change) as total FROM movements WHERE menu_item_id = ?', 
        (menu_item_id,)
    ).fetchone()
    conn.close()
    return result['total'] if result['total'] else 0

def log_menu_audit(menu_item_id, action, old_values=None, new_values=None):
    """Log menu item changes for audit trail"""
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO menu_audit (menu_item_id, action, old_values, new_values, timestamp, user_info)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (menu_item_id, action, old_values, new_values, datetime.now(), 'system'))
    conn.commit()
    conn.close()

def init_database():
    """Initialize database tables"""
    conn = get_db_connection()

    
    # Movements tracking table
    conn.execute('''CREATE TABLE IF NOT EXISTS movements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        menu_item_id INTEGER,
        menu_item_name TEXT NOT NULL,
        quantity_change INTEGER NOT NULL,
        movement_type TEXT NOT NULL,
        notes TEXT,
        partial_stock INTEGER, 
        date DATETIME NOT NULL
    )''')
    
    # Restaurant tables
    conn.execute('''CREATE TABLE IF NOT EXISTS restaurant_tables (
        table_number INTEGER NOT NULL UNIQUE,
        capacity INTEGER NOT NULL,
        status TEXT NOT NULL,
        customer_name TEXT  
    )''')
    
    # Menu items (food and drinks)
    conn.execute('''CREATE TABLE IF NOT EXISTS menu_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        category TEXT NOT NULL,
        price DECIMAL(10,2) NOT NULL,
        stockable BOOLEAN DEFAULT 0
    )''')
    
    # Customer orders
    conn.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_id INTEGER NOT NULL,
        customer_name TEXT,
        status TEXT NOT NULL,
        created_at DATETIME NOT NULL,
        closed_at DATETIME,
        total_amount DECIMAL(10,2)
    )''')
    
    # Individual items in an order
    conn.execute('''CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        menu_item_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 1,
        unit_price DECIMAL(10,2) NOT NULL,
        notes TEXT,
        FOREIGN KEY (order_id) REFERENCES orders (id),
        FOREIGN KEY (menu_item_id) REFERENCES menu_items (id)
    )''')
    
    # Order payments - supports split payments
    conn.execute('''CREATE TABLE IF NOT EXISTS order_payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        payment_method TEXT NOT NULL,
        amount DECIMAL(10,2) NOT NULL,
        notes TEXT,
        created_at DATETIME NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders (id)
    )''')
    
    # Menu audit trail
    conn.execute('''CREATE TABLE IF NOT EXISTS menu_audit (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        menu_item_id INTEGER,
        action TEXT NOT NULL,
        old_values TEXT,
        new_values TEXT,
        timestamp DATETIME NOT NULL,
        user_info TEXT
    )''')
    
    # Order item history - tracks all changes to order items
    conn.execute('''CREATE TABLE IF NOT EXISTS order_item_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        menu_item_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        quantity INTEGER,
        unit_price DECIMAL(10,2),
        notes TEXT,
        timestamp DATETIME NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders (id),
        FOREIGN KEY (menu_item_id) REFERENCES menu_items (id)
    )''')
    
    conn.commit()
    conn.close()