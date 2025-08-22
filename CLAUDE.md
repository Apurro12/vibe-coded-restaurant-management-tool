# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive Flask-based restaurant management system with inventory tracking, order management, and table service capabilities. The system features a Spanish frontend with English backend code, designed for restaurant operations including menu management, stock control, order processing, and complete audit trails.

## Commands

### Installation and Setup
```bash
# Install dependencies using uv (preferred method)
uv pip install -r requirements.txt

# Alternative with standard pip
pip install flask requests
```

### Running the Application
```bash
cd app
python app.py
```
The application runs on `http://127.0.0.1:5001` (port changed from default 5000 to avoid conflicts).

### Testing
```bash
# Quick endpoint testing (with server running)
python3 quick_test.py

# Comprehensive E2E testing (stop server first to avoid database locks)
python3 test_app.py

# Automated test runner
./run_tests.sh
```

### Database Operations
The SQLite database (`inventory.db`) is automatically created with all necessary tables when the application starts. No manual database setup required.

## Code Architecture

### Core System Design
This is a **monolithic Flask application** with all business logic in `app/app.py`. The system evolved from simple inventory management to a full restaurant management platform with these key architectural decisions:

**Stock Management Philosophy**: Stock changes only occur when orders are **closed**, not when items are added to orders. This prevents inventory conflicts during order editing.

**Dual Inventory System**: 
- Legacy `items` table (maintained for backward compatibility)
- Modern `menu_items` with `stockable` boolean flag for inventory control
- Both systems supported in `movements` table via `item_id` and `menu_item_id` foreign keys

### Database Schema (8 Tables)

**Core Menu & Inventory**:
- `menu_items` - Menu items with prices, descriptions, categories, and stockable flag
- `movements` - All stock changes with running totals, supports both legacy items and menu items
- `menu_audit` - Complete audit trail for menu changes

**Restaurant Operations**:
- `restaurant_tables` - Table management with capacity
- `orders` - Order tracking with status (active/closed), customer info
- `order_items` - Items within orders with quantities, prices, notes
- `order_item_history` - Complete audit trail of all order modifications (add/edit/remove)

**Legacy**:
- `items` - Original inventory system (kept for backward compatibility)

### Key Business Logic Functions

**Stock Calculations**:
- `get_current_stock_for_menu_item(menu_item_id)` - Calculates running stock totals from movements
- `log_menu_audit(menu_item_id, action, old_values, new_values)` - Audit trail logging

**Order Processing**:
- Stock movements are created in `close_order()` function, not in `add_order_item()`
- Order editing routes: `/orders/<id>/items/<item_id>/edit` and `/orders/<id>/items/<item_id>/remove`
- All order changes logged to `order_item_history` table

### Route Structure
```
/ - Dashboard with stockable items and stock levels
/menu - Menu management with CRUD operations
/movements - Stock movement history with running totals
/tables - Restaurant table management
/orders - Order listing and management
/orders/new/<table_id> - Create new order for specific table
/orders/<order_id> - Order detail with editing capabilities (active orders only)
/orders/<order_id>/close - Close order and trigger stock movements
```

### Frontend Architecture
- **Language**: Spanish frontend, English backend
- **Framework**: Jinja2 templates with Milligram CSS
- **Responsive Design**: Max-width containers, mobile-friendly
- **Interactive Features**: 
  - Inline quantity editing in order details
  - Real-time form submissions for order modifications
  - Confirmation dialogs for destructive actions

### Database Connection Pattern
```python
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Enable dict-like access
    return conn
```
All database operations use this helper with proper connection closing. **Important**: Database can become locked if Flask server and test scripts run simultaneously.

## Critical Development Patterns

### Stock Movement Timing
**Never create stock movements when adding items to orders**. Stock changes only occur in `close_order()` function to prevent inventory conflicts during order editing.

### Order State Management
- **Active orders**: Allow editing of quantities, notes, adding/removing items
- **Closed orders**: Read-only, display historical data only
- All changes tracked in `order_item_history` with action types: 'added', 'edited', 'removed'

### Stockable vs Non-Stockable Items
Menu items have a `stockable` boolean flag. Only stockable items:
- Generate stock movements when orders are closed
- Appear on the dashboard inventory display
- Affect running stock calculations

### Running Stock Calculations
The system uses SQL window functions for running totals in movement history:
```sql
SUM(m2.quantity_change) as running_stock
FROM movements m2 ON m2.menu_item_id = m.menu_item_id AND m2.date <= m.date
```

### Audit Trail Implementation
Two separate audit systems:
1. `menu_audit` - Tracks all menu item changes (create/update/delete)
2. `order_item_history` - Tracks all order modifications with timestamps

## Testing Architecture

The system includes comprehensive testing with three approaches:
1. **Quick endpoint testing** (`quick_test.py`) - Safe to run with server active
2. **Full E2E testing** (`test_app.py`) - Requires server shutdown to avoid DB locks
3. **Manual testing guide** (`TESTING.md`) - Detailed step-by-step validation procedures

Testing follows the complete restaurant workflow: create menu items (stockable/non-stockable) → add stock → create table → place order → edit order → close order → verify stock changes.

## Translation Implementation

Frontend uses Spanish translations while maintaining English backend code. Template files contain Spanish text for:
- Navigation elements ("Menú", "Movimientos de Stock", "Mesas", "Órdenes")
- Form labels and buttons
- Table headers and status messages
- User-facing text and confirmations

Backend route names, function names, and database schema remain in English for developer clarity.