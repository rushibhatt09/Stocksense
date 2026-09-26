import {
  AlertTriangle,
  ArrowDownToLine,
  ArrowUpFromLine,
  Package,
  Repeat,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import PageHeader from "../components/PageHeader";

const KPIS: { label: string; icon: LucideIcon; tone: string }[] = [
  { label: "Total products in stock", icon: Package, tone: "text-brand-600 bg-brand-50" },
  { label: "Low / out of stock", icon: AlertTriangle, tone: "text-amber-600 bg-amber-50" },
  { label: "Pending receipts", icon: ArrowDownToLine, tone: "text-emerald-600 bg-emerald-50" },
  { label: "Pending deliveries", icon: ArrowUpFromLine, tone: "text-rose-600 bg-rose-50" },
  { label: "Transfers scheduled", icon: Repeat, tone: "text-slate-600 bg-slate-100" },
];

const FILTERS = [
  { label: "Document type", options: ["All", "Receipts", "Delivery", "Internal", "Adjustments"] },
  { label: "Status", options: ["All", "Draft", "Waiting", "Ready", "Done", "Canceled"] },
  { label: "Warehouse", options: ["All warehouses"] },
  { label: "Category", options: ["All categories"] },
];

export default function Dashboard() {
  return (
    <>
      <PageHeader title="Dashboard" subtitle="A snapshot of today's inventory operations." />

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        {KPIS.map(({ label, icon: Icon, tone }) => (
          <article key={label} className="card p-5">
            <div className={`mb-3 inline-flex rounded-lg p-2 ${tone}`}>
              <Icon className="h-5 w-5" />
            </div>
            <p className="text-2xl font-semibold text-slate-400">—</p>
            <p className="mt-1 text-sm text-slate-500">{label}</p>
          </article>
        ))}
      </section>

      <section className="card mt-6 p-5">
        <h2 className="mb-4 text-sm font-semibold text-slate-700">Filters</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {FILTERS.map(({ label, options }) => (
            <div key={label}>
              <label className="label">{label}</label>
              <select className="input" disabled>
                {options.map((option) => (
                  <option key={option}>{option}</option>
                ))}
              </select>
            </div>
          ))}
        </div>
      </section>

      <section className="card mt-6 p-8 text-center">
        <p className="text-sm text-slate-500">
          KPI values and the low-stock list arrive with the dashboard endpoint.
        </p>
      </section>
    </>
  );
}
