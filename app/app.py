from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)
DATABASE = 'inventory.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

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

# Main page: shows stockable menu items and current stock levels
@app.route('/')
def index():
    conn = get_db_connection()
    stockable_items = conn.execute('SELECT * FROM menu_items WHERE stockable = 1 ORDER BY name').fetchall()
    
    # Get current stock for each stockable item
    items_with_stock = []
    for item in stockable_items:
        current_stock = get_current_stock_for_menu_item(item['id'])
        items_with_stock.append({
            'id': item['id'],
            'name': item['name'],
            'unit': 'units',
            'current_stock': current_stock
        })
    
    conn.close()
    return render_template('index.html', items=items_with_stock)

# Movements management
@app.route('/movements')
def movements():
    conn = get_db_connection()
    movements = conn.execute('''
        SELECT m.*, 
               COALESCE(i.name, mi.name) as name, 
               COALESCE(i.unit, 'units') as unit,
               SUM(m2.quantity_change) as running_stock
        FROM movements m 
        LEFT JOIN items i ON m.item_id = i.id 
        LEFT JOIN menu_items mi ON m.menu_item_id = mi.id
        LEFT JOIN movements m2 ON (m2.item_id = m.item_id OR m2.menu_item_id = m.menu_item_id) AND m2.date <= m.date
        GROUP BY m.id, m.item_id, m.menu_item_id, m.quantity_change, m.movement_type, m.notes, m.date
        ORDER BY m.date DESC
    ''').fetchall()
    conn.close()
    return render_template('movements.html', movements=movements)

@app.route('/movements/add', methods=('GET', 'POST'))
def add_movement():
    if request.method == 'POST':
        menu_item_id = request.form['menu_item_id']
        quantity_change = int(request.form['quantity_change'])
        notes = request.form.get('notes', '')
        
        # Determine movement type based on quantity
        if quantity_change > 0:
            movement_type = 'in'
        elif quantity_change < 0:
            movement_type = 'out'
        else:
            movement_type = 'adjust'
        
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO movements (menu_item_id, quantity_change, movement_type, notes, date) 
            VALUES (?, ?, ?, ?, ?)
        ''', (menu_item_id, quantity_change, movement_type, notes, datetime.now()))
        conn.commit()
        conn.close()
        return redirect(url_for('movements'))
    
    # Get stockable menu items for dropdown
    conn = get_db_connection()
    stockable_items = conn.execute('SELECT * FROM menu_items WHERE stockable = 1 ORDER BY name').fetchall()
    conn.close()
    return render_template('add_movement.html', items=stockable_items)

# Table management routes
@app.route('/tables')
def tables():
    conn = get_db_connection()
    tables = conn.execute('''
        SELECT rt.*, 
               COUNT(o.id) as active_orders,
               GROUP_CONCAT(o.customer_name) as customers
        FROM restaurant_tables rt
        LEFT JOIN orders o ON rt.id = o.table_id AND o.status = 'active'
        GROUP BY rt.id
        ORDER BY rt.table_number
    ''').fetchall()
    conn.close()
    return render_template('tables.html', tables=tables)

@app.route('/tables/add', methods=('GET', 'POST'))
def add_table():
    if request.method == 'POST':
        table_number = int(request.form['table_number'])
        capacity = int(request.form['capacity'])
        
        conn = get_db_connection()
        conn.execute('INSERT INTO restaurant_tables (table_number, capacity) VALUES (?, ?)', 
                    (table_number, capacity))
        conn.commit()
        conn.close()
        return redirect(url_for('tables'))
    return render_template('add_table.html')

# Menu management routes
@app.route('/menu')
def menu():
    conn = get_db_connection()
    menu_items = conn.execute('SELECT * FROM menu_items ORDER BY category, name').fetchall()
    conn.close()
    return render_template('menu.html', menu_items=menu_items)

@app.route('/menu/add', methods=('GET', 'POST'))
def add_menu_item():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        category = request.form['category']
        price = float(request.form['price'])
        stockable = 1 if request.form.get('stockable') == 'on' else 0
        
        conn = get_db_connection()
        cursor = conn.execute('INSERT INTO menu_items (name, description, category, price, stockable) VALUES (?, ?, ?, ?, ?)', 
                    (name, description, category, price, stockable))
        menu_item_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Log creation
        new_values = f"name: {name}, description: {description}, category: {category}, price: ${price}, stockable: {stockable}"
        log_menu_audit(menu_item_id, 'CREATE', None, new_values)
        
        return redirect(url_for('menu'))
    return render_template('add_menu_item.html')

@app.route('/menu/edit/<int:id>', methods=('GET', 'POST'))
def edit_menu_item(id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        # Get old values for audit
        old_item = conn.execute('SELECT * FROM menu_items WHERE id = ?', (id,)).fetchone()
        old_values = f"name: {old_item['name']}, description: {old_item['description']}, category: {old_item['category']}, price: ${old_item['price']}, stockable: {old_item['stockable']}"
        
        # Update with new values
        name = request.form['name']
        description = request.form.get('description', '')
        category = request.form['category']
        price = float(request.form['price'])
        stockable = 1 if request.form.get('stockable') == 'on' else 0
        
        conn.execute('UPDATE menu_items SET name = ?, description = ?, category = ?, price = ?, stockable = ? WHERE id = ?',
                    (name, description, category, price, stockable, id))
        conn.commit()
        conn.close()
        
        # Log update
        new_values = f"name: {name}, description: {description}, category: {category}, price: ${price}, stockable: {stockable}"
        log_menu_audit(id, 'UPDATE', old_values, new_values)
        
        return redirect(url_for('menu'))
    
    # GET request - show edit form
    item = conn.execute('SELECT * FROM menu_items WHERE id = ?', (id,)).fetchone()
    conn.close()
    return render_template('edit_menu_item.html', item=item)

@app.route('/menu/delete/<int:id>', methods=('POST',))
def delete_menu_item(id):
    conn = get_db_connection()
    
    # Get item details for audit before deletion
    item = conn.execute('SELECT * FROM menu_items WHERE id = ?', (id,)).fetchone()
    old_values = f"name: {item['name']}, description: {item['description']}, category: {item['category']}, price: ${item['price']}, stockable: {item['stockable']}"
    
    conn.execute('DELETE FROM menu_items WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    # Log deletion
    log_menu_audit(id, 'DELETE', old_values, None)
    
    return redirect(url_for('menu'))

@app.route('/menu/audit')
def menu_audit():
    conn = get_db_connection()
    audit_log = conn.execute('''
        SELECT ma.*, mi.name as current_name
        FROM menu_audit ma
        LEFT JOIN menu_items mi ON ma.menu_item_id = mi.id
        ORDER BY ma.timestamp DESC
    ''').fetchall()
    conn.close()
    return render_template('menu_audit.html', audit_log=audit_log)

# Order management routes
@app.route('/orders')
def orders():
    conn = get_db_connection()
    
    # Get all orders in CSV-like format
    orders = conn.execute('''
        SELECT o.id, rt.table_number, o.created_at, o.closed_at, 
               o.customer_name, o.comments, o.status,
               COUNT(oi.id) as item_count,
               SUM(oi.quantity * oi.unit_price) as calculated_total,
               GROUP_CONCAT(mi.name || ': ' || oi.quantity, ', ') as items_list
        FROM orders o
        JOIN restaurant_tables rt ON o.table_id = rt.id
        LEFT JOIN order_items oi ON o.id = oi.order_id
        LEFT JOIN menu_items mi ON oi.menu_item_id = mi.id
        GROUP BY o.id
        ORDER BY o.created_at DESC
    ''').fetchall()
    
    # Get payment information for each order
    orders_with_payments = []
    for order in orders:
        payments = conn.execute('''
            SELECT payment_method, amount 
            FROM order_payments 
            WHERE order_id = ?
            ORDER BY created_at
        ''', (order['id'],)).fetchall()
        
        # Convert order to dict and add payments
        order_dict = dict(order)
        order_dict['payments'] = payments
        orders_with_payments.append(order_dict)
    
    conn.close()
    return render_template('orders.html', orders=orders_with_payments)

@app.route('/orders/new/<int:table_id>', methods=('GET', 'POST'))
def new_order(table_id):
    if request.method == 'POST':
        customer_name = request.form.get('customer_name', '')
        
        conn = get_db_connection()
        cursor = conn.execute('''
            INSERT INTO orders (table_id, customer_name, created_at) 
            VALUES (?, ?, ?)
        ''', (table_id, customer_name, datetime.now()))
        
        order_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return redirect(url_for('order_detail', order_id=order_id))
    
    # Get table info
    conn = get_db_connection()
    table = conn.execute('SELECT * FROM restaurant_tables WHERE id = ?', (table_id,)).fetchone()
    conn.close()
    return render_template('new_order.html', table=table)

@app.route('/orders/<int:order_id>')
def order_detail(order_id):
    conn = get_db_connection()
    
    # Get order info
    order = conn.execute('''
        SELECT o.*, rt.table_number 
        FROM orders o 
        JOIN restaurant_tables rt ON o.table_id = rt.id 
        WHERE o.id = ?
    ''', (order_id,)).fetchone()
    
    # Get order items
    order_items = conn.execute('''
        SELECT oi.*, mi.name, mi.category 
        FROM order_items oi 
        JOIN menu_items mi ON oi.menu_item_id = mi.id 
        WHERE oi.order_id = ?
    ''', (order_id,)).fetchall()
    
    # Get available menu items for adding
    menu_items = conn.execute('SELECT * FROM menu_items WHERE available = 1 ORDER BY category, name').fetchall()
    
    # Get payment history for this order
    payments = conn.execute('''
        SELECT payment_method, amount, created_at
        FROM order_payments 
        WHERE order_id = ?
        ORDER BY created_at
    ''', (order_id,)).fetchall()
    
    conn.close()
    
    # Calculate total in Python (more reliable than Jinja2 loop)
    total = sum(item['quantity'] * item['unit_price'] for item in order_items)
    
    return render_template('order_detail.html', order=order, order_items=order_items, menu_items=menu_items, total=total, payments=payments)

@app.route('/orders/<int:order_id>/add_item', methods=('POST',))
def add_order_item(order_id):
    menu_item_id = int(request.form['menu_item_id'])
    quantity = int(request.form['quantity'])
    notes = request.form.get('notes', '')
    
    conn = get_db_connection()
    
    # Get menu item details (price and stockable status)
    menu_item = conn.execute('SELECT price, stockable, name FROM menu_items WHERE id = ?', (menu_item_id,)).fetchone()
    
    # Add order item
    conn.execute('''
        INSERT INTO order_items (order_id, menu_item_id, quantity, unit_price, notes) 
        VALUES (?, ?, ?, ?, ?)
    ''', (order_id, menu_item_id, quantity, menu_item['price'], notes))
    
    # Log the action in order item history
    conn.execute('''
        INSERT INTO order_item_history (order_id, menu_item_id, action, quantity, unit_price, notes, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (order_id, menu_item_id, 'added', quantity, menu_item['price'], notes, datetime.now()))
    
    conn.commit()
    conn.close()
    return redirect(url_for('order_detail', order_id=order_id))

@app.route('/orders/<int:order_id>/items/<int:item_id>/edit', methods=('POST',))
def edit_order_item(order_id, item_id):
    quantity = int(request.form['quantity'])
    notes = request.form.get('notes', '')
    
    conn = get_db_connection()
    
    # Get current item details for history
    current_item = conn.execute('SELECT * FROM order_items WHERE id = ?', (item_id,)).fetchone()
    
    # Update the order item
    conn.execute('''
        UPDATE order_items SET quantity = ?, notes = ? WHERE id = ?
    ''', (quantity, notes, item_id))
    
    # Log the action in order item history
    conn.execute('''
        INSERT INTO order_item_history (order_id, menu_item_id, action, quantity, unit_price, notes, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (order_id, current_item['menu_item_id'], 'edited', quantity, current_item['unit_price'], notes, datetime.now()))
    
    conn.commit()
    conn.close()
    return redirect(url_for('order_detail', order_id=order_id))

@app.route('/orders/<int:order_id>/items/<int:item_id>/remove', methods=('POST',))
def remove_order_item(order_id, item_id):
    conn = get_db_connection()
    
    # Get current item details for history before deleting
    current_item = conn.execute('SELECT * FROM order_items WHERE id = ?', (item_id,)).fetchone()
    
    # Log the removal in order item history
    conn.execute('''
        INSERT INTO order_item_history (order_id, menu_item_id, action, quantity, unit_price, notes, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (order_id, current_item['menu_item_id'], 'removed', current_item['quantity'], current_item['unit_price'], current_item['notes'], datetime.now()))
    
    # Remove the order item
    conn.execute('DELETE FROM order_items WHERE id = ?', (item_id,))
    
    conn.commit()
    conn.close()
    return redirect(url_for('order_detail', order_id=order_id))

@app.route('/orders/<int:order_id>/close', methods=('POST',))
def close_order(order_id):
    # Get payment methods and amounts from form
    payment_methods = request.form.getlist('payment_method[]')
    amounts_str = request.form.getlist('amount[]')
    
    # Convert amounts to float and validate
    try:
        amounts = [float(x) for x in amounts_str if x.strip()]
    except ValueError:
        return "Error: Invalid payment amounts", 400
    
    if len(payment_methods) != len(amounts):
        return "Error: Mismatch between payment methods and amounts", 400
    
    conn = get_db_connection()
    
    # Calculate order total
    order_total_result = conn.execute('''
        SELECT SUM(oi.quantity * oi.unit_price) as total
        FROM order_items oi
        WHERE oi.order_id = ?
    ''', (order_id,)).fetchone()
    order_total = order_total_result['total'] or 0
    
    # Validate payment total matches order total
    payment_total = sum(amounts)
    if abs(order_total - payment_total) > 0.01:  # Allow 1 cent rounding difference
        return f"Error: Payment total ${payment_total:.2f} doesn't match order total ${order_total:.2f}", 400
    
    # Get all current order items for stock movements
    order_items = conn.execute('''
        SELECT oi.menu_item_id, oi.quantity, mi.name, mi.stockable
        FROM order_items oi
        JOIN menu_items mi ON oi.menu_item_id = mi.id
        WHERE oi.order_id = ?
    ''', (order_id,)).fetchall()
    
    # Create stock movements for all stockable items when order is closed
    for item in order_items:
        if item['stockable']:
            movement_notes = f"Auto: Order #{order_id} closed - {item['name']} x{item['quantity']}"
            conn.execute('''
                INSERT INTO movements (menu_item_id, quantity_change, movement_type, notes, date) 
                VALUES (?, ?, ?, ?, ?)
            ''', (item['menu_item_id'], -item['quantity'], 'out', movement_notes, datetime.now()))
    
    # Save all payments
    for method, amount in zip(payment_methods, amounts):
        if amount > 0:  # Only save payments with positive amounts
            conn.execute('''
                INSERT INTO order_payments (order_id, payment_method, amount, created_at)
                VALUES (?, ?, ?, ?)
            ''', (order_id, method, amount, datetime.now()))
    
    # Close the order
    conn.execute('UPDATE orders SET status = ?, closed_at = ? WHERE id = ?', 
                ('closed', datetime.now(), order_id))
    
    conn.commit()
    conn.close()
    return redirect(url_for('orders'))

if __name__ == '__main__':
    # Create tables if they don't exist
    conn = get_db_connection()
    
    # Items catalog table
    conn.execute('''CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        unit TEXT NOT NULL
    )''')
    
    # Movements tracking table
    conn.execute('''CREATE TABLE IF NOT EXISTS movements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER,
        menu_item_id INTEGER,
        quantity_change INTEGER NOT NULL,
        movement_type TEXT NOT NULL,
        notes TEXT,
        date DATETIME NOT NULL,
        FOREIGN KEY (item_id) REFERENCES items (id),
        FOREIGN KEY (menu_item_id) REFERENCES menu_items (id)
    )''')
    
    # Restaurant tables
    conn.execute('''CREATE TABLE IF NOT EXISTS restaurant_tables (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_number INTEGER NOT NULL UNIQUE,
        capacity INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'available'
    )''')
    
    # Menu items (food and drinks)
    conn.execute('''CREATE TABLE IF NOT EXISTS menu_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        category TEXT NOT NULL,
        price DECIMAL(10,2) NOT NULL,
        available BOOLEAN DEFAULT 1,
        stockable BOOLEAN DEFAULT 0,
        unit TEXT
    )''')
    
    # Customer orders
    conn.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_id INTEGER NOT NULL,
        customer_name TEXT,
        status TEXT NOT NULL DEFAULT 'active',
        created_at DATETIME NOT NULL,
        closed_at DATETIME,
        comments TEXT,
        total_amount DECIMAL(10,2) DEFAULT 0,
        FOREIGN KEY (table_id) REFERENCES restaurant_tables (id)
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
    app.run(debug=True, port=5000)
