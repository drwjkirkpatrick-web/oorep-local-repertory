"use client";

import { useState } from "react";

export interface QuickLink {
  id: string;
  label: string;
  url: string;
}

interface QuickLinksPanelProps {
  links: QuickLink[];
  onAdd: (link: Omit<QuickLink, "id">) => void;
  onDelete: (id: string) => void;
}

export default function QuickLinksPanel({ links, onAdd, onDelete }: QuickLinksPanelProps) {
  const [label, setLabel] = useState("");
  const [url, setUrl] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleAdd = () => {
    if (!label.trim() || !url.trim()) {
      setError("Label and URL are required");
      return;
    }
    try {
      new URL(url);
    } catch {
      setError("Please enter a valid URL");
      return;
    }
    onAdd({ label: label.trim(), url: url.trim() });
    setLabel("");
    setUrl("");
    setError(null);
  };

  return (
    <div className="bg-white rounded-lg border shadow-sm p-4">
      <h2 className="font-semibold text-sm text-gray-800 mb-3">Quick Links</h2>

      {error && (
        <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
          {error}
        </div>
      )}

      <div className="flex gap-2 mb-4">
        <input
          type="text"
          placeholder="Label (e.g. Kent Repertory)"
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          className="flex-1 border rounded-md px-2 py-1.5 text-sm"
        />
        <input
          type="text"
          placeholder="URL"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          className="flex-[2] border rounded-md px-2 py-1.5 text-sm"
        />
        <button
          onClick={handleAdd}
          className="px-3 py-1.5 bg-blue-600 text-white text-xs font-medium rounded-md hover:bg-blue-700 transition"
        >
          Add
        </button>
      </div>

      <div className="space-y-2">
        {links.length === 0 && (
          <p className="text-xs text-gray-400 italic">No quick links yet — add one above</p>
        )}
        {links.map((link) => (
          <div
            key={link.id}
            className="flex items-center justify-between gap-2 p-2 border rounded-md hover:bg-gray-50"
          >
            <a
              href={link.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-blue-600 hover:underline truncate"
            >
              {link.label}
            </a>
            <button
              onClick={() => onDelete(link.id)}
              className="text-[10px] text-gray-400 hover:text-red-600 px-1.5 py-0.5 rounded hover:bg-red-50 transition shrink-0"
            >
              ×
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
