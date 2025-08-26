from flask import render_template, request, redirect, url_for
from datetime import datetime
from . import movements_bp
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_db_connection

# Movements management
@movements_bp.route('/')
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
    return render_template('movements/index.html', movements=movements)

@movements_bp.route('/add', methods=('GET', 'POST'))
def add_movement():
    if request.method == 'POST':
        menu_item_id = request.form['menu_item_id']
        quantity_change = int(request.form['quantity_change'])
        notes = request.form.get('notes', '')
        
        # Determine movement type based on quantity
        if quantity_change > 0:
            movement_type = 'Entrada'
        elif quantity_change < 0:
            movement_type = 'Salida'
        else:
            movement_type = 'Comentario'
        
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO movements (menu_item_id, quantity_change, movement_type, notes, date) 
            VALUES (?, ?, ?, ?, ?)
        ''', (menu_item_id, quantity_change, movement_type, notes, datetime.now()))
        conn.commit()
        conn.close()
        return redirect(url_for('movements.movements'))
    
    # Get stockable menu items for dropdown
    conn = get_db_connection()
    stockable_items = conn.execute('SELECT * FROM menu_items WHERE stockable = 1 ORDER BY name').fetchall()
    conn.close()
    return render_template('movements/add.html', items=stockable_items)