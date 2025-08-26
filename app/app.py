from flask import Flask, render_template, Blueprint
from utils import get_db_connection, get_current_stock_for_menu_item, init_database

# Import blueprints
from menu import menu_bp
from orders import orders_bp
from tables import tables_bp
from movements import movements_bp

app = Flask(__name__)

# Register blueprints
app.register_blueprint(menu_bp)
app.register_blueprint(orders_bp)
app.register_blueprint(tables_bp)
app.register_blueprint(movements_bp)

# Main blueprint for the dashboard
main_bp = Blueprint('main', __name__)

# Main page: shows stockable menu items and current stock levels
@main_bp.route('/')
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

# Register main blueprint
app.register_blueprint(main_bp)

if __name__ == '__main__':
    # Initialize database
    init_database()
    app.run(debug=True, port=5000)
