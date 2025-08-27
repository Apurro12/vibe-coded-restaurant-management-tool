from flask import render_template, request
from . import caja_bp
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_db_connection

caja_query = """
with table_payments as (
    select 
        date("created_at") "date", 
        "payment_method", 
        sum("amount") "amount", 
        null as description,
        'Orden de mesa' "movement_type"
                                
    from order_payments 
    group by 1,2
),

manual_movements as (
    select 
        date("date") "date", 
        "payment_method", 
        "amount", 
        "description",
        "movement_type"
    from manual_money_movements
),

both_tables as (
    select *
    from table_payments
    union all 
    select *
    from manual_movements
)        

select *
from both_tables 
order by "date" DESC, 2 
"""

# Caja management routes
@caja_bp.route('/')
def caja():
    conn = get_db_connection()
    caja_movements = conn.execute(caja_query).fetchall()
    conn.commit()
    conn.close()
    return render_template('caja/index.html', caja_movements=caja_movements)


@caja_bp.route('/modify_money', methods=('POST',) )
def modify_money():
    amount = request.form['amount']
    description = request.form['description']
    payment_method = request.form['payment_method']

    movement_type = 'Ingreso Manual' if float(amount) > 0 else 'Egreso Manual'

    conn = get_db_connection()
    caja_movements = conn.execute('''
        insert into manual_money_movements ("date","payment_method","description","amount","movement_type")
        values (?, ?, ?, ?, ?)
    ''', (datetime.now(), payment_method, description, amount, movement_type))

    caja_movements = conn.execute(caja_query).fetchall()

    conn.commit()
    conn.close()
    return render_template('caja/index.html', caja_movements=caja_movements)