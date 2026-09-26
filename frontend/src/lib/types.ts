/** Shapes returned by the StockSense API. Mirrors backend/app/schemas/*.py. */

export type Role = "manager" | "staff";

export interface Category {
  id: number;
  name: string;
  parent_id: number | null;
}

export interface Warehouse {
  id: number;
  name: string;
  code: string;
  address: string | null;
}

export type LocationType = "internal" | "vendor" | "customer" | "adjustment" | "scrap";

export interface Location {
  id: number;
  name: string;
  code: string;
  type: LocationType;
  warehouse_id: number | null;
  parent_id: number | null;
}

/** Minimal location info nested inside documents and stock moves. */
export interface LocationBasic {
  id: number;
  name: string;
  code: string;
  type: LocationType;
}

export interface Product {
  id: number;
  name: string;
  sku: string;
  category_id: number | null;
  uom: string;
  barcode: string | null;
  reorder_point: number;
  reorder_qty: number;
  is_active: boolean;
  on_hand: number;
  is_low_stock: boolean;
}

/** Minimal product info nested inside documents and stock moves. */
export interface ProductBasic {
  id: number;
  name: string;
  sku: string;
  uom: string;
}

export interface StockByLocation {
  location: LocationBasic;
  on_hand: number;
}

export type DocType = "receipt" | "delivery" | "internal" | "adjustment";
export type DocStatus = "draft" | "waiting" | "ready" | "done" | "canceled";

export interface DocumentLine {
  id: number;
  product: ProductBasic;
  qty_demand: number;
  qty_done: number;
}

export interface Document {
  id: number;
  reference: string;
  doc_type: DocType;
  status: DocStatus;
  partner_name: string | null;
  src_location: LocationBasic;
  dest_location: LocationBasic;
  scheduled_at: string | null;
  validated_at: string | null;
  created_by: number | null;
  note: string | null;
  lines: DocumentLine[];
}

export interface StockMove {
  id: number;
  document_id: number | null;
  product: ProductBasic;
  from_location: LocationBasic;
  to_location: LocationBasic;
  qty: number;
  done_at: string;
}

export interface DashboardSummary {
  total_products_in_stock: number;
  low_stock_count: number;
  out_of_stock_count: number;
  pending_receipts: number;
  pending_deliveries: number;
  pending_transfers: number;
  pending_adjustments: number;
}

/** The product list is paged: the rows live under `items`. */
export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
