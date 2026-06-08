"use client";

import { useMemo } from "react";

/**
 * Kingdom Morphology Cloud — INTERMEDIATE
 *
 * Word-cloud-style tag cloud per kingdom.
 */

const KINGDOM_WORDS: Record<string, { word: string; size: number }[]> = {
  Plant: [
    { word: "sensitive", size: 28 }, { word: "adapting", size: 24 }, { word: "growing", size: 22 },
    { word: "bending", size: 18 }, { word: "flowering", size: 16 }, { word: "wilting", size: 14 },
    { word: "seeds", size: 12 }, { word: "roots", size: 12 }, { word: "sunlight", size: 10 },
  ],
  Mineral: [
    { word: "structure", size: 26 }, { word: "order", size: 24 }, { word: "rigidity", size: 22 },
    { word: "pressure", size: 18 }, { word: "weight", size: 16 }, { word: "bonds", size: 14 },
    { word: "crystalline", size: 12 }, { word: "density", size: 10 },
  ],
  Animal: [
    { word: "survival", size: 26 }, { word: "predator", size: 24 }, { word: "competition", size: 22 },
    { word: "instinct", size: 20 }, { word: "territory", size: 18 }, { word: "hierarchy", size: 16 },
    { word: "chase", size: 14 }, { word: "prey", size: 12 }, { word: "pack", size: 10 },
  ],
};

const KINGDOM_COLORS: Record<string, string> = {
  Plant: "#16a34a",
  Mineral: "#6b7280",
  Animal: "#be123c",
};

export default function KingdomMorphologyCloud({
  kingdom,
}: {
  kingdom?: "Plant" | "Mineral" | "Animal";
}) {
  const data = useMemo(() => {
    const target = kingdom || "Plant";
    return KINGDOM_WORDS[target] || KINGDOM_WORDS["Plant"];
  }, [kingdom]);

  const color = KINGDOM_COLORS[kingdom || "Plant"];

  return (
    <div className="flex flex-col items-center">
      <p className="text-xs text-slate-500 italic leading-relaxed text-center max-w-md">
        See which homeopathic kingdom (Plant, Mineral, or Animal) the patient's case language most closely matches. The word cloud uses Sankaran's kingdom vocabulary — Plant themes (sensitive, adapting, growing), Mineral themes (structure, order, rigidity), Animal themes (survival, predator, territory). Larger words = stronger theme affinity, helping choose between kingdom-based remedies.
      </p>
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded">INTERMEDIATE</span>
        <span className="text-xs text-gray-500">Case-language kingdom affinity</span>
      </div>

      <div className="flex flex-wrap justify-center gap-x-3 gap-y-1 max-w-[280px] bg-gray-50 rounded-lg p-3">
        {data.map((w, i) => (
          <span
            key={i}
            className="inline-block leading-tight"
            style={{
              fontSize: w.size,
              color: i < 3 ? color : `${color}99`,
              fontWeight: i < 3 ? 700 : 400,
            }}
          >
            {w.word}
          </span>
        ))}
      </div>

      <div className="flex gap-2 mt-2">
        {Object.keys(KINGDOM_COLORS).map((k) => (
          <button
            key={k}
            className={`text-[10px] px-2 py-0.5 rounded border transition ${
              (kingdom || "Plant") === k
                ? "bg-gray-800 text-white"
                : "bg-white text-gray-600 hover:bg-gray-50"
            }`}
          >
            {k}
          </button>
        ))}
      </div>
    </div>
  );
}
