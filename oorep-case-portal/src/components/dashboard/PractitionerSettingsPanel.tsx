"use client";

import { useState } from "react";

export interface PractitionerSettings {
  default_enabled_module_ids?: string[];
  show_advanced_panels?: boolean;
  auto_run_on_save?: boolean;
  preferred_potency_ladder?: string[];
}

interface PractitionerSettingsPanelProps {
  settings: PractitionerSettings | null;
  onSave: (settings: PractitionerSettings) => void;
  modules: { id: string; name: string }[];
}

export default function PractitionerSettingsPanel({
  settings,
  onSave,
  modules,
}: PractitionerSettingsPanelProps) {
  const [form, setForm] = useState<PractitionerSettings>({
    default_enabled_module_ids: settings?.default_enabled_module_ids || [],
    show_advanced_panels: settings?.show_advanced_panels ?? true,
    auto_run_on_save: settings?.auto_run_on_save ?? false,
    preferred_potency_ladder: settings?.preferred_potency_ladder || ["6C", "12C", "30C", "200C"],
  });
  const [saved, setSaved] = useState(false);

  const toggleModule = (id: string) => {
    setForm((prev) => {
      const ids = new Set(prev.default_enabled_module_ids || []);
      if (ids.has(id)) ids.delete(id);
      else ids.add(id);
      return { ...prev, default_enabled_module_ids: Array.from(ids) };
    });
    setSaved(false);
  };

  const handleSave = () => {
    onSave(form);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const enabledIds = new Set(form.default_enabled_module_ids || []);

  return (
    <div className="bg-white rounded-lg border shadow-sm p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-semibold text-sm text-gray-800">Practitioner Settings</h2>
        {saved && (
          <span className="text-[10px] px-2 py-0.5 bg-green-100 text-green-700 rounded">
            Saved
          </span>
        )}
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Default Active Modules
          </label>
          <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto">
            {modules.map((m) => (
              <label
                key={m.id}
                className="flex items-center gap-2 text-xs p-1.5 rounded border cursor-pointer hover:bg-gray-50"
              >
                <input
                  type="checkbox"
                  checked={enabledIds.has(m.id)}
                  onChange={() => toggleModule(m.id)}
                />
                <span className="truncate">{m.name}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-xs cursor-pointer">
            <input
              type="checkbox"
              checked={form.show_advanced_panels ?? true}
              onChange={(e) => {
                setForm((p) => ({ ...p, show_advanced_panels: e.target.checked }));
                setSaved(false);
              }}
            />
            Show advanced panels
          </label>
          <label className="flex items-center gap-2 text-xs cursor-pointer">
            <input
              type="checkbox"
              checked={form.auto_run_on_save ?? false}
              onChange={(e) => {
                setForm((p) => ({ ...p, auto_run_on_save: e.target.checked }));
                setSaved(false);
              }}
            />
            Auto-run on case save
          </label>
        </div>

        <div>
          <label className="block text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-1">
            Preferred Potency Ladder
          </label>
          <input
            type="text"
            value={(form.preferred_potency_ladder || []).join(", ")}
            onChange={(e) => {
              const vals = e.target.value.split(",").map((s) => s.trim()).filter(Boolean);
              setForm((p) => ({ ...p, preferred_potency_ladder: vals }));
              setSaved(false);
            }}
            className="w-full border rounded-md px-2 py-1.5 text-sm"
          />
        </div>

        <button
          onClick={handleSave}
          className="px-3 py-2 bg-blue-600 text-white text-xs font-medium rounded-md hover:bg-blue-700 transition"
        >
          Save Settings
        </button>
      </div>
    </div>
  );
}
