import { useState } from "react";
import type { FormEvent } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Search } from "lucide-react";

import Modal from "../components/Modal";
import PageHeader from "../components/PageHeader";
import { useAuth } from "../auth/AuthContext";
import { ApiError, api } from "../lib/api";
import type { Category, Location, Product } from "../lib/types";

type ProductForm = {
  name: string;
  sku: string;
  category_id: number | "";
  uom: string;
  reorder_point: string;
  reorder_qty: string;
  initial_stock: string;
  initial_stock_location_id: number | "";
};

const EMPTY_FORM: ProductForm = {
  name: "",
  sku: "",
  category_id: "",
  uom: "Unit",
  reorder_point: "0",
  reorder_qty: "0",
  initial_stock: "",
  initial_stock_location_id: "",
};

export default function Products() {
  const { user } = useAuth();
  const isManager = user?.role === "manager";
  const queryClient = useQueryClient();

  const [search, setSearch] = useState("");
  const [categoryId, setCategoryId] = useState<number | "">("");
  const [lowStockOnly, setLowStockOnly] = useState(false);

  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState<ProductForm>(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const productsQuery = useQuery({
    queryKey: ["products", { search, categoryId, lowStockOnly }],
    queryFn: () =>
      api<Product[]>("/products", {
        params: {
          search: search || undefined,
          category_id: categoryId || undefined,
          low_stock: lowStockOnly || undefined,
        },
      }),
  });

  const categoriesQuery = useQuery({
    queryKey: ["categories"],
    queryFn: () => api<Category[]>("/categories"),
  });

  const locationsQuery = useQuery({
    queryKey: ["locations"],
    queryFn: () => api<Location[]>("/locations"),
  });

  const physicalLocations = (locationsQuery.data ?? []).filter(
    (location) => location.type === "internal",
  );

  function openModal() {
    setForm(EMPTY_FORM);
    setError(null);
    setModalOpen(true);
  }

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api<Product>("/products", {
        method: "POST",
        body: {
          name: form.name,
          sku: form.sku,
          category_id: form.category_id || null,
          uom: form.uom,
          reorder_point: Number(form.reorder_point || 0),
          reorder_qty: Number(form.reorder_qty || 0),
          initial_stock: form.initial_stock ? Number(form.initial_stock) : 0,
          initial_stock_location_id: form.initial_stock_location_id || null,
        },
      });
      await queryClient.invalidateQueries({ queryKey: ["products"] });
      await queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      setModalOpen(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create the product");
    } finally {
      setSubmitting(false);
    }
  }

  const products = productsQuery.data ?? [];

  return (
    <>
      <PageHeader
        title="Products"
        subtitle="Every product, its SKU and stock on hand."
        actions={
          isManager ? (
            <button type="button" className="btn-primary" onClick={openModal}>
              <Plus className="h-4 w-4" /> New product
            </button>
          ) : undefined
        }
      />

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            className="input w-56 pl-9"
            placeholder="Search name or SKU…"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>
        <select
          className="input w-48"
          value={categoryId}
          onChange={(event) => setCategoryId(event.target.value ? Number(event.target.value) : "")}
        >
          <option value="">All categories</option>
          {(categoriesQuery.data ?? []).map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </select>
        <label className="flex items-center gap-2 text-sm text-slate-600">
          <input
            type="checkbox"
            checked={lowStockOnly}
            onChange={(event) => setLowStockOnly(event.target.checked)}
          />
          Low stock only
        </label>
      </div>

      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="table-head">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">SKU</th>
              <th className="px-4 py-3">UOM</th>
              <th className="px-4 py-3 text-right">On hand</th>
              <th className="px-4 py-3 text-right">Reorder point</th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {productsQuery.isLoading && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                  Loading…
                </td>
              </tr>
            )}
            {!productsQuery.isLoading && products.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                  No products found.
                </td>
              </tr>
            )}
            {products.map((product) => (
              <tr key={product.id}>
                <td className="px-4 py-3 font-medium text-slate-800">{product.name}</td>
                <td className="px-4 py-3 text-slate-600">{product.sku}</td>
                <td className="px-4 py-3 text-slate-600">{product.uom}</td>
                <td className="px-4 py-3 text-right text-slate-800">{product.on_hand}</td>
                <td className="px-4 py-3 text-right text-slate-600">{product.reorder_point}</td>
                <td className="px-4 py-3">
                  {product.on_hand <= 0 ? (
                    <span className="inline-flex rounded-full bg-rose-100 px-2.5 py-0.5 text-xs font-medium text-rose-700">
                      Out of stock
                    </span>
                  ) : product.is_low_stock ? (
                    <span className="inline-flex rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-medium text-amber-800">
                      Low stock
                    </span>
                  ) : (
                    <span className="inline-flex rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-medium text-emerald-800">
                      In stock
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="New product">
        <form onSubmit={handleCreate} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Name</label>
              <input
                required
                className="input"
                value={form.name}
                onChange={(event) => setForm({ ...form, name: event.target.value })}
              />
            </div>
            <div>
              <label className="label">SKU</label>
              <input
                required
                className="input"
                value={form.sku}
                onChange={(event) => setForm({ ...form, sku: event.target.value })}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Category</label>
              <select
                className="input"
                value={form.category_id}
                onChange={(event) =>
                  setForm({
                    ...form,
                    category_id: event.target.value ? Number(event.target.value) : "",
                  })
                }
              >
                <option value="">None</option>
                {(categoriesQuery.data ?? []).map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Unit of measure</label>
              <input
                className="input"
                value={form.uom}
                onChange={(event) => setForm({ ...form, uom: event.target.value })}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Reorder point</label>
              <input
                type="number"
                min="0"
                className="input"
                value={form.reorder_point}
                onChange={(event) => setForm({ ...form, reorder_point: event.target.value })}
              />
            </div>
            <div>
              <label className="label">Reorder quantity</label>
              <input
                type="number"
                min="0"
                className="input"
                value={form.reorder_qty}
                onChange={(event) => setForm({ ...form, reorder_qty: event.target.value })}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Initial stock (optional)</label>
              <input
                type="number"
                min="0"
                className="input"
                value={form.initial_stock}
                onChange={(event) => setForm({ ...form, initial_stock: event.target.value })}
              />
            </div>
            <div>
              <label className="label">At location</label>
              <select
                className="input"
                value={form.initial_stock_location_id}
                onChange={(event) =>
                  setForm({
                    ...form,
                    initial_stock_location_id: event.target.value ? Number(event.target.value) : "",
                  })
                }
              >
                <option value="">Select…</option>
                {physicalLocations.map((location) => (
                  <option key={location.id} value={location.id}>
                    {location.name} · {location.code}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {error && <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}

          <div className="flex justify-end gap-2 pt-2">
            <button type="button" className="btn-secondary" onClick={() => setModalOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={submitting}>
              {submitting ? "Saving…" : "Create product"}
            </button>
          </div>
        </form>
      </Modal>
    </>
  );
}
