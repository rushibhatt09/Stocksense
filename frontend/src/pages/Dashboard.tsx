import { useState } from "react";
import {
  AlertTriangle,
  ArrowDownToLine,
  ArrowUpFromLine,
  Package,
  Repeat,
  Scale,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import PageHeader from "../components/PageHeader";
import StatusBadge from "../components/StatusBadge";
import { api } from "../lib/api";
import type { DashboardSummary, Document, Warehouse } from "../lib/types";

const DOC_TYPE_LABELS: Record<string, string> = {
  receipt: "Receipt",
  delivery: "Delivery",
  internal: "Internal",
  adjustment: "Adjustment",
};

export default function Dashboard() {
  const [docType, setDocType] = useState("");
  const [status, setStatus] = useState("");
  const [warehouseId, setWarehouseId] = useState<number | "">("");

  const summaryQuery = useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: () => api<DashboardSummary>("/dashboard/summary"),
  });

  const warehousesQuery = useQuery({
    queryKey: ["warehouses"],
    queryFn: () => api<Warehouse[]>("/warehouses"),
  });

  const documentsQuery = useQuery({
    queryKey: ["documents", "dashboard", docType, status, warehouseId],
    queryFn: () =>
      api<Document[]>("/documents", {
        params: {
          doc_type: docType || undefined,
          status: status || undefined,
          warehouse_id: warehouseId || undefined,
        },
      }),
  });

  const summary = summaryQuery.data;

  const kpis: { label: string; value: number | undefined; icon: LucideIcon; tone: string }[] = [
    {
      label: "Total products in stock",
      value: summary?.total_products_in_stock,
      icon: Package,
      tone: "text-brand-600 bg-brand-50",
    },
    {
      label: "Low / out of stock",
      value: summary ? summary.low_stock_count + summary.out_of_stock_count : undefined,
      icon: AlertTriangle,
      tone: "text-amber-600 bg-amber-50",
    },
    {
      label: "Pending receipts",
      value: summary?.pending_receipts,
      icon: ArrowDownToLine,
      tone: "text-emerald-600 bg-emerald-50",
    },
    {
      label: "Pending deliveries",
      value: summary?.pending_deliveries,
      icon: ArrowUpFromLine,
      tone: "text-rose-600 bg-rose-50",
    },
    {
      label: "Transfers scheduled",
      value: summary?.pending_transfers,
      icon: Repeat,
      tone: "text-slate-600 bg-slate-100",
    },
    {
      label: "Pending adjustments",
      value: summary?.pending_adjustments,
      icon: Scale,
      tone: "text-indigo-600 bg-indigo-50",
    },
  ];

  const documents = documentsQuery.data ?? [];

  return (
    <>
      <PageHeader title="Dashboard" subtitle="A snapshot of today's inventory operations." />

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {kpis.map(({ label, value, icon: Icon, tone }) => (
          <article key={label} className="card p-5">
            <div className={`mb-3 inline-flex rounded-lg p-2 ${tone}`}>
              <Icon className="h-5 w-5" />
            </div>
            <p className="text-2xl font-semibold text-slate-900">
              {summaryQuery.isLoading ? "—" : (value ?? 0)}
            </p>
            <p className="mt-1 text-sm text-slate-500">{label}</p>
          </article>
        ))}
      </section>

      <section className="card mt-6 p-5">
        <h2 className="mb-4 text-sm font-semibold text-slate-700">Filters</h2>
        <div className="grid gap-4 sm:grid-cols-3">
          <div>
            <label className="label">Document type</label>
            <select className="input" value={docType} onChange={(event) => setDocType(event.target.value)}>
              <option value="">All</option>
              <option value="receipt">Receipts</option>
              <option value="delivery">Delivery</option>
              <option value="internal">Internal</option>
              <option value="adjustment">Adjustments</option>
            </select>
          </div>
          <div>
            <label className="label">Status</label>
            <select className="input" value={status} onChange={(event) => setStatus(event.target.value)}>
              <option value="">All</option>
              <option value="draft">Draft</option>
              <option value="waiting">Waiting</option>
              <option value="ready">Ready</option>
              <option value="done">Done</option>
              <option value="canceled">Canceled</option>
            </select>
          </div>
          <div>
            <label className="label">Warehouse</label>
            <select
              className="input"
              value={warehouseId}
              onChange={(event) =>
                setWarehouseId(event.target.value ? Number(event.target.value) : "")
              }
            >
              <option value="">All warehouses</option>
              {(warehousesQuery.data ?? []).map((warehouse) => (
                <option key={warehouse.id} value={warehouse.id}>
                  {warehouse.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </section>

      <section className="card mt-6 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="table-head">
            <tr>
              <th className="px-4 py-3">Reference</th>
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3">Route</th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {documentsQuery.isLoading && (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-slate-400">
                  Loading…
                </td>
              </tr>
            )}
            {!documentsQuery.isLoading && documents.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-slate-400">
                  No matching operations.
                </td>
              </tr>
            )}
            {documents.slice(0, 10).map((doc) => (
              <tr key={doc.id}>
                <td className="px-4 py-3 font-medium text-slate-800">{doc.reference}</td>
                <td className="px-4 py-3 text-slate-600">
                  {DOC_TYPE_LABELS[doc.doc_type] ?? doc.doc_type}
                </td>
                <td className="px-4 py-3 text-slate-600">
                  {doc.src_location.name} → {doc.dest_location.name}
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={doc.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
