import { useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Plus, X as XIcon } from "lucide-react";

import LineItemsEditor from "./LineItemsEditor";
import type { LineDraft } from "./LineItemsEditor";
import Modal from "./Modal";
import PageHeader from "./PageHeader";
import StatusBadge from "./StatusBadge";
import { ApiError, api, fetchProducts, fetchDocuments } from "../lib/api";
import type { Document, DocType, Location, LocationType } from "../lib/types";

/** Which side of the document the user picks a physical location for, and
 * which virtual location type the other side is auto-filled from. Mirrors
 * the rules enforced server-side in app/services/documents.py. */
const CONFIG: Record<
  DocType,
  {
    title: string;
    subtitle: string;
    newLabel: string;
    partnerLabel: string | null;
    qtyLabel: string;
    pick: "src" | "dest" | "both";
    virtualType: LocationType | null;
  }
> = {
  receipt: {
    title: "Receipts",
    subtitle: "Incoming stock from vendors.",
    newLabel: "New receipt",
    partnerLabel: "Supplier",
    qtyLabel: "Quantity received",
    pick: "dest",
    virtualType: "vendor",
  },
  delivery: {
    title: "Delivery Orders",
    subtitle: "Outgoing stock to customers.",
    newLabel: "New delivery order",
    partnerLabel: "Customer",
    qtyLabel: "Quantity to deliver",
    pick: "src",
    virtualType: "customer",
  },
  internal: {
    title: "Internal Transfers",
    subtitle: "Move stock between locations inside the company.",
    newLabel: "New transfer",
    partnerLabel: null,
    qtyLabel: "Quantity",
    pick: "both",
    virtualType: null,
  },
  adjustment: {
    title: "Inventory Adjustment",
    subtitle: "Correct recorded stock against a physical count.",
    newLabel: "New adjustment",
    partnerLabel: null,
    qtyLabel: "Counted quantity",
    pick: "dest",
    virtualType: "adjustment",
  },
};

const STATUS_FILTERS = ["all", "draft", "waiting", "ready", "done", "canceled"];

export default function DocumentBoard({ docType }: { docType: DocType }) {
  const config = CONFIG[docType];
  const queryClient = useQueryClient();

  const [statusFilter, setStatusFilter] = useState("all");
  const [modalOpen, setModalOpen] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [partnerName, setPartnerName] = useState("");
  const [srcLocationId, setSrcLocationId] = useState<number | "">("");
  const [destLocationId, setDestLocationId] = useState<number | "">("");
  const [lines, setLines] = useState<LineDraft[]>([{ product_id: "", qty: "" }]);

  const documentsQuery = useQuery({
    queryKey: ["documents", docType, statusFilter],
    queryFn: () =>
      fetchDocuments({
        doc_type: docType,
        status: statusFilter === "all" ? undefined : statusFilter,
      }),
  });

  const locationsQuery = useQuery({
    queryKey: ["locations"],
    // physical_only=false so the vendor, customer and adjustment locations
    // come back too: a receipt needs the Vendors location as its source.
    queryFn: () => api<Location[]>("/locations", { params: { physical_only: false } }),
  });

  const productsQuery = useQuery({
    queryKey: ["products", { is_active: true }],
    queryFn: () => fetchProducts(),
  });

  const locations = locationsQuery.data ?? [];
  const physicalLocations = locations.filter((location) => location.type === "internal");
  const virtualLocation = config.virtualType
    ? locations.find((location) => location.type === config.virtualType)
    : undefined;

  function resetForm() {
    setPartnerName("");
    setSrcLocationId("");
    setDestLocationId("");
    setLines([{ product_id: "", qty: "" }]);
    setFormError(null);
  }

  function openModal() {
    resetForm();
    setModalOpen(true);
  }

  function invalidateAfterChange() {
    queryClient.invalidateQueries({ queryKey: ["documents", docType] });
    queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
    queryClient.invalidateQueries({ queryKey: ["products"] });
    queryClient.invalidateQueries({ queryKey: ["stock-moves"] });
  }

  const validateMutation = useMutation({
    mutationFn: (id: number) => api<Document>(`/documents/${id}/validate`, { method: "POST" }),
    onSuccess: () => {
      setActionError(null);
      invalidateAfterChange();
    },
    onError: (error: unknown) =>
      setActionError(error instanceof ApiError ? error.message : "Could not validate the document"),
  });

  const cancelMutation = useMutation({
    mutationFn: (id: number) => api<Document>(`/documents/${id}/cancel`, { method: "POST" }),
    onSuccess: () => {
      setActionError(null);
      queryClient.invalidateQueries({ queryKey: ["documents", docType] });
    },
    onError: (error: unknown) =>
      setActionError(error instanceof ApiError ? error.message : "Could not cancel the document"),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api<void>(`/documents/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      setActionError(null);
      queryClient.invalidateQueries({ queryKey: ["documents", docType] });
    },
    onError: (error: unknown) =>
      setActionError(error instanceof ApiError ? error.message : "Could not delete the document"),
  });

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    setFormError(null);

    const cleanLines = lines
      .filter((line) => line.product_id !== "" && line.qty !== "")
      .map((line) => ({ product_id: Number(line.product_id), qty: Number(line.qty) }));

    if (cleanLines.length === 0) {
      setFormError("Add at least one product line");
      return;
    }

    let src = srcLocationId;
    let dest = destLocationId;

    if (config.pick === "dest") {
      if (!virtualLocation) {
        setFormError(`No ${config.virtualType} location is configured yet`);
        return;
      }
      src = virtualLocation.id;
    }
    if (config.pick === "src") {
      if (!virtualLocation) {
        setFormError(`No ${config.virtualType} location is configured yet`);
        return;
      }
      dest = virtualLocation.id;
    }
    if (!src || !dest) {
      setFormError("Choose a location");
      return;
    }
    if (config.pick === "both" && src === dest) {
      setFormError("Source and destination must be different");
      return;
    }

    setSubmitting(true);
    try {
      await api<Document>("/documents", {
        method: "POST",
        body: {
          doc_type: docType,
          partner_name: config.partnerLabel ? partnerName || null : null,
          src_location_id: src,
          dest_location_id: dest,
          lines: cleanLines,
        },
      });
      invalidateAfterChange();
      setModalOpen(false);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Could not create the document");
    } finally {
      setSubmitting(false);
    }
  }

  const documents = documentsQuery.data ?? [];
  const routeLabel = docType === "internal" ? "Route" : "Location";

  return (
    <>
      <PageHeader
        title={config.title}
        subtitle={config.subtitle}
        actions={
          <button type="button" className="btn-primary" onClick={openModal}>
            <Plus className="h-4 w-4" /> {config.newLabel}
          </button>
        }
      />

      <div className="mb-4 flex items-center gap-2">
        <label className="text-xs font-medium text-slate-700">Status</label>
        <select
          className="input w-40"
          value={statusFilter}
          onChange={(event) => setStatusFilter(event.target.value)}
        >
          {STATUS_FILTERS.map((option) => (
            <option key={option} value={option}>
              {option === "all" ? "All" : option[0].toUpperCase() + option.slice(1)}
            </option>
          ))}
        </select>
      </div>

      {actionError && (
        <p className="mb-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{actionError}</p>
      )}

      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="table-head">
            <tr>
              <th className="px-4 py-3">Reference</th>
              {config.partnerLabel && <th className="px-4 py-3">{config.partnerLabel}</th>}
              <th className="px-4 py-3">{routeLabel}</th>
              <th className="px-4 py-3">Lines</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {documentsQuery.isLoading && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                  Loading…
                </td>
              </tr>
            )}
            {!documentsQuery.isLoading && documents.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                  No documents yet.
                </td>
              </tr>
            )}
            {documents.map((doc) => {
              const isOpen = doc.status !== "done" && doc.status !== "canceled";
              return (
                <tr key={doc.id}>
                  <td className="px-4 py-3 font-medium text-slate-800">{doc.reference}</td>
                  {config.partnerLabel && (
                    <td className="px-4 py-3 text-slate-600">{doc.partner_name ?? "—"}</td>
                  )}
                  <td className="px-4 py-3 text-slate-600">
                    {docType === "internal"
                      ? `${doc.src_location.name} → ${doc.dest_location.name}`
                      : docType === "delivery"
                        ? doc.src_location.name
                        : doc.dest_location.name}
                  </td>
                  <td className="px-4 py-3 text-slate-600">{doc.lines.length}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={doc.status} />
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-2">
                      {isOpen && (
                        <button
                          type="button"
                          className="btn-secondary px-2 py-1 text-xs"
                          disabled={validateMutation.isPending}
                          onClick={() => validateMutation.mutate(doc.id)}
                        >
                          <Check className="h-3.5 w-3.5" /> Validate
                        </button>
                      )}
                      {doc.status === "draft" && (
                        <button
                          type="button"
                          className="btn-secondary px-2 py-1 text-xs text-rose-600"
                          disabled={deleteMutation.isPending}
                          onClick={() => deleteMutation.mutate(doc.id)}
                        >
                          <XIcon className="h-3.5 w-3.5" /> Delete
                        </button>
                      )}
                      {isOpen && (
                        <button
                          type="button"
                          className="btn-secondary px-2 py-1 text-xs"
                          disabled={cancelMutation.isPending}
                          onClick={() => cancelMutation.mutate(doc.id)}
                        >
                          Cancel
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={config.newLabel}>
        <form onSubmit={handleCreate} className="space-y-4">
          {config.partnerLabel && (
            <div>
              <label className="label">{config.partnerLabel}</label>
              <input
                className="input"
                value={partnerName}
                onChange={(event) => setPartnerName(event.target.value)}
              />
            </div>
          )}

          {config.virtualType && (
            <p className="text-xs text-slate-500">
              {config.pick === "dest" ? "From" : "To"}:{" "}
              <span className="font-medium text-slate-700">
                {virtualLocation?.name ?? config.virtualType}
              </span>
            </p>
          )}

          {config.pick === "both" && (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">Source location</label>
                <select
                  className="input"
                  value={srcLocationId}
                  onChange={(event) =>
                    setSrcLocationId(event.target.value ? Number(event.target.value) : "")
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
              <div>
                <label className="label">Destination location</label>
                <select
                  className="input"
                  value={destLocationId}
                  onChange={(event) =>
                    setDestLocationId(event.target.value ? Number(event.target.value) : "")
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
          )}

          {config.pick === "dest" && (
            <div>
              <label className="label">
                {docType === "adjustment" ? "Location being counted" : "Location"}
              </label>
              <select
                className="input"
                value={destLocationId}
                onChange={(event) =>
                  setDestLocationId(event.target.value ? Number(event.target.value) : "")
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
          )}

          {config.pick === "src" && (
            <div>
              <label className="label">Location</label>
              <select
                className="input"
                value={srcLocationId}
                onChange={(event) =>
                  setSrcLocationId(event.target.value ? Number(event.target.value) : "")
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
          )}

          <LineItemsEditor
            products={productsQuery.data ?? []}
            lines={lines}
            onChange={setLines}
            qtyLabel={config.qtyLabel}
          />

          {formError && (
            <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{formError}</p>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <button type="button" className="btn-secondary" onClick={() => setModalOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={submitting}>
              {submitting ? "Saving…" : "Save"}
            </button>
          </div>
        </form>
      </Modal>
    </>
  );
}
