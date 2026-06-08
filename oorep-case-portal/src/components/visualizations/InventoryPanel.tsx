"use client";

export default function InventoryPanel({ result }: { result?: { total_items?: number; low_stock_count?: number; total_quantity?: number } }) {
  const low = result?.low_stock_count || 0;
  return (
    <div className="space-y-3">
      <p className="text-xs text-slate-500 italic leading-relaxed">
        At-a-glance pharmacy status — how many distinct remedies are in stock, total units on the shelf, and how many items have fallen below the reorder threshold. A red low-stock count warns the practitioner to re-order before a patient runs out of a needed potency.
      </p>
      <div className="grid grid-cols-3 gap-2 text-center">
        <div>
          <div className="text-xl font-bold text-slate-800">{result?.total_items || 0}</div>
          <div className="text-xs text-slate-500">Items</div>
        </div>
        <div>
          <div className="text-xl font-bold text-slate-800">{result?.total_quantity || 0}</div>
          <div className="text-xs text-slate-500">Quantity</div>
        </div>
        <div>
          <div className={`text-xl font-bold ${low > 0 ? "text-red-600" : "text-emerald-600"}`}>{low}</div>
          <div className="text-xs text-slate-500">Low stock</div>
        </div>
      </div>
      {low > 0 && <div className="text-xs bg-red-50 text-red-600 p-2 rounded">⚠ {low} items need reordering</div>}
    </div>
  );
}
