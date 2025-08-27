# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive Flask-based restaurant management system with inventory tracking, order management, and table service capabilities. The system features a Spanish frontend with English backend code, designed for restaurant operations including menu management, stock control, order processing, payment handling, and complete audit trails.

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
The application runs on `http://127.0.0.1:5000` (default Flask port).

### Testing
```bash
# Quick endpoint testing (with server running on port 5001)
python3 quick_test.py

# Comprehensive E2E testing (stop server first to avoid database locks)
python3 tests/integration/test_app.py

# Automated test runner
./run_tests.sh
```

### Database Operations
The SQLite database (`inventory.db`) is automatically created with all necessary tables when the application starts. For testing, the system supports custom database paths via environment variables. No manual database setup required.

## Code Architecture

### Core System Design
This is a **modularized Flask application** using **Blueprint architecture** with the main app coordinating separate modules. The system evolved from simple inventory management to a full restaurant management platform with these key architectural decisions:

**Modular Blueprint Structure**:
- `app/app.py` - Main application with dashboard and blueprint registration
- `app/menu/routes.py` - Menu management routes
- `app/orders/routes.py` - Order processing and management routes  
- `app/tables/routes.py` - Restaurant table management routes
- `app/movements/routes.py` - Stock movement routes
- `app/utils.py` - Database utilities and helper functions

**Stock Management Philosophy**: Stock changes only occur when orders are **closed**, not when items are added to orders. This prevents inventory conflicts during order editing.

### Database Schema (9 Tables)

**Core Menu & Inventory**:
- `menu_items` - Menu items with prices, descriptions, categories, and stockable flag
- `movements` - All stock changes with partial_stock tracking for running totals
- `menu_audit` - Complete audit trail for menu changes

**Restaurant Operations**:
- `restaurant_tables` - Table management with capacity, status, customer info, and open order tracking
- `orders` - Order tracking with status (active/closed), customer info, timestamps, total amounts
- `order_items` - Items within orders with quantities, prices, notes
- `order_item_history` - Complete audit trail of all order modifications (add/edit/remove)
- `order_payments` - Payment tracking with support for split payments and multiple payment methods

### Key Business Logic Functions

**Stock Calculations**:
- `get_current_stock_for_menu_item(menu_item_id)` - Calculates running stock totals from movements
- `get_last_stock(menu_item_id)` - Gets the most recent partial_stock value for running totals
- `log_menu_audit(menu_item_id, action, old_values, new_values)` - Audit trail logging

**Order Processing**:
- Stock movements are created in `close_order()` function, not in `add_order_item()`
- Order editing routes: `/orders/<id>/items/<item_id>/edit` and `/orders/<id>/items/<item_id>/remove`
- Payment processing with split payment support in `close_order()`
- All order changes logged to `order_item_history` table

### Route Structure (Blueprint-based)
```
/ - Dashboard with stockable items and stock levels
/menu - Menu management with CRUD operations and audit trail
/menu/add - Add new menu items (POST)
/menu/edit/<id> - Edit menu items (GET/POST)
/menu/delete/<id> - Delete menu items (POST)  
/menu/audit - View menu change history
/movements - Stock movement history with running totals
/movements/add - Add stock movements (GET/POST)
/tables - Restaurant table management
/tables/add - Add new tables (GET/POST)
/orders - Order listing with payment details and CSV-like format
/orders/new/<table_id> - Create new order for specific table (GET/POST)
/orders/<order_id> - Order detail with editing capabilities (active orders only)
/orders/<order_id>/add_item - Add items to orders (POST)
/orders/<order_id>/items/<item_id>/edit - Edit order items (POST)
/orders/<order_id>/items/<item_id>/remove - Remove order items (POST)
/orders/<order_id>/close - Close order, process payments, and trigger stock movements (POST)
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

### Payment Processing
The system supports multiple payment methods with split payment capabilities:
- Payment validation ensures total payments match order totals (within 1 cent tolerance)
- Multiple payment methods per order (cash, card, etc.)
- Payment history stored in `order_payments` table
- Payments are recorded when orders are closed

### Running Stock Calculations
The system uses two approaches for stock calculations:
1. **SUM-based calculation** (`get_current_stock_for_menu_item`) - Sums all quantity changes
2. **Partial stock tracking** (`get_last_stock`) - Uses `partial_stock` field for running totals

### Audit Trail Implementation
Multiple audit systems ensure complete traceability:
1. `menu_audit` - Tracks all menu item changes (create/update/delete) with old/new values
2. `order_item_history` - Tracks all order modifications with action types: 'added', 'old_edited', 'new_edited', 'removed'

### Order Item History Actions
- `'added'` - Item added to order
- `'old_edited'` - Original state before edit
- `'new_edited'` - New state after edit  
- `'removed'` - Item removed from order

## Testing Architecture

The system includes comprehensive testing with three approaches:
1. **Quick endpoint testing** (`quick_test.py`) - Safe to run with server active on port 5001
2. **Full E2E testing** (`tests/integration/test_app.py`) - Requires server shutdown to avoid DB locks, uses custom test database
3. **Automated test runner** (`run_tests.sh`) - Handles dependencies and server checks

The E2E testing includes:
- Database isolation using environment variables
- Complete restaurant workflow validation: create menu items (stockable/non-stockable) → add stock → create table → place order → edit order → close order → verify stock changes
- Payment processing validation
- Order history verification
- Stock movement verification for stockable vs non-stockable items

## Translation Implementation

Frontend uses Spanish translations while maintaining English backend code. Template files contain Spanish text for:
- Navigation elements ("Menú", "Movimientos de Stock", "Mesas", "Órdenes")
- Form labels and buttons
- Table headers and status messages
- User-facing text and confirmations

Backend route names, function names, and database schema remain in English for developer clarity.