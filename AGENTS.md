# StockSense - Multi-Agent Development Guide

This document defines the four specialized agents for StockSense development, their responsibilities, owned files, and inter-agent dependencies.

---

## Overview

StockSense is developed using a **4-agent architecture**, where each agent specializes in one domain:

| Agent | Domain | Focus |
|-------|--------|-------|
| **UI Agent** | Frontend | React components, pages, UI/UX |
| **Auth/Guard Agent** | Auth & Security | Authentication, authorization, guards |
| **Inventory Agent** | Products & Stock | Product management, warehouses, locations |
| **Operations Agent** | Documents & Ledger | Receipts, deliveries, transfers, adjustments, stock moves |

---

## Agent 1: UI Agent

### Domain
**Frontend User Interface** – React components, pages, routing, styling, and user experience

### Responsibilities

1. **Dashboard Page** (`/src/pages/Dashboard.tsx`)
   - Display KPI tiles: Total Products, Low Stock Items, Pending Receipts/Deliveries/Transfers
   - Dynamic filters: By doc type, status, warehouse, date range
   - Real-time sync of pending operations
   - Cards showing latest moves & alerts

2. **Products Page** (`/src/pages/Products.tsx`)
   - Product list with search, sort, filter
   - Create/edit product form (name, SKU, category, UOM, reorder rules)
   - Product details: stock per location, reorder point, barcode
   - Bulk operations (activate/deactivate)
   - Category filter & navigation

3. **Receipt Page** (`/src/pages/Receipts.tsx`)
   - Receipt document list with status filter
   - Create receipt form: supplier, products, quantities
   - Receipt detail view & edit (draft only)
   - Line items: add/remove products
   - Validation button to mark as ready/done

4. **Delivery Page** (`/src/pages/Deliveries.tsx`)
   - Delivery document list with customer filter
   - Create delivery form: customer, products, quantities
   - Delivery detail view & edit (draft only)
   - Picking & packing workflow
   - Validation & shipment confirmation

5. **Transfers Page** (`/src/pages/Transfers.tsx`)
   - Internal transfer document list
   - Create transfer form: source location → destination location
   - Products & quantities per transfer
   - Location hierarchy browser
   - Validation workflow

6. **Adjustments Page** (`/src/pages/Adjustments.tsx`)
   - Adjustment document list
   - Create adjustment: product, location, counted qty vs recorded qty
   - Auto-calculate difference
   - Reason selector (damage, shrinkage, miscounting, etc.)
   - Validation workflow

7. **Move History Page** (`/src/pages/MoveHistory.tsx`)
   - Stock ledger view: all moves
   - Filterable by product, location, date, doc type, user
   - Columns: Product, From, To, Qty, Timestamp, Document
   - Drill down to related document
   - Export option

8. **Settings Page** (`/src/pages/SettingsWarehouses.tsx`)
   - Warehouse list: create, edit, delete
   - Location management: add/edit locations per warehouse
   - Location hierarchy (parent-child)
   - Location types: Internal, Vendor, Customer, Adjustment, Scrap
   - Virtual locations setup

9. **Profile Page** (`/src/pages/Profile.tsx`)
   - User details (name, email, role)
   - Edit profile form
   - Change password form
   - Account info (created date, last login)
   - Session management

10. **Auth Pages** (Already stubbed)
    - Login page (`/src/pages/Login.tsx`) – integration with AuthContext
    - Signup page (`/src/pages/Signup.tsx`) – registration form
    - Forgot Password page (`/src/pages/ForgotPassword.tsx`) – OTP flow

### Key Components to Build/Improve

- **AppLayout** (`/src/components/AppLayout.tsx`): Protected layout wrapper
- **Sidebar** (`/src/components/Sidebar.tsx`): Navigation menu, user menu
- **PageHeader** (`/src/components/PageHeader.tsx`): Title, breadcrumbs, actions
- **StatusBadge** (`/src/components/StatusBadge.tsx`): Status indicator styling
- **DataTable** (create): Reusable table component with sort/filter
- **Modal/Dialog** (create): Form dialogs for CRUD operations
- **KPI Card** (create): Dashboard KPI tile component
- **Form Fields** (create): Reusable input, select, date, textarea components

### Technology Stack
- React 18 + TypeScript
- React Router v6
- React Query v5 (data fetching & caching)
- Tailwind CSS (styling)
- Lucide React (icons)
- Vite (build)

### API Consumption

This agent **consumes** APIs built by other agents:

**From Auth/Guard Agent:**
- `POST /auth/login` – Login
- `POST /auth/signup` – Register
- `POST /auth/forgot-password` – Initiate reset
- `POST /auth/verify-otp` – Verify OTP
- `POST /auth/reset-password` – Complete reset
- `GET /auth/me` – Current user

**From Inventory Agent:**
- `GET /products` – List products
- `POST /products` – Create product
- `PUT /products/{id}` – Update product
- `GET /products/{id}` – Product details
- `GET /products/{id}/stock` – Stock at locations
- `GET /warehouses` – List warehouses
- `POST /warehouses` – Create warehouse
- `PUT /warehouses/{id}` – Update warehouse
- `GET /warehouses/{id}/locations` – Locations in warehouse
- `POST /locations` – Create location
- `GET /categories` – List categories
- `POST /categories` – Create category

**From Operations Agent:**
- `GET /documents` – List documents
- `POST /documents` – Create document
- `GET /documents/{id}` – Document details
- `PUT /documents/{id}` – Update document
- `POST /documents/{id}/validate` – Validate document
- `GET /stock-moves` – List stock moves
- `GET /stock-moves?product={id}&location={id}` – Filtered moves

### Output Files
```
frontend/src/pages/
  ├─ Dashboard.tsx
  ├─ Products.tsx
  ├─ Receipts.tsx
  ├─ Deliveries.tsx
  ├─ Transfers.tsx
  ├─ Adjustments.tsx
  ├─ MoveHistory.tsx
  ├─ SettingsWarehouses.tsx
  ├─ Profile.tsx
  ├─ Login.tsx (complete)
  ├─ Signup.tsx (complete)
  └─ ForgotPassword.tsx (complete)

frontend/src/components/
  ├─ AppLayout.tsx (enhance)
  ├─ Sidebar.tsx (enhance)
  ├─ PageHeader.tsx (enhance)
  ├─ StatusBadge.tsx (enhance)
  ├─ DataTable.tsx (new)
  ├─ Modal.tsx (new)
  ├─ KpiCard.tsx (new)
  └─ FormFields/
      ├─ Input.tsx
      ├─ Select.tsx
      ├─ DateInput.tsx
      └─ TextArea.tsx

frontend/src/lib/
  └─ api.ts (augment with new endpoints)
```

---

## Agent 2: Auth/Guard Agent

### Domain
**Authentication & Authorization** – User authentication, OTP, JWT tokens, role-based access control

### Responsibilities

1. **Auth Routes** (`backend/app/api/routes/auth.py`)
   - ✅ Already implemented:
     - `POST /auth/signup` – User registration
     - `POST /auth/login` – Login with email/password
     - `GET /auth/me` – Current user
     - `POST /auth/forgot-password` – Request OTP
     - `POST /auth/verify-otp` – Verify OTP code
     - `POST /auth/reset-password` – Reset password with token

2. **Security & Tokens** (`backend/app/core/security.py`)
   - ✅ Already implemented:
     - Password hashing (bcrypt)
     - JWT token creation (access & reset tokens)
     - Token validation & decoding
   - 🚧 To enhance:
     - Token refresh mechanism
     - Rate limiting for login attempts
     - Brute force protection

3. **OTP Service** (`backend/app/services/otp.py`)
   - ✅ Core implementation complete
   - 🚧 Enhancements needed:
     - Email sending (currently prints to console in dev)
     - SMTP configuration for production
     - OTP retry limits
     - OTP validation logging

4. **Dependencies** (`backend/app/api/deps.py`)
   - ✅ `get_current_user` – Extracts user from token
   - 🚧 To add:
     - `get_current_manager` – Guard for managers only
     - `get_current_staff` – Guard for staff only
     - `check_document_owner` – Guard for document ownership
     - Rate limiting middleware

5. **Database Models** (`backend/app/models/user.py`)
   - ✅ User model complete
   - ✅ OtpToken model complete
   - 🚧 Consider:
     - User login history (audit)
     - Failed login tracking
     - Session management

6. **Frontend Auth Context** (`frontend/src/auth/AuthContext.tsx`)
   - ✅ Basic auth context setup
   - 🚧 Enhancements:
     - Token refresh logic
     - Auto-logout on token expiry
     - Loading states
     - Error handling

7. **Authorization Middleware**
   - 🚧 To build:
     - Role-based access middleware
     - Document ownership validation
     - Location access validation
     - API guard wrappers

### API Endpoints (Owned by This Agent)

**Public (No Auth Required)**
- `POST /auth/signup` – Create account
- `POST /auth/login` – Get token
- `POST /auth/forgot-password` – Request OTP
- `POST /auth/verify-otp` – Verify code
- `POST /auth/reset-password` – Complete reset

**Protected (Bearer Token Required)**
- `GET /auth/me` – Get current user

### Key Implementation Details

**Password Policy**
- Minimum 8 characters, maximum 128
- Hashed with bcrypt + salt
- Never transmitted in plain text

**JWT Payload Structure**
```json
{
  "sub": "1",
  "exp": 1234567890,
  "iat": 1234567800,
  "type": "access"  // or "reset"
}
```

**OTP Format**
- 6-digit numeric code
- 10-minute expiry
- Single use only
- Hashed in database

**User Roles**
```python
class Role:
    MANAGER = "manager"
    STAFF = "staff"
```

### Output Files
```
backend/app/api/routes/
  └─ auth.py (already done, maintain)

backend/app/core/
  ├─ security.py (enhance for token refresh, rate limiting)
  └─ config.py (add OTP email config)

backend/app/services/
  └─ otp.py (enhance with email sending)

backend/app/api/
  └─ deps.py (add manager/staff guards)

backend/app/models/
  └─ user.py (already done, maintain)

frontend/src/auth/
  └─ AuthContext.tsx (enhance)
```

### Dependencies
- Depends on: Nothing
- Required by: UI Agent, Inventory Agent, Operations Agent

---

## Agent 3: Inventory Agent

### Domain
**Inventory Management** – Products, categories, warehouses, locations, stock visibility

### Responsibilities

1. **Product Management**
   - Product CRUD (Create, Read, Update, Delete)
   - SKU validation (unique)
   - Category assignment
   - UOM (Unit of Measure) management
   - Reorder point & quantity
   - Barcode support
   - Product status (active/inactive)

2. **Categories**
   - Hierarchical categories (parent-child)
   - Category CRUD
   - Organize products by type

3. **Warehouse Management**
   - Warehouse CRUD
   - Warehouse code (unique)
   - Address & contact info
   - Multi-warehouse support

4. **Locations**
   - Location CRUD within warehouses
   - Location types: Internal, Vendor, Customer, Adjustment, Scrap
   - Hierarchical locations (parent-child)
   - Virtual locations for non-physical entities
   - Location code (unique)

5. **Stock Queries**
   - Get on-hand stock per location (derived from stock_moves)
   - Get stock per product across all locations
   - Low-stock alerts (on-hand ≤ reorder_point)
   - Stock movement history per location/product

6. **Reordering Logic**
   - Flag products where on-hand ≤ reorder_point
   - Suggest reorder_qty based on rules
   - Dashboard low-stock widget

### API Endpoints (To Implement)

**Products**
```
GET /products                          # List all products (with filters)
POST /products                         # Create new product
GET /products/{id}                     # Get product details
PUT /products/{id}                     # Update product
DELETE /products/{id}                  # Delete (soft delete)
GET /products/{id}/stock               # On-hand stock at all locations
GET /products?category={cat_id}        # Filter by category
GET /products?low_stock=true           # Low stock only
```

**Categories**
```
GET /categories                        # List all categories
POST /categories                       # Create category
PUT /categories/{id}                   # Update category
DELETE /categories/{id}                # Delete category
```

**Warehouses**
```
GET /warehouses                        # List all warehouses
POST /warehouses                       # Create warehouse
GET /warehouses/{id}                   # Get warehouse details
PUT /warehouses/{id}                   # Update warehouse
DELETE /warehouses/{id}                # Delete warehouse
GET /warehouses/{id}/locations         # Locations in warehouse
```

**Locations**
```
GET /locations                         # List all locations
POST /locations                        # Create location
GET /locations/{id}                    # Get location details
PUT /locations/{id}                    # Update location
DELETE /locations/{id}                 # Delete location
GET /locations?warehouse={wh_id}       # Filter by warehouse
GET /locations?type=internal           # Filter by type
```

### Database Models (To Build/Enhance)

**Product Model** (`backend/app/models/inventory.py`)
- ✅ Already defined
- 🚧 Relationships to add:
  - Reverse relation from stock_moves

**Warehouse Model**
- ✅ Already defined
- 🚧 Methods to add:
  - `get_locations()` – Efficient fetch
  - `get_stock()` – Warehouse-wide stock view

**Location Model**
- ✅ Already defined
- 🚧 Methods to add:
  - `is_physical` property ✅ already done
  - `get_on_hand()` – Sum of stock_moves to this location

**Category Model**
- ✅ Already defined
- 🚧 Methods to add:
  - `get_children()` – Hierarchical query
  - `get_products()` – Products in category

### Business Logic

**Stock Calculation**
```python
def get_on_hand(product_id: int, location_id: int) -> float:
    """
    Sum all stock moves for this product at this location.
    from_location_id = location: subtract qty
    to_location_id = location: add qty
    """
    result = db.query(func.sum(StockMove.qty)).filter(
        StockMove.product_id == product_id,
        StockMove.to_location_id == location_id
    ).scalar() or 0
    result -= db.query(func.sum(StockMove.qty)).filter(
        StockMove.product_id == product_id,
        StockMove.from_location_id == location_id
    ).scalar() or 0
    return result
```

**Low Stock Detection**
```python
def is_low_stock(product_id: int, location_id: int) -> bool:
    product = db.get(Product, product_id)
    on_hand = get_on_hand(product_id, location_id)
    return on_hand <= product.reorder_point
```

### Output Files
```
backend/app/api/routes/
  ├─ products.py (new)
  ├─ warehouses.py (new)
  └─ locations.py (new)

backend/app/models/
  └─ inventory.py (enhance with methods)

backend/app/schemas/
  ├─ products.py (new)
  ├─ warehouses.py (new)
  └─ locations.py (new)
```

### Schema Files (Pydantic Models for Request/Response)

**Products Schema**
```python
class ProductIn(BaseModel):
    name: str
    sku: str
    category_id: int | None
    uom: str = "Unit"
    reorder_point: float = 0
    reorder_qty: float = 0

class ProductOut(BaseModel):
    id: int
    name: str
    sku: str
    category_id: int | None
    uom: str
    reorder_point: float
    reorder_qty: float
```

Similar for Warehouses, Locations, Categories

### Dependencies
- Depends on: Auth/Guard Agent
- Required by: UI Agent, Operations Agent

---

## Agent 4: Operations Agent

### Domain
**Stock Operations** – Documents (receipts, deliveries, transfers, adjustments), stock ledger, validation logic

### Responsibilities

1. **Receipt Operations**
   - Create receipt document
   - Add/remove receipt lines (product, qty)
   - Validate receipt (create stock moves)
   - Track supplier info

2. **Delivery Operations**
   - Create delivery document
   - Add/remove delivery lines (product, qty)
   - Validate delivery (create stock moves)
   - Track customer info

3. **Internal Transfer Operations**
   - Create transfer document
   - Add/remove transfer lines
   - Validate transfer (create stock moves)
   - Source & destination location validation

4. **Inventory Adjustment Operations**
   - Create adjustment document
   - Product & location selection
   - Recorded vs. counted qty
   - Auto-calculate difference
   - Validate adjustment (create stock moves)

5. **Stock Move Ledger**
   - Append-only ledger view
   - Never update/delete moves
   - Reversals done by creating opposite moves
   - Timestamp every move

6. **Document Workflow**
   - Status transitions: Draft → Waiting → Ready → Done → (Canceled)
   - Document reference numbering (auto-generated)
   - Document validation logic
   - Prevent editing validated documents

7. **Stock Move Creation**
   - Atomic creation (all lines → all moves in one transaction)
   - Move location validation
   - Qty validation (no negative on-hand)
   - Move timestamping

### API Endpoints (To Implement)

**Documents (Generic)**
```
GET /documents                         # List all documents
GET /documents?doc_type=receipt        # Filter by type
GET /documents?status=draft            # Filter by status
GET /documents?warehouse={id}          # Filter by warehouse
POST /documents                        # Create document
GET /documents/{id}                    # Get document details
PUT /documents/{id}                    # Update document (draft only)
POST /documents/{id}/validate          # Validate document
POST /documents/{id}/cancel            # Cancel document
DELETE /documents/{id}                 # Delete document (draft only)
```

**Document Lines**
```
POST /documents/{id}/lines             # Add line item
PUT /documents/{id}/lines/{line_id}    # Update line
DELETE /documents/{id}/lines/{line_id} # Remove line
```

**Stock Moves**
```
GET /stock-moves                       # List all moves
GET /stock-moves?product={id}          # Filter by product
GET /stock-moves?location={id}         # Filter by location
GET /stock-moves?from_date=2026-01-01  # Filter by date
GET /stock-moves/{id}                  # Get move details
```

### Database Models (To Build/Enhance)

**Document Model** (`backend/app/models/operations.py`)
- ✅ Already defined
- 🚧 Methods to add:
  - `validate()` – Perform validations before creating moves
  - `create_stock_moves()` – Generate stock_moves
  - `can_edit()` – Check if still in draft
  - `get_status_display()` – Human-readable status

**DocumentLine Model**
- ✅ Already defined
- 🚧 Methods to add:
  - `get_qty_remaining()` – qty_demand - qty_done

**StockMove Model**
- ✅ Already defined (append-only)
- ✅ Relationships complete
- Methods:
  - Pure read-only (no updates/deletes)

### Validation Logic

**Receipt Validation**
```
✓ Supplier name provided
✓ At least one line item
✓ All products exist
✓ All quantities > 0
✓ Destination location is internal & physical
✓ Source location is "Vendor" type
✓ Status is Draft/Waiting
→ Create stock_moves, set status=Done, set validated_at
```

**Delivery Validation**
```
✓ Customer name provided
✓ At least one line item
✓ All products exist
✓ All quantities > 0
✓ Enough stock at source location
✓ Source location is internal & physical
✓ Destination location is "Customer" type
✓ Status is Draft/Waiting/Ready
→ Create stock_moves, set status=Done, set validated_at
```

**Transfer Validation**
```
✓ At least one line item
✓ All products exist
✓ All quantities > 0
✓ Enough stock at source location
✓ Source location is physical
✓ Destination location is physical & different from source
✓ Status is Draft/Waiting
→ Create stock_moves, set status=Done, set validated_at
```

**Adjustment Validation**
```
✓ Product exists
✓ Location is physical
✓ Counted quantity ≥ 0
✓ Difference calculated correctly
✓ Status is Draft/Waiting
→ Create stock_move(s) for difference, set status=Done, set validated_at
```

### Stock Move Creation (Pseudo-Code)

```python
def create_stock_moves(document: Document):
    """Create stock moves from document lines."""
    moves = []
    for line in document.lines:
        # Get actual quantity to move (qty_done or qty_demand)
        qty = line.qty_done if line.qty_done > 0 else line.qty_demand
        
        # Create move from source to destination
        move = StockMove(
            document_id=document.id,
            product_id=line.product_id,
            from_location_id=document.src_location_id,
            to_location_id=document.dest_location_id,
            qty=qty,
            done_at=datetime.now(UTC)
        )
        moves.append(move)
    
    db.add_all(moves)
    db.commit()
    return moves
```

### Output Files
```
backend/app/api/routes/
  ├─ documents.py (new)
  ├─ stock_moves.py (new)
  └─ receipts.py (new, optional if within documents)

backend/app/models/
  └─ operations.py (enhance with validation methods)

backend/app/schemas/
  ├─ documents.py (new)
  ├─ operations.py (new)
  └─ stock_moves.py (new)

backend/app/services/
  └─ document_service.py (new, validation & workflow logic)
```

### Dependencies
- Depends on: Auth/Guard Agent, Inventory Agent
- Required by: UI Agent

---

## Dependency Graph

```
Auth/Guard Agent
  └─ (No dependencies)

Inventory Agent
  └─ Depends on: Auth/Guard Agent

Operations Agent
  ├─ Depends on: Auth/Guard Agent
  └─ Depends on: Inventory Agent

UI Agent
  ├─ Depends on: Auth/Guard Agent
  ├─ Depends on: Inventory Agent
  └─ Depends on: Operations Agent
```

**Development Order**:
1. ✅ **Auth/Guard Agent** (foundation)
2. **Inventory Agent** (products & warehouses needed for operations)
3. **Operations Agent** (documents depend on products)
4. **UI Agent** (consumes all backend APIs)

---

## Cross-Agent Communication

### Data Contracts (JSON)

**Product Response**
```json
{
  "id": 1,
  "name": "Steel Rod",
  "sku": "STEEL-001",
  "category_id": 5,
  "uom": "kg",
  "reorder_point": 20,
  "reorder_qty": 100,
  "is_active": true
}
```

**Document Response**
```json
{
  "id": 1,
  "reference": "WH1/IN/0001",
  "doc_type": "receipt",
  "status": "done",
  "partner_name": "Steel Corp",
  "src_location_id": 3,
  "dest_location_id": 1,
  "lines": [
    {
      "id": 1,
      "product_id": 1,
      "qty_demand": 100,
      "qty_done": 100
    }
  ],
  "validated_at": "2026-01-15T10:30:00Z",
  "created_by": 1
}
```

**StockMove Response**
```json
{
  "id": 1,
  "document_id": 1,
  "product_id": 1,
  "from_location_id": 3,
  "to_location_id": 1,
  "qty": 100,
  "done_at": "2026-01-15T10:30:00Z"
}
```

---

## Testing Strategy

### Auth/Guard Agent Tests
- User signup validation
- Password hashing verification
- JWT token creation & validation
- OTP generation & consumption
- Login with correct/incorrect credentials

### Inventory Agent Tests
- Product CRUD operations
- Category hierarchy
- Warehouse/location creation
- Stock calculation from moves
- Low-stock detection

### Operations Agent Tests
- Document creation & validation
- Stock move creation
- Status transitions
- Document line management
- Stock move ledger queries

### UI Agent Tests
- Component rendering
- Form validation & submission
- API integration (mocked)
- Navigation & routing
- Authentication flow

---

## Handoff Checklist

### When Auth/Guard Agent Completes:
- [ ] All auth endpoints tested
- [ ] JWT token generation working
- [ ] OTP service functional
- [ ] Dependency injection guards implemented
- [ ] Frontend auth context integrated
- [ ] API docs updated

### When Inventory Agent Completes:
- [ ] Product API endpoints functional
- [ ] Category API endpoints functional
- [ ] Warehouse/location API endpoints functional
- [ ] Stock queries returning correct values
- [ ] Low-stock logic validated
- [ ] Database relationships verified

### When Operations Agent Completes:
- [ ] Document CRUD endpoints functional
- [ ] Validation logic tested
- [ ] Stock moves created correctly
- [ ] Status transitions working
- [ ] Stock ledger append-only verified
- [ ] Move history queries functional

### When UI Agent Completes:
- [ ] All pages rendering
- [ ] Forms submitting correctly
- [ ] Data fetching with React Query
- [ ] Error handling & loading states
- [ ] Responsive design on mobile/tablet
- [ ] Accessibility compliance (WCAG)

---

## Success Criteria

✅ **All endpoints documented** in FastAPI Swagger (`/docs`)
✅ **All flows tested** (happy path + error cases)
✅ **No breaking changes** between agents (semver versioning)
✅ **Zero data loss** in append-only ledger
✅ **All status codes correct** (201 for creation, 400 for validation, etc.)
✅ **All timestamps UTC** with timezone awareness
✅ **All responses have consistent structure**

---

**Last Updated**: 2026-09-26
**Project**: StockSense Inventory Management System
**Team**: 4 Specialized Agents
