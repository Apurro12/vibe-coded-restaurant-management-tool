from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)
DATABASE = 'inventory.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def get_current_stock(item_id):
    """Calculate current stock for an item based on movements"""
    conn = get_db_connection()
    result = conn.execute(
        'SELECT SUM(quantity_change) as total FROM movements WHERE item_id = ?', 
        (item_id,)
    ).fetchone()
    conn.close()
    return result['total'] if result['total'] else 0

# Main page: shows items catalog and current stock levels
@app.route('/')
def index():
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM items ORDER BY name').fetchall()
    
    # Get current stock for each item
    items_with_stock = []
    for item in items:
        current_stock = get_current_stock(item['id'])
        items_with_stock.append({
            'id': item['id'],
            'name': item['name'],
            'unit': item['unit'],
            'current_stock': current_stock
        })
    
    conn.close()
    return render_template('index.html', items=items_with_stock)

# Items catalog management
@app.route('/items')
def items_catalog():
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM items ORDER BY name').fetchall()
    conn.close()
    return render_template('items_catalog.html', items=items)

@app.route('/items/add', methods=('GET', 'POST'))
def add_item():
    if request.method == 'POST':
        name = request.form['name']
        unit = request.form['unit']
        conn = get_db_connection()
        conn.execute('INSERT INTO items (name, unit) VALUES (?, ?)', (name, unit))
        conn.commit()
        conn.close()
        return redirect(url_for('items_catalog'))
    return render_template('add_item.html')

@app.route('/items/delete/<int:id>', methods=('POST',))
def delete_item(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM items WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('items_catalog'))

# Movements management
@app.route('/movements')
def movements():
    conn = get_db_connection()
    movements = conn.execute('''
        SELECT m.*, i.name, i.unit,
               SUM(m2.quantity_change) as running_stock
        FROM movements m 
        JOIN items i ON m.item_id = i.id 
        LEFT JOIN movements m2 ON m2.item_id = m.item_id AND m2.date <= m.date
        GROUP BY m.id, m.item_id, m.quantity_change, m.movement_type, m.notes, m.date, i.name, i.unit
        ORDER BY m.date DESC
    ''').fetchall()
    conn.close()
    return render_template('movements.html', movements=movements)

@app.route('/movements/add', methods=('GET', 'POST'))
def add_movement():
    if request.method == 'POST':
        item_id = request.form['item_id']
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
            INSERT INTO movements (item_id, quantity_change, movement_type, notes, date) 
            VALUES (?, ?, ?, ?, ?)
        ''', (item_id, quantity_change, movement_type, notes, datetime.now()))
        conn.commit()
        conn.close()
        return redirect(url_for('movements'))
    
    # Get items for dropdown
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM items ORDER BY name').fetchall()
    conn.close()
    return render_template('add_movement.html', items=items)

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
        item_id INTEGER NOT NULL,
        quantity_change INTEGER NOT NULL,
        movement_type TEXT NOT NULL,
        notes TEXT,
        date DATETIME NOT NULL,
        FOREIGN KEY (item_id) REFERENCES items (id)
    )''')
    
    conn.commit()
    conn.close()
    app.run(debug=True)
