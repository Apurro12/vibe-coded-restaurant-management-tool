from flask import render_template, request, redirect, url_for
from . import menu_bp
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_db_connection, log_menu_audit

# Menu management routes
@menu_bp.route('/')
def menu():
    conn = get_db_connection()
    # Hard delete, all items in this table exists
    menu_items = conn.execute('SELECT * FROM menu_items ORDER BY category, name').fetchall()
    conn.close()
    return render_template('menu/index.html', menu_items=menu_items)

@menu_bp.route('/add', methods=('POST',))
def add_menu_item():
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
    
    return redirect(url_for('menu.menu'))

@menu_bp.route('/edit/<int:id>', methods=('GET', 'POST'))
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
        
        return redirect(url_for('menu.menu'))
    
    # GET request - show edit form
    item = conn.execute('SELECT * FROM menu_items WHERE id = ?', (id,)).fetchone()
    conn.close()
    return render_template('menu/edit.html', item=item)

@menu_bp.route('/delete/<int:id>', methods=('POST',))
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
    
    return redirect(url_for('menu.menu'))

@menu_bp.route('/audit')
def menu_audit():
    conn = get_db_connection()
    audit_log = conn.execute('''
        SELECT ma.*, mi.name as current_name
        FROM menu_audit ma
        LEFT JOIN menu_items mi ON ma.menu_item_id = mi.id
        ORDER BY ma.timestamp DESC
    ''').fetchall()
    conn.close()
    return render_template('menu/audit.html', audit_log=audit_log)