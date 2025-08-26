from flask import render_template, request, redirect, url_for
from . import tables_bp
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_db_connection

# Table management routes
@tables_bp.route('/')
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
    return render_template('tables/index.html', tables=tables)

@tables_bp.route('/add', methods=('GET', 'POST'))
def add_table():
    if request.method == 'POST':
        table_number = int(request.form['table_number'])
        capacity = int(request.form['capacity'])
        
        conn = get_db_connection()
        conn.execute('INSERT INTO restaurant_tables (table_number, capacity) VALUES (?, ?)', 
                    (table_number, capacity))
        conn.commit()
        conn.close()
        return redirect(url_for('tables.tables'))
    return render_template('tables/add.html')