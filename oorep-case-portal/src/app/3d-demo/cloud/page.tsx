"use client";

import React from "react";
import ConfidenceCloud from "@/components/visualizations/ConfidenceCloud";

const DEMO_REMEDIES = [
  { abbrev: "Puls.", name: "Pulsatilla", score: 28, cycle_analysis: { segment_coverage: 0.72, meets_threshold: true }, srp_density: 0.65, outcome_rate: 0.82, matches: [{rubric:"Mind; weeping",weight:4,grade:3},{rubric:"Generals; warm-blooded",weight:3,grade:2},{rubric:"Stomach; thirstless",weight:3,grade:2}] },
  { abbrev: "Ars.", name: "Arsenicum", score: 24, cycle_analysis: { segment_coverage: 0.58, meets_threshold: true }, srp_density: 0.78, outcome_rate: 0.76, matches: [{rubric:"Mind; anxiety",weight:4,grade:3},{rubric:"Generals; chilly",weight:3,grade:2},{rubric:"Sleep; restless",weight:2,grade:1}] },
  { abbrev: "Sep.", name: "Sepia", score: 19, cycle_analysis: { segment_coverage: 0.61, meets_threshold: false }, srp_density: 0.42, outcome_rate: 0.68, matches: [{rubric:"Mind; indifference",weight:3,grade:2},{rubric:"Female; bearing down",weight:4,grade:3}] },
  { abbrev: "Sulph.", name: "Sulphur", score: 17, cycle_analysis: { segment_coverage: 0.45, meets_threshold: false }, srp_density: 0.55, outcome_rate: 0.71, matches: [{rubric:"Skin; itching",weight:3,grade:2},{rubric:"Generals; hot",weight:3,grade:2}] },
  { abbrev: "Lyc.", name: "Lycopodium", score: 14, cycle_analysis: { segment_coverage: 0.38, meets_threshold: false }, srp_density: 0.33, outcome_rate: 0.64, matches: [{rubric:"Mind; anticipatory anxiety",weight:3,grade:2},{rubric:"Digestion; bloating",weight:2,grade:1}] },
  { abbrev: "Nat-m.", name: "Natrum-mur", score: 12, cycle_analysis: { segment_coverage: 0.52, meets_threshold: true }, srp_density: 0.48, outcome_rate: 0.59, matches: [{rubric:"Mind; grief",weight:4,grade:3},{rubric:"Generals; crave salt",weight:3,grade:2}] },
  { abbrev: "Calc.", name: "Calcarea", score: 10, cycle_analysis: { segment_coverage: 0.30, meets_threshold: false }, srp_density: 0.28, outcome_rate: 0.55, matches: [{rubric:"Mind; fear of disease",weight:2,grade:1},{rubric:"Generals; chilly",weight:2,grade:1}] },
  { abbrev: "Nux-v.", name: "Nux-vomica", score: 8, cycle_analysis: { segment_coverage: 0.41, meets_threshold: false }, srp_density: 0.40, outcome_rate: 0.52, matches: [{rubric:"Mind; irritability",weight:3,grade:2},{rubric:"Digestion; dyspepsia",weight:2,grade:1}] },
];

export default function Page() {
  return (
    <div className="min-h-screen bg-gray-900 p-4 flex items-center justify-center">
      <div className="w-full max-w-5xl">
        <ConfidenceCloud remedies={DEMO_REMEDIES} />
      </div>
    </div>
  );
}
