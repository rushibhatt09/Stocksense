# StockSense - Project Overview

## Problem Statement

**Goal**: Build a modular Inventory Management System (IMS) that digitalizes and streamlines all stock-related operations within a business. Replace manual registers, Excel sheets, and scattered tracking methods with a centralized, real-time, easy-to-use app.

### Target Users

- **Inventory Managers** – Manage incoming & outgoing stock, monitor stock levels
- **Warehouse Staff** – Perform transfers, picking, shelving, and physical counts

---

## Core Features

### 1. Authentication & Access Control

**Signup/Login Flow**
- New user registration with name, email, password
- Role selection (Manager or Staff)
- Password validation (8-128 characters)
- OTP-based password reset for security

**Authentication Method**
- JWT bearer tokens (12-hour expiry)
- OTP codes (10-minute expiry) for password reset
- Automatic redirection to Dashboard on successful login

**User Roles**
- **Manager**: Full access to all operations and settings
- **Staff**: Warehouse operations, limited to assigned tasks

---

### 2. Dashboard (Landing Page)

Snapshot view of all inventory operations after login.

#### Dashboard KPIs

| KPI | Purpose |
|-----|---------|
| **Total Products in Stock** | Count of active products with on-hand qty > 0 |
| **Low Stock / Out of Stock Items** | Products where on-hand ≤ reorder_point |
| **Pending Receipts** | Receipt documents in Draft/Waiting/Ready status |
| **Pending Deliveries** | Delivery documents in Draft/Waiting/Ready status |
| **Internal Transfers Scheduled** | Transfer documents in Draft/Waiting/Ready status |

#### Dynamic Filters

Users can filter operations by:
- **Document Type**: Receipts / Delivery / Internal Transfer / Adjustments
- **Status**: Draft, Waiting, Ready, Done, Canceled
- **Warehouse/Location**: Scope to specific warehouse or location
- **Date Range**: Filter by date created or scheduled

---

### 3. Product Management

#### Create/Update Products

Product details:
- **Name**: Product description (required)
- **SKU / Code**: Unique product identifier (required)
- **Category**: Assign to a product category
- **Unit of Measure (UOM)**: e.g., kg, liters, units, boxes
- **Initial Stock**: Optional stock when creating
- **Barcode**: Optional for scanning
- **Reorder Point**: Stock level threshold for low-stock alerts
- **Reorder Quantity**: Standard quantity to order when low
- **Status**: Active/Inactive toggle

#### Stock Availability Per Location

- View current on-hand quantity at each warehouse/location
- Real-time stock derived from stock moves ledger
- Drill down to move history for a product at a location

#### Product Categories

- Hierarchical categories (parent-child relationships)
- Organize products for reporting & filtering
- Support for product attributes per category

#### Reordering Rules

- Define reorder_point (trigger for low-stock alert)
- Define reorder_qty (standard replenishment amount)
- Dashboard alerts when stock drops below reorder_point

---

### 4. Core Operations

#### 4.1 Receipts (Incoming Stock)

**Purpose**: Record goods arriving from vendors

**Workflow**:
1. Create a new Receipt document
2. Add supplier information & products
3. Input quantities received against each line
4. Validate the document
5. Stock increases automatically per `stock_moves` ledger

**Example**:
- Receive 50 units of "Steel Rods" from Vendor A
- Result: Total stock of Steel Rods +50

**Document Fields**:
- Reference number (auto-generated, e.g., WH1/IN/0001)
- Supplier name
- Document lines: Product, Qty Demanded, Qty Received
- Status: Draft → Waiting → Ready → Done
- Scheduled date (when goods are expected)
- Validated date (when goods confirmed)

#### 4.2 Delivery Orders (Outgoing Stock)

**Purpose**: Record goods leaving the warehouse to customers

**Workflow**:
1. Create a new Delivery document
2. Add customer information & products
3. Input quantities to deliver
4. Validate (pick, pack, confirm)
5. Stock decreases automatically

**Example**:
- Sales order for 10 chairs
- Delivery order reduces stock of chairs by 10

**Document Fields**:
- Reference number (auto-generated, e.g., WH1/OUT/0001)
- Customer name
- Document lines: Product, Qty Demanded, Qty Delivered
- Status: Draft → Waiting → Ready → Done
- Scheduled date (when delivery is due)
- Validated date (when goods shipped)

#### 4.3 Internal Transfers

**Purpose**: Move stock between locations within the company

**Examples**:
- Main Warehouse → Production Floor
- Shelf A → Shelf B (within same warehouse)
- Warehouse 1 → Warehouse 2 (multi-site)

**Workflow**:
1. Create Internal Transfer document
2. Select source location (from)
3. Select destination location (to)
4. Add products & quantities
5. Validate the transfer
6. Stock location updates, total stock unchanged

**Document Fields**:
- Reference number (e.g., WH1/INT/0001)
- Source location
- Destination location
- Document lines: Product, Qty Demanded, Qty Moved
- Status: Draft → Waiting → Ready → Done
- Scheduled date & validated date

**Ledger Entry**: Each move logged separately
- Row 1: Product X, Qty 20 from "Shelf A" to "Shelf B"
- Shelf A: -20, Shelf B: +20, Total: unchanged

#### 4.4 Inventory Adjustment

**Purpose**: Correct discrepancies between recorded and physical stock

**Workflow**:
1. Perform physical count
2. Create Adjustment document for product & location
3. Enter counted quantity vs recorded quantity
4. System calculates difference
5. Stock auto-updates with adjustment move

**Example**:
- Recorded stock of Steel: 100 kg
- Physical count: 97 kg
- Adjustment: -3 kg (damaged/lost)
- New stock: 97 kg

**Document Fields**:
- Reference number (e.g., WH1/ADJ/0001)
- Product & location
- Recorded quantity
- Counted quantity
- Difference (calculated)
- Reason (damage, shrinkage, miscounting, etc.)
- Status: Draft → Waiting → Ready → Done

---

### 5. Move History (Stock Ledger)

Complete audit trail of all stock movements.

**View**:
- All stock moves (append-only ledger)
- Product, source location, destination location, quantity
- Timestamp of when move occurred
- Link to originating document

**Filters**:
- By product
- By location
- By date range
- By document type
- By user (who created the move)

**Purpose**: 
- Audit trail for compliance
- Troubleshooting stock discrepancies
- Understanding stock flow

---

### 6. Settings

#### Warehouse Management

**Warehouses**:
- Create/edit warehouses (e.g., "Main Warehouse", "Branch 2")
- Set warehouse code & address
- Parent entity for locations

**Locations**:
- Create/edit locations within warehouses
- Examples: "Shelf A", "Bin 123", "Packing Area"
- Hierarchical structure (parent locations)
- Location types: Internal (physical), Vendor (virtual), Customer (virtual), Adjustment (virtual), Scrap (virtual)
- Used as source/destination in operations

---

### 7. Profile Menu (Sidebar)

**User Profile**:
- View current user details (name, email, role)
- Edit profile information
- Change password
- View account creation date

**Logout**:
- Clear authentication token
- Return to login screen

---

## Navigation Structure

```
📊 Dashboard
   └─ View KPIs, pending operations, filters

📦 Products
   ├─ Product list, create/edit
   ├─ Categories
   └─ Stock availability per location

📥 Receipts
   ├─ Create receipt
   ├─ View receipt list
   └─ Manage receipt documents

📤 Deliveries
   ├─ Create delivery order
   ├─ View delivery list
   └─ Manage delivery documents

🔄 Internal Transfers
   ├─ Create transfer
   ├─ View transfer list
   └─ Manage transfer documents

📋 Inventory Adjustments
   ├─ Create adjustment
   ├─ View adjustment list
   └─ Manage adjustment documents

📖 Move History
   └─ Stock ledger (all moves, filterable)

⚙️ Settings
   ├─ Warehouses & Locations
   └─ Categories (optional)

👤 Profile Menu (Sidebar)
   ├─ My Profile
   └─ Logout
```

---

## Technical Architecture

### Single Source of Truth: Stock Ledger

**Key Principle**: The `stock_moves` table is append-only and the **only** place quantities are stored.

```
stock_moves ledger:
────────────────────────────────────────────────────
id | product_id | from_location | to_location | qty | timestamp
────────────────────────────────────────────────────
1  | 5          | Vendor        | Shelf A     | 100 | 2026-01-01
2  | 5          | Shelf A       | Shelf B     | 20  | 2026-01-02
3  | 5          | Shelf B       | Customer    | 20  | 2026-01-03
4  | 5          | Adjustment    | Shelf A     | -3  | 2026-01-04
────────────────────────────────────────────────────

On-hand Stock Calculation:
Product 5, Shelf A: 100 - 20 - 3 = 77
Product 5, Shelf B: 20 - 20 = 0
Total Product 5: 77 + 0 = 77
```

### Why This Approach?

✅ **Complete audit trail**: Every move is logged
✅ **No drift**: Stock is always derived from moves
✅ **Self-balancing**: Ledger entries are balanced (from A to B)
✅ **Error recovery**: Mistakes corrected by reversing entries
✅ **Real-time**: Stock updated immediately on validation

---

## Example Flow: End-to-End

### Step 1: Receive Goods from Vendor

**Action**: Receive 100 kg Steel Rods
- Create Receipt document
- Add: Product "Steel Rods", Qty 100, Supplier "Steel Corp"
- Validate document
- **Ledger Entry**: `(Vendor, Shelf A, Steel Rods, +100)`
- **Result**: Total stock of Steel Rods = 100 kg

### Step 2: Move to Production Rack

**Action**: Internal Transfer of 40 kg to Production
- Create Transfer document
- Add: Product "Steel Rods", 40 kg, From "Shelf A" → To "Production Rack"
- Validate document
- **Ledger Entry**: `(Shelf A, Production Rack, Steel Rods, +40)`
- **Result**: 
  - Shelf A: 60 kg
  - Production Rack: 40 kg
  - Total: 100 kg (unchanged)

### Step 3: Deliver Finished Goods

**Action**: Deliver 20 kg Steel Rods to Customer
- Create Delivery document
- Add: Product "Steel Rods", Qty 20, Customer "ABC Inc"
- Validate document
- **Ledger Entry**: `(Production Rack, Customer, Steel Rods, +20)`
- **Result**: Production Rack: 20 kg

### Step 4: Adjust for Damaged Items

**Action**: Physical count reveals 2 kg damaged
- Create Adjustment document
- Product "Steel Rods", Recorded: 20 kg, Counted: 18 kg, Difference: -2 kg
- Validate document
- **Ledger Entry**: `(Production Rack, Scrap, Steel Rods, +2)`
- **Result**: Production Rack: 18 kg

---

## Business Rules

### Product Rules
- SKU must be unique
- Product must belong to a category
- Reorder point & quantity define low-stock alerts
- Products can be marked inactive (archived)

### Warehouse/Location Rules
- Warehouse code must be unique
- Location code must be unique
- Internal locations must belong to a warehouse
- Virtual locations (vendor, customer, adjustment, scrap) have no warehouse

### Document Rules
- Each document gets a unique reference (auto-generated)
- Status workflow: Draft → Waiting → Ready → Done (or Canceled)
- Cannot edit validated documents (create adjustment instead)
- All operations require a user (creator)

### Stock Movement Rules
- Moves are **append-only** (never updated or deleted)
- Each move has a source & destination location
- Qty must be positive (reversals done with new entries)
- Moves are **balanced**: Total In = Total Out

### Authorization Rules
- Managers: Full CRUD on all entities
- Staff: View dashboard, create/edit operations, cannot access settings
- Only created-by user or manager can edit draft documents

---

## Future Enhancements

### Phase 2
- Barcode scanning for faster receipt/delivery
- Multi-user login tracking per session
- Export reports (PDF, Excel)
- Email notifications for low stock

### Phase 3
- Supplier management (contact info, reorder history)
- Customer management
- Batch/lot tracking
- Serial number tracking
- Cost tracking (FIFO, LIFO, weighted average)

### Phase 4
- Mobile app for warehouse staff
- Real-time sync across devices
- Offline mode with sync
- Advanced analytics & forecasting
- Integration with ERP systems

---

## Success Metrics

✅ **System goes live** with all core operations
✅ **Zero manual register** need for stock tracking
✅ **Real-time visibility** into stock levels
✅ **100% audit trail** for compliance
✅ **Sub-second queries** for dashboard KPIs
✅ **<1 minute** average time to complete an operation
✅ **Zero data loss** (append-only ledger)
✅ **<5 second** mobile page load time

---

## Deployment

### Development
- Frontend: `npm run dev` (http://localhost:5173)
- Backend: `uvicorn app.main:app --reload` (http://localhost:8000)
- Database: SQLite (automatic) or PostgreSQL (docker-compose)

### Production
- Frontend: Built assets served via nginx/CDN
- Backend: Uvicorn behind reverse proxy (nginx, traefik)
- Database: PostgreSQL (managed instance)
- Auth: All endpoints HTTPS only
- OTP: Real email service (SendGrid, AWS SES, etc.)

---

## Mock-Up Reference

**UI Design**: https://link.excalidraw.com/l/65VNwvy7c4X/3ENvQFu9o8R

---

## Current Status

**✅ Completed**
- Problem statement & feature design
- Database schema & ER model
- Auth system (JWT + OTP)
- Backend scaffolding (FastAPI)
- Frontend scaffolding (React + Router)
- Demo data seeder

**🚧 In Progress**
- Auth routes & guards
- Product API routes
- Warehouse/location API routes
- Inventory operation routes (receipts, deliveries, transfers, adjustments)
- Stock move ledger logic
- Frontend pages & components

**⏳ Not Started**
- Email integration (OTP sending)
- File uploads (attachments)
- Advanced reporting
- Mobile app

---

**Last Updated**: 2026-09-26  
**Repository**: StockSense  
**Problem Statement**: Hackathon Project (Inventory Management System)
