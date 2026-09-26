import { Trash2 } from "lucide-react";

import type { ProductBasic } from "../lib/types";

export type LineDraft = { product_id: number | ""; qty: string };

type Props = {
  products: ProductBasic[];
  lines: LineDraft[];
  onChange: (lines: LineDraft[]) => void;
  qtyLabel?: string;
};

/** The product + quantity rows shared by every document form (receipts,
 * deliveries, transfers, adjustments). */
export default function LineItemsEditor({ products, lines, onChange, qtyLabel = "Quantity" }: Props) {
  function updateLine(index: number, patch: Partial<LineDraft>) {
    onChange(lines.map((line, i) => (i === index ? { ...line, ...patch } : line)));
  }

  function addLine() {
    onChange([...lines, { product_id: "", qty: "" }]);
  }

  function removeLine(index: number) {
    onChange(lines.filter((_, i) => i !== index));
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-slate-700">Line items</span>
        <button type="button" className="text-sm text-brand-600 hover:underline" onClick={addLine}>
          + Add line
        </button>
      </div>

      {lines.length === 0 && <p className="text-sm text-slate-400">No lines yet.</p>}

      {lines.map((line, index) => (
        <div key={index} className="flex gap-2">
          <select
            className="input"
            value={line.product_id}
            onChange={(event) =>
              updateLine(index, {
                product_id: event.target.value ? Number(event.target.value) : "",
              })
            }
          >
            <option value="">Select product…</option>
            {products.map((product) => (
              <option key={product.id} value={product.id}>
                {product.name} ({product.sku})
              </option>
            ))}
          </select>
          <input
            type="number"
            min="0"
            step="any"
            className="input w-36"
            placeholder={qtyLabel}
            value={line.qty}
            onChange={(event) => updateLine(index, { qty: event.target.value })}
          />
          <button
            type="button"
            className="btn-secondary px-3"
            onClick={() => removeLine(index)}
            aria-label="Remove line"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      ))}
    </div>
  );
}
