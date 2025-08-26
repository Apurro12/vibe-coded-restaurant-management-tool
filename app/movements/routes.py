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
        SELECT  m.*,
                'units' as unit
        FROM movements m 
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
        item_name = request.form.get('item_name', '')
        
        # Determine movement type based on quantity
        if quantity_change > 0:
            movement_type = 'Entrada'
        elif quantity_change < 0:
            movement_type = 'Salida'
        else:
            movement_type = 'Comentario'
        
        conn = get_db_connection()

        last_movement = conn.execute('''
            select "partial_stock"
            from movements
            where "id" in (
                SELECT max("id") "id"
                FROM movements
                where menu_item_id = ?
            )''', (menu_item_id,)).fetchone()
        
        # If is the first movement return zero
        # Here I need to be sure that is not None or something strange
        if last_movement is None:
            last_movement = 0
        else:
            last_movement = last_movement["partial_stock"]
        last_movement += quantity_change

        conn.execute('''
            INSERT INTO movements (menu_item_id, menu_item_name, quantity_change, movement_type, notes, date, partial_stock) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (menu_item_id, item_name, quantity_change, movement_type, notes, datetime.now(), last_movement))
        conn.commit()
        conn.close()
        return redirect(url_for('movements.movements'))
    
    # Get stockable menu items for dropdown
    conn = get_db_connection()
    stockable_items = conn.execute('SELECT * FROM menu_items WHERE stockable = 1 ORDER BY name').fetchall()
    conn.close()
    return render_template('movements/add.html', items=stockable_items)