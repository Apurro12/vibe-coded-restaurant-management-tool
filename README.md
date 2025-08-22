# Restaurant Management System

A Flask-based restaurant inventory and order management system with Spanish frontend.

## Features

- **Menu Management**: Add/edit menu items with stockable inventory tracking
- **Stock Movements**: Track inventory changes with running totals
- **Table Management**: Restaurant table capacity and status tracking
- **Order System**: Complete order workflow with item editing capability
- **Order History**: Full audit trail of all order modifications
- **Spanish Interface**: Frontend in Spanish, backend in English

## Installation

1. Install dependencies using uv:
```bash
uv pip install -r requirements.txt
```

2. Run the application:
```bash
cd app
python app.py
```

The application will be available at `http://127.0.0.1:5001`

## Key Features

### Stock Management
- Stock updates only when orders are **closed** (not when items are added)
- Only **stockable menu items** affect inventory
- Real-time stock level display on dashboard

### Order Editing
- Edit quantities and notes for **active orders**
- Remove items from orders before closing
- Complete change history tracking
- **Closed orders** become read-only

### Inventory Integration
- Menu items can be marked as "stockable"
- Automatic stock movements when orders are completed
- Full movement history with running totals

## Testing

See [TESTING.md](TESTING.md) for comprehensive testing procedures.

Quick test:
```bash
python3 quick_test.py
```

## Database

Uses SQLite database (`inventory.db`) with the following main tables:
- `menu_items` - Menu items with prices and stockable flag
- `movements` - Stock movements with running calculations
- `restaurant_tables` - Table management
- `orders` & `order_items` - Order system
- `order_item_history` - Complete audit trail

## Development

The system is built with:
- **Backend**: Flask (Python)
- **Frontend**: HTML templates with Spanish translations
- **Database**: SQLite with foreign key constraints
- **Styling**: Milligram CSS framework