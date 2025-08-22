# Restaurant Management System - Testing Guide

## Installation

Install dependencies using uv:
```bash
uv pip install -r requirements.txt
```

## Quick Testing Scripts

### 1. Automated Endpoint Test
```bash
python3 quick_test.py
```
This tests basic endpoint availability and responses.

### 2. Comprehensive E2E Test (when server is stopped)
```bash
python3 test_app.py
```
This performs full database testing but requires the Flask server to be stopped first to avoid database locks.

---

## Manual E2E Testing Workflow

**Server URL:** http://127.0.0.1:5001

### Test Scenario: Complete Order Flow with Stock Management

#### Step 1: Create Menu Items
1. Go to **Menu** (Menú)
2. Click **Agregar Nuevo Artículo**
3. Create **Stockable Item**:
   - Name: `Pizza Margarita`
   - Description: `Pizza with tomato and cheese`
   - Category: `Comida`
   - Price: `15.99`
   - ✅ **Check "Controlar Stock"**
   - Click **Agregar Artículo**

4. Create **Non-Stockable Item**:
   - Name: `Mesa Service` 
   - Description: `Table service charge`
   - Category: `Comida`
   - Price: `5.00`
   - ❌ **Leave "Controlar Stock" unchecked**
   - Click **Agregar Artículo**

**Expected:** Both items appear in the menu list.

#### Step 2: Add Stock to Stockable Item
1. Go to **Movimientos de Stock**
2. Click **Agregar Movimiento**
3. Fill form:
   - Artículo: `Pizza Margarita`
   - Cambio de Stock: `+25` (positive number to add stock)
   - Notas: `Initial inventory`
4. Click **Agregar Movimiento**

**Expected:** 
- Movement appears in history
- Stock shows as 25 for Pizza Margarita on Dashboard

#### Step 3: Create Table
1. Go to **Mesas del Restaurante**
2. Click **Agregar Mesa**
3. Fill form:
   - Número de Mesa: `10`
   - Capacidad: `4`
4. Click **Agregar Mesa**

**Expected:** Table 10 appears with "Disponible" status.

#### Step 4: Create Order
1. From **Mesas**, click **Nueva Orden** on Table 10
2. Enter customer name: `Test Customer`
3. Click **Iniciar Orden**

**Expected:** Redirected to order detail page showing empty order.

#### Step 5: Add Items to Order
1. In **Agregar Artículo a la Orden** form:
   - Select `Pizza Margarita`
   - Quantity: `3`
   - Notes: `Extra cheese`
   - Click **Agregar Artículo**

2. Add second item:
   - Select `Mesa Service`
   - Quantity: `1`
   - Notes: `Premium service`
   - Click **Agregar Artículo**

**Expected:** 
- Order shows both items with correct quantities and prices
- Total calculates correctly: (3 × $15.99) + (1 × $5.00) = $52.97
- ⚠️ **Stock should NOT change yet** - check Dashboard shows Pizza still at 25

#### Step 6: Test Order Editing (New Feature)
1. Change Pizza quantity from 3 to 2 by editing the quantity field
2. Edit notes for Mesa Service by changing text and clicking 💾
3. Try removing an item using the 🗑️ button

**Expected:**
- Quantities update in real-time
- Notes save correctly
- Removed items disappear from order
- Total recalculates automatically

#### Step 7: Close Order and Verify Stock Movement
1. Click **Cerrar Orden**
2. Confirm in dialog

**Expected:**
- Order status changes to "closed"
- Redirected to orders list showing closed order

#### Step 8: Verify Stock Was Updated
1. Go to **Dashboard**
2. Check Pizza Margarita stock level

**Expected:** 
- Pizza stock should now be 23 (25 - 2, if you edited to 2 pizzas)
- Non-stockable item (Mesa Service) should have no stock tracking

#### Step 9: Verify Stock Movement History
1. Go to **Movimientos de Stock**
2. Look for automatic movement

**Expected:**
- New movement entry: `Auto: Order #[ORDER_ID] closed - Pizza Margarita x2`
- Movement type: `Out`
- Quantity change: `-2`
- Running stock shows progression: 25 → 23

#### Step 10: Verify Order History
1. Go to **Órdenes**
2. Click **Ver** on the test order

**Expected:**
- Order shows as closed with timestamp
- All items and final quantities displayed
- No edit/remove buttons (order is closed)

---

## Key Features to Verify

### ✅ Stock Management
- [ ] Stock only updates when order is **closed**, not when items are added
- [ ] Only **stockable items** affect inventory
- [ ] **Non-stockable items** never create stock movements
- [ ] Running stock calculations are correct

### ✅ Order Editing
- [ ] Can edit quantities for **active orders only**
- [ ] Can edit notes for active orders
- [ ] Can remove items from active orders
- [ ] **Closed orders** cannot be edited
- [ ] All changes are tracked in history

### ✅ User Interface
- [ ] All text is in **Spanish** (frontend)
- [ ] Forms validate correctly
- [ ] Navigation works between all sections
- [ ] Tables display data properly
- [ ] Buttons and actions work as expected

---

## Database Verification (Optional)

If you want to check the database directly:

```bash
sqlite3 app/inventory.db

-- Check order item history
SELECT * FROM order_item_history ORDER BY timestamp DESC LIMIT 10;

-- Check stock movements
SELECT * FROM movements ORDER BY date DESC LIMIT 10;

-- Check order status
SELECT o.*, rt.table_number FROM orders o 
JOIN restaurant_tables rt ON o.table_id = rt.id 
ORDER BY o.id DESC LIMIT 5;
```

---

## Troubleshooting

- **500 Errors**: Usually database locks. Stop server, restart, try again.
- **Items not appearing**: Check that forms submitted successfully (look for validation errors).
- **Stock not updating**: Ensure order is **closed** - stock only updates on order completion.
- **Edit buttons missing**: Only active orders can be edited, closed orders are read-only.