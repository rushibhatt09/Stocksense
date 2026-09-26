import { useState } from "react";
import type { FormEvent } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";

import Modal from "../components/Modal";
import PageHeader from "../components/PageHeader";
import { useAuth } from "../auth/AuthContext";
import { ApiError, api } from "../lib/api";
import type { Location, Warehouse } from "../lib/types";

export default function SettingsWarehouses() {
  const { user } = useAuth();
  const isManager = user?.role === "manager";
  const queryClient = useQueryClient();

  const warehousesQuery = useQuery({
    queryKey: ["warehouses"],
    queryFn: () => api<Warehouse[]>("/warehouses"),
  });
  const locationsQuery = useQuery({
    queryKey: ["locations"],
    queryFn: () => api<Location[]>("/locations", { params: { physical_only: false } }),
  });

  const [warehouseModalOpen, setWarehouseModalOpen] = useState(false);
  const [locationModalOpen, setLocationModalOpen] = useState(false);
  const [activeWarehouseId, setActiveWarehouseId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [warehouseForm, setWarehouseForm] = useState({ name: "", code: "", address: "" });
  const [locationForm, setLocationForm] = useState({ name: "", code: "" });

  function openWarehouseModal() {
    setWarehouseForm({ name: "", code: "", address: "" });
    setError(null);
    setWarehouseModalOpen(true);
  }

  async function handleCreateWarehouse(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api("/warehouses", {
        method: "POST",
        body: { ...warehouseForm, address: warehouseForm.address || null },
      });
      await queryClient.invalidateQueries({ queryKey: ["warehouses"] });
      setWarehouseModalOpen(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create the warehouse");
    } finally {
      setSubmitting(false);
    }
  }

  function openLocationModal(warehouseId: number) {
    setActiveWarehouseId(warehouseId);
    setLocationForm({ name: "", code: "" });
    setError(null);
    setLocationModalOpen(true);
  }

  async function handleCreateLocation(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api("/locations", {
        method: "POST",
        body: { ...locationForm, type: "internal", warehouse_id: activeWarehouseId },
      });
      await queryClient.invalidateQueries({ queryKey: ["locations"] });
      setLocationModalOpen(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create the location");
    } finally {
      setSubmitting(false);
    }
  }

  const warehouses = warehousesQuery.data ?? [];
  const locations = locationsQuery.data ?? [];
  const virtualLocations = locations.filter((location) => location.warehouse_id == null);

  return (
    <>
      <PageHeader
        title="Warehouses"
        subtitle="Warehouses and the locations inside them."
        actions={
          isManager ? (
            <button type="button" className="btn-primary" onClick={openWarehouseModal}>
              <Plus className="h-4 w-4" /> New warehouse
            </button>
          ) : undefined
        }
      />

      <div className="space-y-4">
        {warehouses.map((warehouse) => {
          const warehouseLocations = locations.filter(
            (location) => location.warehouse_id === warehouse.id,
          );
          return (
            <div key={warehouse.id} className="card p-5">
              <div className="mb-3 flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-slate-800">{warehouse.name}</h3>
                  <p className="text-xs text-slate-500">
                    {warehouse.code}
                    {warehouse.address ? ` · ${warehouse.address}` : ""}
                  </p>
                </div>
                {isManager && (
                  <button
                    type="button"
                    className="btn-secondary px-3 py-1.5 text-xs"
                    onClick={() => openLocationModal(warehouse.id)}
                  >
                    <Plus className="h-3.5 w-3.5" /> Location
                  </button>
                )}
              </div>
              {warehouseLocations.length === 0 ? (
                <p className="text-sm text-slate-400">No locations yet.</p>
              ) : (
                <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {warehouseLocations.map((location) => (
                    <li key={location.id} className="rounded-lg border border-slate-200 px-3 py-2 text-sm">
                      <p className="font-medium text-slate-700">{location.name}</p>
                      <p className="text-xs text-slate-500">{location.code}</p>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          );
        })}

        {warehouses.length === 0 && !warehousesQuery.isLoading && (
          <div className="card p-8 text-center text-sm text-slate-500">No warehouses yet.</div>
        )}

        <div className="card p-5">
          <h3 className="mb-1 text-sm font-semibold text-slate-800">Virtual locations</h3>
          <p className="mb-3 text-xs text-slate-500">
            The counterpart every stock move balances against — vendors, customers, adjustments and
            scrap. Seeded automatically, not created here.
          </p>
          <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
            {virtualLocations.map((location) => (
              <li key={location.id} className="rounded-lg border border-slate-200 px-3 py-2 text-sm">
                <p className="font-medium capitalize text-slate-700">{location.type}</p>
                <p className="text-xs text-slate-500">{location.name}</p>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <Modal open={warehouseModalOpen} onClose={() => setWarehouseModalOpen(false)} title="New warehouse">
        <form onSubmit={handleCreateWarehouse} className="space-y-4">
          <div>
            <label className="label">Name</label>
            <input
              required
              className="input"
              value={warehouseForm.name}
              onChange={(event) => setWarehouseForm({ ...warehouseForm, name: event.target.value })}
            />
          </div>
          <div>
            <label className="label">Code</label>
            <input
              required
              className="input"
              value={warehouseForm.code}
              onChange={(event) => setWarehouseForm({ ...warehouseForm, code: event.target.value })}
            />
          </div>
          <div>
            <label className="label">Address (optional)</label>
            <input
              className="input"
              value={warehouseForm.address}
              onChange={(event) => setWarehouseForm({ ...warehouseForm, address: event.target.value })}
            />
          </div>
          {error && <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" className="btn-secondary" onClick={() => setWarehouseModalOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={submitting}>
              {submitting ? "Saving…" : "Create"}
            </button>
          </div>
        </form>
      </Modal>

      <Modal open={locationModalOpen} onClose={() => setLocationModalOpen(false)} title="New location">
        <form onSubmit={handleCreateLocation} className="space-y-4">
          <div>
            <label className="label">Name</label>
            <input
              required
              className="input"
              value={locationForm.name}
              onChange={(event) => setLocationForm({ ...locationForm, name: event.target.value })}
            />
          </div>
          <div>
            <label className="label">Code</label>
            <input
              required
              className="input"
              value={locationForm.code}
              onChange={(event) => setLocationForm({ ...locationForm, code: event.target.value })}
            />
          </div>
          {error && <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" className="btn-secondary" onClick={() => setLocationModalOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={submitting}>
              {submitting ? "Saving…" : "Create"}
            </button>
          </div>
        </form>
      </Modal>
    </>
  );
}
