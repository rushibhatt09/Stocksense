# StockSense - Agent Onboarding Guide

Welcome to the StockSense Inventory Management System! This guide helps each agent get started.

---

## Quick Start

### Prerequisites

- **Git**: Clone the repository
- **Backend**: Python 3.10+, pip
- **Frontend**: Node.js 18+, npm
- **Database**: SQLite (built-in) or PostgreSQL (optional, via Docker)

### Setup (Shared by All Agents)

```bash
# Clone repo
git clone <repo-url>
cd Stocksense

# Backend setup
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # Use defaults (SQLite)
alembic upgrade head               # Run migrations
python -m app.seed                 # Seed demo data

# In a separate terminal, start API
uvicorn app.main:app --reload
# API available at http://localhost:8000
# Swagger docs at http://localhost:8000/docs

# Frontend setup
cd ../frontend
npm install
npm run dev
# Frontend available at http://localhost:5173
```

### Demo Accounts

Use these accounts in the dev environment:

| Email | Password | Role |
|-------|----------|------|
| `manager@stocksense.app` | `manager123` | Manager (full access) |
| `staff@stocksense.app` | `staff123` | Staff (limited access) |

---

## Agent 1: UI Agent - Getting Started

### Your Goal
Build React components and pages that consume backend APIs and provide an excellent user experience.

### Essential Files to Read First

1. **Project Overview**
   - `PROJECT.md` – Features & user flows
   - `CLAUDE.md` – Architecture & tech stack

2. **Agent Responsibilities**
   - `AGENTS.md` → **Agent 1: UI Agent** section

3. **Current Frontend Structure**
   - `frontend/src/App.tsx` – Routing & pages
   - `frontend/src/auth/AuthContext.tsx` – Auth state management
   - `frontend/src/lib/api.ts` – API client setup
   - `frontend/src/components/AppLayout.tsx` – Main layout wrapper
   - `frontend/src/pages/Dashboard.tsx` – Example page (stub)

### Your First Task

1. **Understand the Auth Flow**
   ```bash
   cd frontend
   npm run dev
   # Open http://localhost:5173/login
   # Test login with manager@stocksense.app / manager123
   ```

2. **Enhance the Dashboard Page**
   - Read: `AGENTS.md` → "UI Agent → Responsibilities → Dashboard"
   - Read: `PROJECT.md` → "Dashboard (Landing Page)"
   - Build KPI cards for: Total Products, Low Stock Items, Pending Operations
   - Add dynamic filters
   - Use React Query to fetch data from `/documents` (when Operations Agent completes)

3. **Build a Reusable Component Library**
   - DataTable component for displaying lists
   - Modal/Dialog for CRUD forms
   - KPI Card component
   - Status Badge component
   - Form fields (Input, Select, DateInput, TextArea)

### Tech Resources

- **React Router**: https://reactrouter.com/en/main
- **React Query**: https://tanstack.com/query/latest
- **Tailwind CSS**: https://tailwindcss.com
- **TypeScript**: https://www.typescriptlang.org/docs/

### API Integration Pattern

```typescript
// In your page component
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export default function Products() {
  const { data: products, isLoading, error } = useQuery({
    queryKey: ["products"],
    queryFn: () => api.get("/products"),
  });

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      {products?.map((product) => (
        <div key={product.id}>{product.name}</div>
      ))}
    </div>
  );
}
```

### Expected API Endpoints (Built by Other Agents)

You'll consume these APIs:

- Auth: `/auth/login`, `/auth/signup`, `/auth/me`, `/auth/forgot-password`
- Products: `GET /products`, `POST /products`, `PUT /products/{id}`, etc.
- Warehouses: `GET /warehouses`, `POST /warehouses`, etc.
- Locations: `GET /locations`, `POST /locations`, etc.
- Documents: `GET /documents`, `POST /documents`, `POST /documents/{id}/validate`, etc.
- Stock Moves: `GET /stock-moves`, etc.

**Note**: These endpoints will be added incrementally by other agents. UI pages can render once the API is ready.

### Checklist

- [ ] Backend running with `uvicorn app.main:app --reload`
- [ ] Frontend running with `npm run dev`
- [ ] Can login with demo credentials
- [ ] Understand React Query & how to fetch data
- [ ] Build DataTable component
- [ ] Build KPI Card component
- [ ] Build Modal component
- [ ] Build first page (Dashboard with placeholder KPIs)

---

## Agent 2: Auth/Guard Agent - Getting Started

### Your Goal
Implement authentication endpoints, guards, middleware, and OTP service. This is the foundation for other agents.

### Essential Files to Read First

1. **Project Overview**
   - `CLAUDE.md` → "Authentication & Security" section
   - `CLAUDE.md` → "API Routes → Authentication Endpoints"

2. **Agent Responsibilities**
   - `AGENTS.md` → **Agent 2: Auth/Guard Agent** section

3. **Existing Code to Understand**
   - `backend/app/api/routes/auth.py` – Routes (mostly complete)
   - `backend/app/core/security.py` – JWT & password hashing (complete)
   - `backend/app/services/otp.py` – OTP generation (complete)
   - `backend/app/api/deps.py` – Dependency injection
   - `backend/app/models/user.py` – User & OTP models (complete)

### Your First Task

1. **Test Existing Auth Endpoints**
   ```bash
   # Start backend
   cd backend
   uvicorn app.main:app --reload
   
   # Visit http://localhost:8000/docs
   # Try signup, login, forgot-password, verify-otp flows
   ```

2. **Add Manager/Staff Guard Decorators**
   - Extend `backend/app/api/deps.py`
   - Create `get_current_manager()` and `get_current_staff()`
   - Use in routes like: `@router.get("/admin") def admin_only(current_user: User = Depends(get_current_manager)):`

3. **Enhance OTP Service for Email** (Optional for Now)
   - Currently prints OTP to console (dev-friendly)
   - Later: Integrate with SMTP (SendGrid, AWS SES)
   - Config in `backend/app/core/config.py`

4. **Add Rate Limiting** (Future Enhancement)
   - Prevent brute force on login
   - Prevent OTP spam

### Key Code Patterns

**Add a Guard to a Route**
```python
from fastapi import Depends
from app.api.deps import get_current_user, get_current_manager
from app.models.user import User

@router.post("/protected")
def protected_endpoint(current_user: User = Depends(get_current_manager)):
    return {"user": current_user.name}
```

**Using get_db and get_current_user Together**
```python
@router.post("/example")
def example(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # current_user is already authenticated
    # db is database session
    user = db.get(User, current_user.id)
    return user
```

### Provided Utilities

**Password Hashing**
```python
from app.core.security import hash_password, verify_password

hashed = hash_password("mypassword")
is_valid = verify_password("mypassword", hashed)
```

**JWT Token Generation**
```python
from app.core.security import create_access_token, decode_token

token = create_access_token(user_id=1)
claims = decode_token(token, expected_type="access")
print(claims["sub"])  # "1"
```

### Testing

```bash
# Run auth tests
cd backend
pytest tests/test_auth.py -v

# Add new tests for guards
pytest tests/ -v
```

### Checklist

- [ ] Understand existing auth code
- [ ] Test all auth endpoints via Swagger
- [ ] Create `get_current_manager()` guard
- [ ] Create `get_current_staff()` guard
- [ ] Test guards work (try protecting an endpoint)
- [ ] OTP prints to console in dev mode
- [ ] Frontend login/logout works
- [ ] Token is stored in AuthContext

---

## Agent 3: Inventory Agent - Getting Started

### Your Goal
Implement Product, Category, Warehouse, and Location API endpoints. These are dependencies for Operations Agent.

### Essential Files to Read First

1. **Project Overview**
   - `CLAUDE.md` → "Database Schema → Inventory & Stock"
   - `PROJECT.md` → "Product Management" & "Settings → Warehouse Management"

2. **Agent Responsibilities**
   - `AGENTS.md` → **Agent 3: Inventory Agent** section

3. **Existing Models**
   - `backend/app/models/inventory.py` – Product, Category, Warehouse, Location models

### Your First Task

1. **Create Pydantic Schemas**
   - Create `backend/app/schemas/products.py`
   - Create `backend/app/schemas/warehouses.py`
   - Create `backend/app/schemas/locations.py`

   Example:
   ```python
   # backend/app/schemas/products.py
   from pydantic import BaseModel

   class ProductIn(BaseModel):
       name: str
       sku: str
       category_id: int | None = None
       uom: str = "Unit"
       reorder_point: float = 0
       reorder_qty: float = 0

   class ProductOut(BaseModel):
       id: int
       name: str
       sku: str
       ...
       
       class Config:
           from_attributes = True
   ```

2. **Create API Routes**
   - Create `backend/app/api/routes/products.py`
   - Create `backend/app/api/routes/warehouses.py`
   - Create `backend/app/api/routes/locations.py`

   Example:
   ```python
   # backend/app/api/routes/products.py
   from fastapi import APIRouter, Depends
   from sqlalchemy.orm import Session
   from app.db.session import get_db
   from app.api.deps import get_current_user
   from app.models.user import User
   from app.models.inventory import Product
   from app.schemas.products import ProductIn, ProductOut

   router = APIRouter(prefix="/products", tags=["products"])

   @router.get("/", response_model=list[ProductOut])
   def list_products(db: Session = Depends(get_db)):
       return db.query(Product).all()

   @router.post("/", response_model=ProductOut, status_code=201)
   def create_product(payload: ProductIn, db: Session = Depends(get_db)):
       product = Product(**payload.model_dump())
       db.add(product)
       db.commit()
       db.refresh(product)
       return product

   @router.get("/{id}", response_model=ProductOut)
   def get_product(id: int, db: Session = Depends(get_db)):
       product = db.get(Product, id)
       if not product:
           raise HTTPException(status_code=404, detail="Not found")
       return product
   ```

3. **Register Routes in Main App**
   - Edit `backend/app/main.py`
   - Include routers:
   ```python
   from app.api.routes import products, warehouses, locations

   app.include_router(products.router)
   app.include_router(warehouses.router)
   app.include_router(locations.router)
   ```

4. **Implement Stock Query**
   - Add method to Product model:
   ```python
   def get_on_hand(self, location_id: int, db: Session) -> float:
       """Get on-hand quantity at a location."""
       # Sum all stock_moves for this product at this location
       # Implementation details in AGENTS.md
   ```

### Key Business Logic

**Stock Calculation**
```python
from sqlalchemy import func
from app.models.operations import StockMove

def get_on_hand(product_id: int, location_id: int, db: Session) -> float:
    """Get on-hand stock for a product at a location."""
    incoming = db.query(func.sum(StockMove.qty)).filter(
        StockMove.product_id == product_id,
        StockMove.to_location_id == location_id
    ).scalar() or 0
    
    outgoing = db.query(func.sum(StockMove.qty)).filter(
        StockMove.product_id == product_id,
        StockMove.from_location_id == location_id
    ).scalar() or 0
    
    return incoming - outgoing
```

**Low Stock Detection**
```python
def is_low_stock(product: Product, location_id: int, db: Session) -> bool:
    on_hand = get_on_hand(product.id, location_id, db)
    return on_hand <= product.reorder_point
```

### Testing

```bash
# Test endpoints via Swagger
cd backend
uvicorn app.main:app --reload
# Visit http://localhost:8000/docs

# Or write tests
pytest tests/test_products.py -v
```

### Checklist

- [ ] Create Pydantic schemas for Product, Warehouse, Location, Category
- [ ] Create API routes for each entity
- [ ] Register routes in `app/main.py`
- [ ] Test all CRUD endpoints via Swagger
- [ ] Implement stock calculation method
- [ ] Test low-stock detection
- [ ] Add proper error handling (404, 409 for duplicates)
- [ ] All endpoints documented in Swagger

---

## Agent 4: Operations Agent - Getting Started

### Your Goal
Implement Document, DocumentLine, and StockMove endpoints. This is the core business logic.

### Essential Files to Read First

1. **Project Overview**
   - `PROJECT.md` → "Core Operations" (Receipts, Deliveries, Transfers, Adjustments)
   - `CLAUDE.md` → "Database Schema → Operations & Stock Ledger"
   - `CLAUDE.md` → "The core idea" section

2. **Agent Responsibilities**
   - `AGENTS.md` → **Agent 4: Operations Agent** section

3. **Existing Models**
   - `backend/app/models/operations.py` – Document, DocumentLine, StockMove models

### Your First Task

1. **Understand the Ledger Pattern**
   - Read `CLAUDE.md` → "Important Patterns → Ledger-Based Inventory"
   - Read `PROJECT.md` → "Example Flow: End-to-End"
   - StockMove is **append-only** (never updated/deleted)
   - All stock quantities are **derived** from stock_moves

2. **Create Document Schemas**
   - Create `backend/app/schemas/documents.py`
   - Create `backend/app/schemas/operations.py`

   ```python
   # backend/app/schemas/documents.py
   from datetime import datetime
   from pydantic import BaseModel

   class DocumentLineIn(BaseModel):
       product_id: int
       qty_demand: float

   class DocumentIn(BaseModel):
       doc_type: str  # "receipt", "delivery", "internal", "adjustment"
       partner_name: str | None
       src_location_id: int
       dest_location_id: int
       lines: list[DocumentLineIn]
       scheduled_at: datetime | None = None

   class DocumentOut(BaseModel):
       id: int
       reference: str
       doc_type: str
       status: str
       partner_name: str | None
       lines: list[DocumentLineOut]
       ...
   ```

3. **Create Document Routes**
   - Create `backend/app/api/routes/documents.py`

   ```python
   @router.post("/documents", response_model=DocumentOut, status_code=201)
   def create_document(
       payload: DocumentIn,
       current_user: User = Depends(get_current_user),
       db: Session = Depends(get_db)
   ):
       # Create document with lines
       # Generate reference number (e.g., WH1/IN/0001)
       # Set status to "draft"
       # Return document
   ```

4. **Implement Validation Logic**
   - Create `backend/app/services/document_service.py`
   - Implement `validate_receipt()`, `validate_delivery()`, etc.
   - Generate stock_moves on validation

   ```python
   def validate_document(document: Document, db: Session) -> list[StockMove]:
       """
       Validate document and create stock moves.
       Raises HTTPException on validation failure.
       """
       # Validate based on doc_type
       if document.doc_type == "receipt":
           # Check: supplier, lines, qty > 0, destination is internal
           # Create moves from vendor to destination
       elif document.doc_type == "delivery":
           # Check: customer, lines, qty > 0, source is internal, stock available
           # Create moves from source to customer
       # ... etc
       
       moves = create_stock_moves(document, db)
       document.status = "done"
       document.validated_at = datetime.now(UTC)
       db.commit()
       return moves
   ```

5. **Create Stock Move Routes**
   - Create `backend/app/api/routes/stock_moves.py`

   ```python
   @router.get("/stock-moves", response_model=list[StockMoveOut])
   def list_stock_moves(
       product_id: int | None = None,
       location_id: int | None = None,
       db: Session = Depends(get_db)
   ):
       query = db.query(StockMove)
       if product_id:
           query = query.filter(StockMove.product_id == product_id)
       if location_id:
           query = query.filter(
               (StockMove.from_location_id == location_id) |
               (StockMove.to_location_id == location_id)
           )
       return query.order_by(StockMove.done_at.desc()).all()
   ```

### Key Business Logic

**Reference Number Generation**
```python
def generate_reference(doc_type: str, warehouse_id: int, db: Session) -> str:
    """Generate unique reference like WH1/IN/0001"""
    from app.models.enums import DocType
    
    prefix = DocType.PREFIX[doc_type]
    warehouse = db.get(Warehouse, warehouse_id)
    
    last_doc = db.query(Document).filter(
        Document.doc_type == doc_type,
        Document.src_location_id.in_(
            db.query(Location.id).filter(Location.warehouse_id == warehouse_id)
        )
    ).order_by(Document.id.desc()).first()
    
    sequence = (last_doc.id % 10000) + 1 if last_doc else 1
    return f"{warehouse.code}/{prefix}/{sequence:04d}"
```

**Stock Move Creation**
```python
def create_stock_moves(document: Document, db: Session) -> list[StockMove]:
    """Create append-only stock moves from document lines."""
    from datetime import UTC, datetime
    
    moves = []
    for line in document.lines:
        qty = line.qty_done if line.qty_done > 0 else line.qty_demand
        
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
    db.flush()  # Generate IDs without committing yet
    return moves
```

### Testing

```bash
# Test endpoints
cd backend
uvicorn app.main:app --reload
# Visit http://localhost:8000/docs

# Test flows:
# 1. Create receipt → validate → check stock_moves created
# 2. Create delivery → validate → check stock decreased
# 3. Create transfer → validate → check location changed
# 4. Create adjustment → validate → check ledger balanced
```

### Checklist

- [ ] Understand append-only ledger pattern
- [ ] Create document schemas
- [ ] Create document CRUD routes
- [ ] Implement reference number generation
- [ ] Create validation service
- [ ] Implement stock move creation
- [ ] Create stock move list endpoint
- [ ] Test all document workflows via Swagger
- [ ] Test ledger is balanced (sum of moves = 0)
- [ ] Test moves are append-only (cannot edit/delete)

---

## Common Tasks & Patterns

### How to Handle Errors

```python
from fastapi import HTTPException, status

# 400 Bad Request
raise HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Invalid quantity"
)

# 401 Unauthorized (Auth required)
# Automatically handled by get_current_user

# 403 Forbidden (Not allowed)
raise HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="You don't have permission"
)

# 404 Not Found
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Product not found"
)

# 409 Conflict (Duplicate)
raise HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Product with this SKU already exists"
)
```

### How to Add Timestamps

```python
from datetime import UTC, datetime

# In a route
created_at = datetime.now(UTC)

# In a model (if using TimestampMixin)
# Already has created_at and updated_at
```

### How to Make a DB Query

```python
from sqlalchemy import select
from app.db.session import get_db

# Simple get by ID
product = db.get(Product, 1)

# Query with filter
product = db.query(Product).filter(Product.sku == "ABC-123").first()

# Using select (modern SQLAlchemy 2.0)
stmt = select(Product).where(Product.sku == "ABC-123")
product = db.scalar(stmt)

# Query multiple
products = db.query(Product).filter(Product.is_active == True).all()
```

### How to Add a Relationship Query

```python
# Get a product with its category
product = db.query(Product).filter(Product.id == 1).first()
print(product.category.name)  # Accesses relationship

# Get a category with all products
category = db.query(Category).filter(Category.id == 1).first()
for product in category.products:
    print(product.name)
```

---

## Useful Commands

```bash
# Backend

# Run migrations
cd backend
alembic upgrade head

# Create new migration (after changing models)
alembic revision --autogenerate -m "add_new_field"
alembic upgrade head

# Run tests
pytest tests/ -v
pytest tests/test_auth.py -v

# Start API with auto-reload
uvicorn app.main:app --reload

# Check code style
black app/
flake8 app/

# Frontend

cd frontend

# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Format code
npm run format
```

---

## Important Notes

### Database Transactions

Always wrap multiple DB operations:
```python
try:
    db.add(item1)
    db.add(item2)
    db.commit()
except Exception:
    db.rollback()
    raise
```

### Always Use UTC for Timestamps

```python
from datetime import UTC, datetime

# ✅ Correct
created_at = datetime.now(UTC)

# ❌ Wrong
created_at = datetime.now()  # No timezone info
```

### Never Expose Internal Errors

```python
# ❌ Wrong
except Exception as e:
    return {"error": str(e)}

# ✅ Correct
except Exception as e:
    log.error(str(e))
    raise HTTPException(status_code=500, detail="Internal server error")
```

### Use Status Codes Correctly

| Code | Meaning | When to Use |
|------|---------|------------|
| 200 | OK | GET succeeded |
| 201 | Created | POST/PUT succeeded |
| 204 | No Content | DELETE succeeded |
| 400 | Bad Request | Validation failed |
| 401 | Unauthorized | Auth token missing/invalid |
| 403 | Forbidden | User doesn't have permission |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate (e.g., SKU) |
| 422 | Unprocessable Entity | Schema validation failed |
| 500 | Server Error | Unhandled exception |

---

## Getting Help

### Questions?

1. **Check CLAUDE.md** for architecture & patterns
2. **Check PROJECT.md** for feature details
3. **Check AGENTS.md** for your agent's responsibilities
4. **Read existing code** in `backend/app/models/` & `backend/app/api/routes/auth.py`
5. **Check FastAPI docs** at http://localhost:8000/docs (when running)

### Dependencies on Other Agents

- **UI Agent** depends on all API endpoints
- **Inventory Agent** depends on Auth/Guard Agent
- **Operations Agent** depends on Auth/Guard Agent + Inventory Agent
- **Auth/Guard Agent** has no dependencies

### Handoff Process

When your agent completes:
1. Create a summary of what was implemented
2. List all new endpoints with their paths & methods
3. Note any breaking changes
4. Verify Swagger docs are auto-generated correctly
5. Run tests and fix any failures
6. Notify next agent that their dependencies are ready

---

**Last Updated**: 2026-09-26  
**Project**: StockSense Inventory Management System  
**Team**: 4 Specialized Agents
