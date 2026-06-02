"use client";

import { useState } from "react";
import type { PortalModule } from "../../lib/portal-types";

const CATEGORY_LABELS: Record<string, string> = {
  differential: "Differential & Selection",
  navigation: "Repertory Navigation",
  analytics: "Patient Memory & Analytics",
  safety: "Safety, Privacy & Audit",
  materia_medica: "Materia Medica & Learning",
  teaching: "Teaching & Training",
  workflow: "Documentation & Workflow",
  infrastructure: "Multi-Agent & Infra",
};

const CATEGORY_ORDER = [
  "differential",
  "safety",
  "navigation",
  "analytics",
  "materia_medica",
  "workflow",
  "teaching",
  "infrastructure",
];

export default function ModulePickerSidebar({
  modules,
  activeIds,
  onToggle,
}: {
  modules: PortalModule[];
  activeIds: Set<string>;
  onToggle: (id: string) => void;
}) {
  const [search, setSearch] = useState("");
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());

  const filtered = modules.filter(
    (m) =>
      m.name.toLowerCase().includes(search.toLowerCase()) ||
      m.description.toLowerCase().includes(search.toLowerCase()) ||
      String(m.benefit).includes(search)
  );

  const byCategory = filtered.reduce((acc, m) => {
    if (!acc[m.category]) acc[m.category] = [];
    acc[m.category].push(m);
    return acc;
  }, {} as Record<string, PortalModule[]>);

  return (
    <aside className="w-72 bg-white border-r flex flex-col h-full shrink-0">
      <div className="p-4 border-b">
        <div className="flex items-center justify-between mb-2">
          <h2 className="font-semibold text-sm">Module Picker</h2>
          <span className="text-xs text-gray-400">{activeIds.size} active</span>
        </div>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search modules..."
          className="w-full border rounded-md px-2 py-1 text-sm"
        />
      </div>

      <div className="flex-1 overflow-y-auto">
        {CATEGORY_ORDER.map((cat) => {
          const list = byCategory[cat];
          if (!list) return null;
          const isCollapsed = collapsed.has(cat);
          return (
            <div key={cat} className="border-b">
              <button
                className="w-full flex items-center justify-between px-4 py-2 text-xs font-semibold bg-gray-50 hover:bg-gray-100 transition"
                onClick={() =>
                  setCollapsed((prev) => {
                    const next = new Set(prev);
                    if (next.has(cat)) next.delete(cat);
                    else next.add(cat);
                    return next;
                  })
                }
              >
                <span>{CATEGORY_LABELS[cat]}</span>
                <span className="text-gray-400">{isCollapsed ? "▸" : "▾"}</span>
              </button>
              {!isCollapsed &&
                list.map((m) => (
                  <label
                    key={m.id}
                    className="flex items-start gap-2 px-4 py-2 text-sm hover:bg-gray-50 cursor-pointer transition"
                  >
                    <input
                      type="checkbox"
                      checked={activeIds.has(m.id)}
                      onChange={() => onToggle(m.id)}
                      className="mt-0.5 shrink-0"
                    />
                    <div className="leading-tight">
                      <div className="font-medium text-sm">{m.name}</div>
                      <div className="text-xs text-gray-400">
                        #{m.benefit} — {m.description.slice(0, 60)}…
                      </div>
                    </div>
                  </label>
                ))}
            </div>
          );
        })}
      </div>
    </aside>
  );
}
