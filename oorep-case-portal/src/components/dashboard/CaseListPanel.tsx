"use client";

import { useState } from "react";

export interface SavedCase {
  id: string;
  case_code: string;
  patient_pseudonym: string;
  chief_concern: string;
  modalities: string;
  body: string;
  created_at: string;
  status: string;
}

interface CaseListPanelProps {
  cases: SavedCase[];
  onLoad: (c: SavedCase) => void;
  onDelete: (id: string) => void;
  activeCaseId?: string;
}

export default function CaseListPanel({
  cases,
  onLoad,
  onDelete,
  activeCaseId,
}: CaseListPanelProps) {
  const [search, setSearch] = useState("");
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);

  const filtered = cases.filter((c) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      c.patient_pseudonym.toLowerCase().includes(q) ||
      c.chief_concern.toLowerCase().includes(q) ||
      c.case_code.toLowerCase().includes(q)
    );
  });

  const handleDelete = (id: string) => {
    if (confirmDelete === id) {
      onDelete(id);
      setConfirmDelete(null);
    } else {
      setConfirmDelete(id);
    }
  };

  return (
    <div className="bg-white rounded-lg border shadow-sm p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-semibold text-sm text-gray-800">Saved Cases</h2>
        <span className="text-[10px] text-gray-400 bg-gray-50 px-2 py-0.5 rounded">
          {cases.length} total
        </span>
      </div>

      <input
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search cases…"
        className="w-full border rounded-md px-2 py-1.5 text-sm mb-3"
      />

      <div className="max-h-[24rem] overflow-y-auto space-y-2">
        {filtered.length === 0 && (
          <p className="text-xs text-gray-400 italic py-2">
            {search ? "No matches" : "No saved cases yet — create one above"}
          </p>
        )}

        {filtered.map((c) => {
          const isActive = c.id === activeCaseId;
          return (
            <div
              key={c.id}
              className={`border rounded-md p-2.5 text-sm transition cursor-pointer ${
                isActive
                  ? "bg-blue-50 border-blue-200"
                  : "hover:bg-gray-50"
              }`}
              onClick={() => onLoad(c)}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[10px] text-gray-400">
                      {c.case_code}
                    </span>
                    {isActive && (
                      <span className="text-[10px] px-1 py-0.5 bg-blue-100 text-blue-700 rounded">
                        Active
                      </span>
                    )}
                  </div>
                  <p className="font-medium text-gray-800 truncate mt-0.5">
                    {c.chief_concern || "(no concern)"}
                  </p>
                  {c.patient_pseudonym && (
                    <p className="text-[10px] text-gray-400 mt-0.5">
                      {c.patient_pseudonym}
                    </p>
                  )}
                  <p className="text-[10px] text-gray-400 mt-0.5">
                    {new Date(c.created_at).toLocaleDateString()}
                  </p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(c.id);
                  }}
                  className={`text-[10px] px-1.5 py-0.5 rounded border shrink-0 ${
                    confirmDelete === c.id
                      ? "bg-red-100 text-red-700 border-red-200"
                      : "text-gray-400 hover:text-red-600 hover:bg-red-50 border-transparent"
                  }`}
                >
                  {confirmDelete === c.id ? "Confirm" : "×"}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
