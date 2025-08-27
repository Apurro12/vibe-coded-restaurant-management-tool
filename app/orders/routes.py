from flask import render_template, request, redirect, url_for
from datetime import datetime

from . import orders_bp
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_db_connection, get_last_stock

# Order management routes
@orders_bp.route('/')
def orders():
    conn = get_db_connection()
    
    # Get all orders in CSV-like format
    orders = conn.execute('''
        SELECT  orders.id, 
                orders.table_id, 
                orders.customer_name, 
                orders.status,
                orders.created_at, 
                orders.closed_at, 
                SUM(order_items.quantity * order_items.unit_price) as calculated_total,
                GROUP_CONCAT(order_items.menu_item_name || ': ' || order_items.quantity, ', ') as items_list
                          
        FROM orders     
        LEFT JOIN order_items ON orders.id = order_items.order_id
        GROUP BY orders.id
        ORDER BY orders.id DESC
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
    return render_template('orders/index.html', orders=orders_with_payments)

@orders_bp.route('/new/<int:table_id>', methods=('GET', 'POST'))
def new_order(table_id):
    if request.method == 'POST':
        customer_name = request.form.get('customer_name', '')
        
        conn = get_db_connection()
        cursor = conn.execute('''
            INSERT INTO orders (table_id, customer_name, created_at, status) 
            VALUES (?, ?, ?, ?)
        ''', (table_id, customer_name, datetime.now(), 'active'))

        conn.commit()

        order_id = conn.execute('''
                    select "id"
                    from orders
                    where table_id = ? and status = ?
                ''', (table_id, 'active')).fetchone()["id"]

        conn.execute('''
            update restaurant_tables
            set "status" = 'in use'
            where table_number = ?
        ''', (table_id,))

        conn.execute('''
            update restaurant_tables
            set "customer_name" = ?
            where table_number = ?
        ''', (customer_name, table_id))

        conn.execute('''
            update restaurant_tables
            set "open_order_number" = ?
            where table_number = ?
        ''', (order_id, table_id))

        order_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return redirect(url_for('orders.order_detail', order_id=order_id))
    
    # Get table info
    conn = get_db_connection()
    table = conn.execute('SELECT * FROM restaurant_tables WHERE table_number = ?', (table_id,)).fetchone()
    conn.close()
    return render_template('orders/new.html', table=table)

@orders_bp.route('/<int:order_id>')
def order_detail(order_id):
    conn = get_db_connection()
    
    # Get order info
    order = conn.execute('''
        SELECT o.*, rt.table_number 
        FROM orders o 
        JOIN restaurant_tables rt ON o.table_id = rt.table_number 
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
    menu_items = conn.execute('SELECT * FROM menu_items ORDER BY category, name').fetchall()
    
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
    
    return render_template('orders/detail.html', order=order, order_items=order_items, menu_items=menu_items, total=total, payments=payments)

@orders_bp.route('/<int:order_id>/add_item', methods=('POST',))
def add_order_item(order_id):
    menu_item_id = int(request.form['menu_item_id'])
    quantity = int(request.form['quantity'])
    notes = request.form.get('notes', '')
    
    conn = get_db_connection()
    
    # Get menu item details (price and stockable status)
    menu_item = conn.execute('SELECT price, name FROM menu_items WHERE id = ?', (menu_item_id,)).fetchone()
    
    # Add order item
    cursor = conn.execute('''
        INSERT INTO order_items (order_id, menu_item_id, quantity, unit_price, notes, menu_item_name) 
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (order_id, menu_item_id, quantity, menu_item['price'], notes, menu_item['name']))
    
    # Get the auto-incremental ID of the just inserted order item
    order_item_id = cursor.lastrowid
    
    # Log the action in order item history
    conn.execute('''
        INSERT INTO order_item_history (order_id, menu_item_id, action, quantity, unit_price, notes, timestamp, menu_item_name)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (order_id, menu_item_id, 'added', quantity, menu_item['price'], notes, datetime.now(), menu_item['name']))
    
    conn.commit()
    conn.close()
    return redirect(url_for('orders.order_detail', order_id=order_id))

@orders_bp.route('/<int:order_id>/items/<int:item_id>/edit', methods=('POST',))
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
    

    # Log the edit action in order item history
    conn.execute('''
        INSERT INTO order_item_history (order_id, menu_item_id, action, quantity, unit_price, notes, timestamp, menu_item_name)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (order_id, current_item['menu_item_id'], 'old_edited', current_item['quantity'], current_item['unit_price'], current_item['notes'], datetime.now(), current_item["menu_item_name"]))
    

    # Log the edit action in order item history
    conn.execute('''
        INSERT INTO order_item_history (order_id, menu_item_id, action, quantity, unit_price, notes, timestamp, menu_item_name)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (order_id, current_item['menu_item_id'], 'new_edited', quantity, current_item['unit_price'], notes, datetime.now(), current_item["menu_item_name"]))
    
    conn.commit()
    conn.close()
    return redirect(url_for('orders.order_detail', order_id=order_id))

@orders_bp.route('/<int:order_id>/items/<int:item_id>/remove', methods=('POST',))
def remove_order_item(order_id, item_id):
    conn = get_db_connection()
    
    # Get current item details for history before deleting
    current_item = conn.execute('SELECT * FROM order_items WHERE id = ?', (item_id,)).fetchone()

    # Log the edit action in order item history
    conn.execute('''
        INSERT INTO order_item_history (order_id, menu_item_id, action, quantity, unit_price, notes, timestamp, menu_item_name)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (order_id, current_item['menu_item_id'], 'removed', current_item["quantity"], current_item['unit_price'], current_item["notes"], datetime.now(), current_item["menu_item_name"]))
    

    # Remove the order item
    conn.execute('DELETE FROM order_items WHERE id = ?', (item_id,))
    
    conn.commit()
    conn.close()
    return redirect(url_for('orders.order_detail', order_id=order_id))

@orders_bp.route('/<int:order_id>/close', methods=('POST',))
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
        SELECT oi.menu_item_id, oi.quantity, menu_item_name, mi.stockable
        FROM order_items oi
        JOIN menu_items mi ON oi.menu_item_id = mi.id
        WHERE oi.order_id = ?
    ''', (order_id,)).fetchall()
    
    # Create stock movements for all stockable items when order is closed
    for item in order_items:
        if item['stockable']:
            last_movement = get_last_stock(item["menu_item_id"])
            new_stock = last_movement - item['quantity']
            movement_notes = f"Auto: Order #{order_id} closed - {item['menu_item_name']} x{item['quantity']}"
            conn.execute('''
                INSERT INTO movements (menu_item_id, quantity_change, movement_type, notes, date, menu_item_name, partial_stock) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (item['menu_item_id'], -item['quantity'], 'out', movement_notes, datetime.now(), item['menu_item_name'], new_stock))
    
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
    
    table_number = conn.execute('''
        SELECT table_number
        FROM restaurant_tables
        WHERE open_order_number = ?
        and status = ?
    ''', (order_id, 'in use')).fetchone()["table_number"]

    conn.execute(
        'UPDATE restaurant_tables SET open_order_number = null WHERE table_number = ? and status = ?',
        (table_number, 'in use')
    )

    conn.execute(
        'UPDATE restaurant_tables SET status = ? WHERE table_number = ? and status = ?',
        ('available', table_number, 'in use')
    )
    
    conn.commit()
    conn.close()
    return redirect(url_for('orders.orders'))