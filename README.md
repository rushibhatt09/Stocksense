# StockSense

An Inventory Management System that replaces manual registers and spreadsheets:
products, multi-warehouse stock, and the four stock operations a warehouse
actually performs, all recorded in one append-only ledger.

## The core idea

There is no `quantity` column anywhere. Every operation appends rows to
`stock_moves` — *this product, this quantity, from location A to location B* —
and on-hand stock is derived by summing that ledger. One engine covers all four
operations:

| Operation | Move | Effect on total stock |
| --- | --- | --- |
| Receipt | Vendors (virtual) → warehouse | increases |
| Delivery | warehouse → Customers (virtual) | decreases |
| Internal transfer | location → location | unchanged, location changes |
| Adjustment | Inventory Adjustment (virtual) ↔ location | ± the counted difference |

Move History, the dashboard KPIs, per-location stock and low-stock alerts are
all derived from the same rows, so the numbers can never drift apart.

## Running the backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # optional: defaults to SQLite
alembic upgrade head
python -m app.seed            # warehouses, locations, categories, 10 products, 2 users
uvicorn app.main:app --reload
```

Interactive API docs: http://localhost:8000/docs

Demo accounts created by the seed:

| Email | Password | Role |
| --- | --- | --- |
| manager@stocksense.app | manager123 | manager |
| staff@stocksense.app | staff123 | staff |

To use Postgres instead of SQLite: `docker compose up -d db`, then set
`DATABASE_URL` in `backend/.env` and re-run `alembic upgrade head`.

## Running the frontend

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

The frontend reads `VITE_API_URL` (defaults to `http://localhost:8000`).

## Repository layout

```
backend/    FastAPI + SQLAlchemy + Alembic
frontend/   Vite + React + TypeScript + Tailwind
```
