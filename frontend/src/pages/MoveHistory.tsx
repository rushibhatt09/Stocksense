import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import PageHeader from "../components/PageHeader";
import { api } from "../lib/api";
import type { Product, StockMove } from "../lib/types";

export default function MoveHistory() {
  const [productId, setProductId] = useState<number | "">("");

  const productsQuery = useQuery({
    queryKey: ["products"],
    queryFn: () => api<Product[]>("/products"),
  });

  const movesQuery = useQuery({
    queryKey: ["stock-moves", productId],
    queryFn: () =>
      api<StockMove[]>("/stock-moves", { params: { product_id: productId || undefined } }),
  });

  const moves = movesQuery.data ?? [];

  return (
    <>
      <PageHeader title="Move History" subtitle="Every stock movement, in order." />

      <div className="mb-4 flex items-center gap-2">
        <label className="text-xs font-medium text-slate-700">Product</label>
        <select
          className="input w-64"
          value={productId}
          onChange={(event) => setProductId(event.target.value ? Number(event.target.value) : "")}
        >
          <option value="">All products</option>
          {(productsQuery.data ?? []).map((product) => (
            <option key={product.id} value={product.id}>
              {product.name} ({product.sku})
            </option>
          ))}
        </select>
      </div>

      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="table-head">
            <tr>
              <th className="px-4 py-3">Date</th>
              <th className="px-4 py-3">Product</th>
              <th className="px-4 py-3">From</th>
              <th className="px-4 py-3">To</th>
              <th className="px-4 py-3 text-right">Quantity</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {movesQuery.isLoading && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-slate-400">
                  Loading…
                </td>
              </tr>
            )}
            {!movesQuery.isLoading && moves.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-slate-400">
                  No stock movements yet.
                </td>
              </tr>
            )}
            {moves.map((move) => (
              <tr key={move.id}>
                <td className="px-4 py-3 text-slate-600">
                  {new Date(move.done_at).toLocaleString()}
                </td>
                <td className="px-4 py-3 font-medium text-slate-800">{move.product.name}</td>
                <td className="px-4 py-3 text-slate-600">{move.from_location.name}</td>
                <td className="px-4 py-3 text-slate-600">{move.to_location.name}</td>
                <td className="px-4 py-3 text-right text-slate-800">
                  {move.qty} {move.product.uom}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
