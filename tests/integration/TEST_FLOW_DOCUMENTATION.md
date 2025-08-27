# Test Flow Documentation

This document explains the comprehensive test flow of the restaurant management system's integration tests.

## Overview

The test suite (`tests/integration/test_app.py`) performs a complete end-to-end validation of all system functionality, covering 16+ endpoints and complex business logic scenarios. The tests are designed to simulate real restaurant operations from menu setup to order completion.

## Test Environment Setup

- **Database**: Uses isolated test database via `DATABASE_PATH` environment variable
- **Server**: Expects Flask server running on `http://127.0.0.1:5000`
- **Authentication**: Uses session-based requests to maintain state
- **Cleanup**: Automatically deletes test database after completion

## Detailed Test Flow

### Phase 1: Basic Endpoint Accessibility (8 endpoints)
Tests all primary GET endpoints to ensure system is responsive:

1. **GET /** - Dashboard page
2. **GET /menu** - Menu management page
3. **GET /menu/audit** - Menu audit trail page
4. **GET /movements** - Stock movements page
5. **GET /movements/add** - Add stock movement form
6. **GET /tables** - Restaurant tables page
7. **GET /tables/add** - Add table form
8. **GET /orders** - Orders list page

**Purpose**: Verify all main pages load correctly and server is operational.

---

### Phase 2: Menu System Setup and Testing
Creates test data and validates menu management functionality:

#### Step 1: Create Test Menu Items
- **Create Pizza (Stockable)**:
  - Name: "Pizza Margherita Test"
  - Price: $15.99
  - Category: food
  - Stockable: Yes (generates inventory movements)
  - **Endpoint**: `POST /menu/add`
  - **Verification**: Item exists in database with correct attributes

- **Create Service (Non-Stockable)**:
  - Name: "Table Service Test" 
  - Price: $5.00
  - Category: food
  - Stockable: No (no inventory impact)
  - **Endpoint**: `POST /menu/add`
  - **Verification**: Item exists in database with stockable=0

#### Step 2: Test Menu Editing Capabilities
- **Edit Pizza Item**:
  - **Endpoint**: `GET /menu/edit/1` (load edit form)
  - **Endpoint**: `POST /menu/edit/1` (update item)
  - Changes: Name → "Pizza Margherita Test Updated", Price → $16.99
  - **Verification**: Database updated, audit trail created
  - **Business Logic**: Menu audit table tracks all changes with old/new values

**Database State After Phase 2:**
```
menu_items: 2 items (1 stockable pizza, 1 non-stockable service)
menu_audit: 2+ entries tracking create/edit operations
```

---

### Phase 3: Table Management System
Sets up restaurant tables for order processing:

#### Step 3: Create Primary Table
- **Create Table 99**:
  - Capacity: 4 people
  - Status: available
  - **Endpoint**: `POST /tables/add`
  - **Verification**: Table exists with correct capacity

#### Step 4: Create Additional Table  
- **Create Table 88**:
  - Capacity: 6 people
  - Status: available
  - **Endpoint**: `POST /tables/add`
  - **Verification**: Both tables exist, different capacities confirmed

**Database State After Phase 3:**
```
restaurant_tables: 2 tables (88 & 99) both available
```

---

### Phase 4: Stock Management System
Establishes inventory levels and tests stock operations:

#### Step 5: Add Initial Stock
- **Add Stock to Pizza**:
  - Quantity: +50 units
  - Notes: "Initial stock for testing"
  - **Endpoint**: `POST /movements/add`
  - **Verification**: Current stock = 50 units

#### Step 6: Test Complex Stock Movements
- **Manual Stock Reduction**:
  - Quantity: -10 units
  - Notes: "Manual stock reduction for testing"
  - **Endpoint**: `POST /movements/add`
  - **Verification**: Stock movement recorded

- **Additional Stock Delivery**:
  - Quantity: +25 units  
  - Notes: "Additional stock delivery"
  - **Endpoint**: `POST /movements/add`
  - **Verification**: Running total = 50 - 10 + 25 = 65 units

**Database State After Phase 4:**
```
movements: 3 entries for pizza (Initial: +50, Reduction: -10, Addition: +25)
Current stock: 65 units
```

---

### Phase 5: Core Order Processing (E2E Workflow)
Simulates complete customer order lifecycle:

#### Step 7: Create Customer Order
- **Create Order on Table 99**:
  - Customer: "Test Customer E2E"
  - **Endpoint**: `POST /orders/new/99`
  - **Status**: Returns 302 redirect to order detail page
  - **Verification**: Order created with status='active', table status updated

#### Step 8: Add Items to Order
- **Add Pizza (Stockable Item)**:
  - Quantity: 3 units
  - Notes: "Extra cheese please"
  - **Endpoint**: `POST /orders/{order_id}/add_item`
  - **Business Logic**: No stock movement yet (only on order closure)

- **Add Service (Non-Stockable Item)**:
  - Quantity: 1 unit
  - Notes: "Premium service"
  - **Endpoint**: `POST /orders/{order_id}/add_item`
  - **Verification**: Both items in order_items table

#### Step 9: Verify Order State (Pre-Closure)
- **Stock Verification**: Stock remains at 65 units (unchanged)
- **Order Items**: 2 items confirmed (pizza: 3 qty, service: 1 qty)
- **Business Rule**: Stock only moves when orders are closed, not when items are added

#### Step 10: Close Order with Payment Processing
- **Calculate Order Total**: 3 × $16.99 + 1 × $5.00 = $55.97
- **Process Payment**:
  - Method: Cash
  - Amount: $55.97 (exact match required)
  - **Endpoint**: `POST /orders/{order_id}/close`
  - **Payment Validation**: Total must match within $0.01

#### Step 11: Verify Order Closure Effects
- **Order Status**: Changed to 'closed' with timestamp
- **Table Status**: Table 99 becomes available again
- **Stock Movement**: -3 units for pizza (65 → 62 units)
- **Payment Record**: $55.97 cash payment recorded
- **No Service Stock Movement**: Confirmed (non-stockable item)

**Database State After Phase 5:**
```
orders: 1 closed order with payment info
order_items: 2 items (pizza: 3 qty, service: 1 qty)  
movements: 4 entries (original 3 + order closure: -3)
Current pizza stock: 62 units
order_payments: 1 payment record ($55.97 cash)
```

---

### Phase 6: Order History Validation
Verifies complete audit trail functionality:

#### Step 12: Validate Order Item History
- **History Entries**: 2 'added' actions tracked
- **Pizza Entry**: Action='added', Quantity=3, Item="Pizza Margherita Test Updated"
- **Service Entry**: Action='added', Quantity=1, Item="Table Service Test"
- **Timestamps**: All actions timestamped for audit compliance
- **Purpose**: Ensures complete traceability of all order modifications

---

### Phase 7: Advanced Order Operations Testing
Tests comprehensive order management capabilities:

#### Step 13: Create Second Order (Table 88)
- **Customer**: "Second Customer Test"
- **Endpoint**: `POST /orders/new/88`
- **Purpose**: Test multi-table operations

#### Step 14: Test Order Detail Access
- **Endpoint**: `GET /orders/{order_id}`
- **Verification**: Order detail page loads correctly
- **Purpose**: Confirm order viewing functionality

#### Step 15: Test Advanced Order Item Operations

**Add Item to Second Order**:
- **Item**: Pizza (2 units)
- **Notes**: "Less cheese this time"
- **Endpoint**: `POST /orders/{order_id}/add_item`

**Edit Order Item**:
- **Change Quantity**: 2 → 3 units
- **Change Notes**: "Less cheese" → "Changed to extra cheese"
- **Endpoint**: `POST /orders/{order_id}/items/{item_id}/edit`
- **History Tracking**: Creates 'old_edited' and 'new_edited' audit entries

**Remove Order Item**:
- **Endpoint**: `POST /orders/{order_id}/items/{item_id}/remove`
- **History Tracking**: Creates 'removed' audit entry
- **Verification**: Item removed from order, history preserved

#### Step 16: Final Stock Calculation Verification
- **Final Stock Check**: Confirms all movements calculated correctly
- **Multiple Movement Sources**: Initial stock + manual adjustments + order consumption
- **Expected Calculation**: 50 (initial) - 10 (reduction) + 25 (addition) - 3 (order) = 62 units

---

## Business Logic Validation

### Stock Management Rules
1. **Stock movements only occur on order closure**, not when items are added to orders
2. **Only stockable items generate movements** (non-stockable items ignored)
3. **Running totals calculated from all movements** using SQL SUM operations
4. **Audit trail maintained** for all stock changes with notes and timestamps

### Order Management Rules  
1. **Orders start as 'active'** and can be edited freely
2. **Payment required for order closure** with exact total matching
3. **Complete history tracking** for all order item modifications
4. **Table status management** (available ↔ in use) based on active orders

### Payment Processing Rules
1. **Multiple payment methods supported** (cash, card, etc.)
2. **Split payments allowed** with multiple method/amount pairs
3. **Payment validation enforced** (total must match order within $0.01)
4. **Payment history recorded** in order_payments table

## Test Data Summary

After complete test execution:
- **Menu Items**: 2 items (1 stockable, 1 non-stockable)
- **Tables**: 2 tables (different capacities)
- **Orders**: 2 orders (1 closed with payment, 1 active then modified)
- **Stock Movements**: 4+ movements (initial, manual adjustments, order consumption)
- **Audit Records**: 10+ audit entries across menu and order history tables
- **Final Stock Level**: 62 units for pizza item

## Error Scenarios Covered

1. **Payment Validation**: Order closure fails if payment doesn't match total
2. **Stock Verification**: Ensures stock doesn't change prematurely
3. **Database Integrity**: All foreign key relationships maintained
4. **Status Code Validation**: Correct HTTP response codes (200 for pages, 302 for form submissions)
5. **Data Consistency**: Cross-table data verification throughout

## Performance Considerations

- **Database Operations**: Uses transactions and proper connection management
- **Test Isolation**: Each test run uses fresh database
- **Sequential Operations**: Tests maintain proper order dependencies
- **Resource Cleanup**: Automatic database cleanup after test completion

This comprehensive test flow ensures the restaurant management system functions correctly across all business scenarios and maintains data integrity throughout complex operations.