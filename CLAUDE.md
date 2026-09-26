# StockSense - CLAUDE.md

## Project Overview

**StockSense** is a modular Inventory Management System (IMS) that digitalizes and streamlines all stock-related operations within a business. It replaces manual registers, Excel sheets, and scattered tracking methods with a centralized, real-time, easy-to-use app.

### Core Philosophy

The system uses an **append-only stock ledger** (`stock_moves` table) as the single source of truth. Every operation (Receipt, Delivery, Internal Transfer, Adjustment) appends rows to this ledger. On-hand stock is **derived** by summing the ledger, ensuring numbers never drift apart.

| Operation | Move | Effect on Total Stock |
|-----------|------|----------------------|
| Receipt | Vendors (virtual) → warehouse | Increases |
| Delivery | warehouse → Customers (virtual) | Decreases |
| Internal Transfer | location → location | Unchanged (location changes) |
| Adjustment | Inventory Adjustment (virtual) ↔ location | ± counted difference |

---

## Architecture

### Tech Stack

**Frontend:**
- React 18 + TypeScript
- Vite (build tool)
- React Router v6 (routing)
- React Query v5 (data fetching)
- Tailwind CSS (styling)
- Lucide React (icons)

**Backend:**
- FastAPI (async Python web framework)
- SQLAlchemy 2.0 (ORM)
- Alembic (database migrations)
- PostgreSQL or SQLite (database)
- PyJWT + bcrypt (authentication & security)

**Infrastructure:**
- Docker Compose (PostgreSQL setup, optional)
- Uvicorn (ASGI server)

---

## Database Schema

### User Management

**Table: `users`**
- `id` (PK): Integer
- `name`: String(120)
- `email`: String(255) - unique, indexed
- `password_hash`: String(255) - bcrypt hash
- `role`: String(20) - 'manager' or 'staff'
- `is_active`: Boolean
- `created_at`, `updated_at`: Timestamps

**Table: `otp_tokens`**
- `id` (PK): Integer
- `user_id` (FK): Foreign key to users
- `code_hash`: String(255) - hashed 6-digit code
- `purpose`: String(40) - 'password_reset'
- `expires_at`: DateTime
- `used_at`: DateTime (NULL if unused)
- `created_at`, `updated_at`: Timestamps

### Inventory & Stock

**Table: `warehouses`**
- `id` (PK): Integer
- `name`: String(120)
- `code`: String(20) - unique warehouse code
- `address`: String(255)
- `created_at`, `updated_at`: Timestamps

**Table: `locations`**
- `id` (PK): Integer
- `warehouse_id` (FK): Optional (NULL for virtual locations)
- `name`: String(120)
- `code`: String(40) - unique location code
- `type`: String(20) - 'internal', 'vendor', 'customer', 'adjustment', 'scrap'
- `parent_id` (FK): Optional (for hierarchical locations)
- `created_at`, `updated_at`: Timestamps
- Virtual locations (vendor, customer, adjustment, scrap) have no warehouse

**Table: `categories`**
- `id` (PK): Integer
- `name`: String(120) - unique
- `parent_id` (FK): Optional (hierarchical categories)
- `created_at`, `updated_at`: Timestamps

**Table: `products`**
- `id` (PK): Integer
- `name`: String(180) - indexed
- `sku`: String(60) - unique, indexed
- `category_id` (FK): Optional
- `uom`: String(20) - Unit of Measure (e.g., 'kg', 'Unit')
- `barcode`: String(60) - optional
- `reorder_point`: Numeric(14,3) - stock level threshold for alerts
- `reorder_qty`: Numeric(14,3) - quantity to reorder when low
- `is_active`: Boolean
- `created_at`, `updated_at`: Timestamps

### Operations & Stock Ledger

**Table: `documents`**
- `id` (PK): Integer
- `reference`: String(40) - unique (e.g., 'WH1/IN/0001')
- `doc_type`: String(20) - 'receipt', 'delivery', 'internal', 'adjustment'
- `status`: String(20) - 'draft', 'waiting', 'ready', 'done', 'canceled'
- `partner_name`: String(180) - supplier/customer name
- `src_location_id` (FK): From location
- `dest_location_id` (FK): To location
- `scheduled_at`: DateTime
- `validated_at`: DateTime
- `created_by` (FK): User who created it
- `note`: Text
- `created_at`, `updated_at`: Timestamps

**Table: `document_lines`**
- `id` (PK): Integer
- `document_id` (FK): Parent document
- `product_id` (FK): Product
- `qty_demand`: Numeric(14,3) - requested quantity
- `qty_done`: Numeric(14,3) - actually moved/received

**Table: `stock_moves`** (Append-only ledger)
- `id` (PK): Integer
- `document_id` (FK): Originating document (nullable)
- `product_id` (FK): Product moved
- `from_location_id` (FK): Source location
- `to_location_id` (FK): Destination location
- `qty`: Numeric(14,3) - quantity moved (positive)
- `done_at`: DateTime - when the move was recorded
- **Never updated or deleted** — mistakes corrected by adding opposite moves

---

## API Routes

### Authentication Endpoints

**POST `/auth/signup`**
- Create a new user account
- Request: `SignupIn` (name, email, password, role)
- Response: `UserOut` (id, name, email, role)
- Validates: email uniqueness, password strength (8-128 chars), role validity

**POST `/auth/login`**
- Authenticate and get access token
- Request: `LoginIn` (email, password)
- Response: `TokenOut` (access_token, token_type, user)
- Returns: JWT bearer token + user info

**GET `/auth/me`**
- Get current authenticated user
- Required: Bearer token
- Response: `UserOut`

**POST `/auth/forgot-password`**
- Initiate password reset
- Request: `ForgotPasswordIn` (email)
- Response: `ForgotPasswordOut` (message, otp)
- Dev mode: returns OTP; prod: sends via email (not implemented)

**POST `/auth/verify-otp`**
- Verify OTP code
- Request: `VerifyOtpIn` (email, otp)
- Response: `VerifyOtpOut` (reset_token)
- Returns: Short-lived reset token

**POST `/auth/reset-password`**
- Update password with reset token
- Request: `ResetPasswordIn` (reset_token, new_password)
- Response: `MessageOut` (message)

**GET `/health`**
- Health check endpoint
- Response: `{"status": "ok", "service": "StockSense API"}`

### Inventory Endpoints (manager-only writes, any authenticated user can read)

- `GET/POST /categories`, `PUT/DELETE /categories/{id}`
- `GET/POST /warehouses`, `GET/PUT/DELETE /warehouses/{id}`, `GET /warehouses/{id}/locations`
- `GET/POST /locations` (filter by `warehouse_id`, `type`), `GET/PUT/DELETE /locations/{id}`
- `GET/POST /products` (filter by `category_id`, `is_active`, `low_stock`, `search`), `GET/PUT/DELETE /products/{id}`
- `GET /products/{id}/stock` — on-hand quantity broken down per physical location

Product creation accepts optional `initial_stock` + `initial_stock_location_id`, recorded as a stock move from the Inventory Adjustment virtual location.

### Operations Endpoints (any authenticated user — managers and staff both perform operations)

- `GET/POST /documents` (filter by `doc_type`, `status`, `warehouse_id`, `location_id`) — one endpoint for receipts, deliveries, internal transfers and adjustments, distinguished by `doc_type`
- `GET/PUT/DELETE /documents/{id}` (edit/delete only while still Draft/Waiting)
- `POST /documents/{id}/validate` — turns the document's lines into `stock_moves` and marks it Done
- `POST /documents/{id}/cancel`
- `GET /stock-moves` (filter by `product_id`, `location_id`, `document_id`, `from_date`, `to_date`) — Move History
- `GET /dashboard/summary` — the KPI tiles (total in stock, low/out-of-stock, pending receipts/deliveries/transfers/adjustments)

See `app/services/documents.py` for the per-doc_type location-type rules (e.g. a receipt's source must be a Vendor location, its destination a physical one) and how adjustment lines compare counted vs. on-hand quantity to decide move direction.

---

## Frontend Structure

### Pages

- **Login** (`/login`): Authentication entry point
- **Signup** (`/signup`): User registration
- **ForgotPassword** (`/forgot-password`): Password reset flow
- **Dashboard** (`/dashboard`): KPI snapshot & pending operations
- **Products** (`/products`): Product CRUD & stock availability
- **Receipts** (`/receipts`): Incoming goods from vendors
- **Deliveries** (`/deliveries`): Outgoing goods to customers
- **Transfers** (`/transfers`): Internal stock movements
- **Adjustments** (`/adjustments`): Inventory corrections
- **MoveHistory** (`/moves`): Stock ledger view
- **SettingsWarehouses** (`/settings/warehouses`): Warehouse & location config
- **Profile** (`/profile`): User profile & settings

### Key Components

- **AppLayout**: Protected layout wrapper with sidebar
- **Sidebar**: Navigation menu with profile & logout
- **PageHeader**: Page title & breadcrumbs
- **StatusBadge**: Status indicator component
- **Placeholder**: Stub component for in-progress pages
- **AuthContext**: React context for auth state & token management

### Authentication Flow

1. User navigates to `/login`
2. Credentials sent to `/auth/login`
3. JWT token stored in context
4. Token added to all subsequent API requests
5. Protected routes wrapped with `RequireAuth`
6. Redirect to `/login` if token invalid/missing

---

## Authentication & Security

### Password Hashing
- Uses **bcrypt** with automatic salt generation
- Passwords: 8-128 characters
- Hash verification on login

### JWT Tokens
- Algorithm: **HS256**
- Access tokens: 720 minutes (12 hours) by default
- Reset tokens: 10 minutes (OTP expiry time)
- Token payload: `{sub: user_id, exp, iat, type}`

### OTP (One-Time Password)
- **Purpose**: Password reset verification
- **Format**: 6-digit code
- **Expiry**: 10 minutes
- **Storage**: Hashed in DB
- **Dev mode**: Printed to console; prod: would email

### User Roles
- **Manager**: Full access to all operations
- **Staff**: Warehouse operations (details in future guards)

---

## Key Implementation Details

### Ledger-Based Inventory

All stock quantities are **derived** from `stock_moves`:

```sql
SELECT 
  product_id,
  to_location_id,
  SUM(qty) as on_hand
FROM stock_moves
GROUP BY product_id, to_location_id
```

**Advantages:**
- Complete audit trail
- Numbers never drift
- No manual reconciliation needed
- Mistakes corrected by reversing entries

### Document Workflow

1. **Draft** → Create document with lines, no stock change
2. **Waiting** → Ready for fulfillment
3. **Ready** → Picked/packed, awaiting validation
4. **Done** → Validated, `stock_moves` created
5. **Canceled** → Document voided

### Location Types

- **Internal**: Real warehouse/shelf location
- **Vendor**: Virtual (source of receipts)
- **Customer**: Virtual (destination of deliveries)
- **Adjustment**: Virtual (inventory corrections)
- **Scrap**: Virtual (write-offs/damaged goods)

---

## Development Setup

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env

# SQLite (default)
alembic upgrade head
python -m app.seed

# Or with Postgres
docker compose up -d db
# Set DATABASE_URL in .env
alembic upgrade head
python -m app.seed

uvicorn app.main:app --reload
# API docs: http://localhost:8000/docs
```

**Demo Accounts** (seeded):
- `manager@stocksense.app` / `manager123`
- `staff@stocksense.app` / `staff123`

### Frontend

```bash
cd frontend
npm install
npm run dev
# http://localhost:5173
```

**Environment:**
- `VITE_API_URL`: API endpoint (default: `http://localhost:8000`)

---

## Testing

### Backend Tests

```bash
cd backend
pytest tests/
pytest tests/test_auth.py -v
```

Tests use SQLite in-memory database for isolation.

---

## Multi-Agent Development Strategy

This project is designed for **4 specialized agents**:

### 1. **UI Agent** (Frontend)
- Owns: React components, pages, routing, styling
- Responsibilities:
  - Dashboard KPIs layout
  - Forms for products, receipts, deliveries, transfers, adjustments
  - Dynamic filters (doc type, status, warehouse)
  - Stock tables with real-time updates
  - Settings & profile pages
- Tools: Vite, React Router, React Query, Tailwind CSS

### 2. **Auth/Guard Agent** (Authentication & Authorization)
- Owns: Auth endpoints, guards, role-based access
- Responsibilities:
  - Auth flow (signup, login, forgot-password, OTP, reset)
  - JWT token generation & validation
  - OTP service & email integration
  - Role-based middleware guards
  - Protected route configuration
- Files:
  - `backend/app/api/routes/auth.py`
  - `backend/app/core/security.py`
  - `backend/app/services/otp.py`
  - `backend/app/api/deps.py`
  - `frontend/src/auth/AuthContext.tsx`

### 3. **Inventory Backend Agent** (Products & Stock)
- Owns: Product management, categories, warehouses, locations
- Responsibilities:
  - Product CRUD with SKU, UOM, reorder rules
  - Category management (hierarchical)
  - Warehouse & location setup
  - Stock availability queries
  - Low-stock alerts
- Files:
  - `backend/app/models/inventory.py`
  - Backend API routes for products, warehouses, locations

### 4. **Operations Backend Agent** (Documents & Stock Ledger)
- Owns: Receipts, Deliveries, Transfers, Adjustments, Stock Ledger
- Responsibilities:
  - Document CRUD (create, update, validate)
  - Document line management
  - Stock move ledger creation
  - Move history & audit trail
  - Inventory adjustments
- Files:
  - `backend/app/models/operations.py`
  - Backend API routes for documents & stock moves
  - Document workflow & validation logic

---

## Important Patterns

### Dependency Injection (FastAPI)
```python
from app.api.deps import get_current_user
from app.db.session import get_db

@router.post("/example")
def example(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    pass
```

### Database Session
- Automatically created per request
- Committed after successful response
- Rolled back on exception

### Error Handling
- HTTPException for user-facing errors
- Consistent status codes (401, 403, 404, 409, 422)
- Never expose internal error details

### Email (Not Yet Implemented)
- OTP sending configured in `ForgotPasswordOut`
- Dev mode: prints to console
- Prod: needs SMTP config in settings

---

## Configuration Reference

### Environment Variables (`.env`)

```env
DATABASE_URL=postgresql+psycopg2://stocksense:stocksense@localhost:5432/stocksense
SECRET_KEY=change-me-before-demo
ACCESS_TOKEN_EXPIRE_MINUTES=720
OTP_EXPIRE_MINUTES=10
DEV_SHOW_OTP=true
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### Alembic Migrations

Migrations in `backend/alembic/versions/`:
- `ea16feff0e85_initial_schema.py`: Full schema setup

To create new migration:
```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

---

## Current Status

- ✅ Backend scaffolding complete
- ✅ Auth system with JWT + OTP
- ✅ Database schema & migrations
- ✅ Role-based guards (`get_current_manager` in `app/api/deps.py`)
- ✅ Inventory API: products, categories, warehouses, locations (`app/api/routes/`)
- ✅ Operations API: documents (receipts/deliveries/transfers/adjustments), stock moves, dashboard
- ✅ Stock-on-hand service derived from the `stock_moves` ledger (`app/services/stock.py`)
- ✅ Demo data seeding
- ✅ Backend test suite: 36 tests passing (auth, inventory, operations)
- 🚧 Frontend pages (placeholders — UI Agent's turn next)
- 🚧 Email integration for OTP (dev mode prints/returns the code instead)

---

## Next Steps (Prioritized)

1. ✅ ~~**Auth/Guard Agent**: Complete auth guards & role-based middleware~~
2. ✅ ~~**Inventory Agent**: Implement product & warehouse API routes~~
3. ✅ ~~**Operations Agent**: Implement document & stock move logic~~
4. **UI Agent**: Build and integrate frontend pages against the now-complete API
5. **Testing**: Frontend test coverage (backend already at 36 passing tests)
6. **Email**: SMTP setup for OTP in production

See `AGENTS.md` for the full endpoint list each agent owns.

---

## Links & References

- **Mockup**: https://link.excalidraw.com/l/65VNwvy7c4X/3ENvQFu9o8R
- **FastAPI Docs**: http://localhost:8000/docs (when running)
- **Vite Docs**: https://vitejs.dev
- **React Query**: https://tanstack.com/query/latest
- **SQLAlchemy 2.0**: https://docs.sqlalchemy.org

---

**Last Updated**: 2026-09-26  
**Repository**: StockSense (Hackathon Project)  
**Team**: Multi-agent development with specialized agents for UI, Auth, Inventory, and Operations
