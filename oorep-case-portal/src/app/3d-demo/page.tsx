"use client";

import React from "react";
import ConcordanceCube from "@/components/visualizations/ConcordanceCube";
import RemedyLandscape from "@/components/visualizations/RemedyLandscape";
import ConfidenceCloud from "@/components/visualizations/ConfidenceCloud";
import SymptomConstellation from "@/components/visualizations/SymptomConstellation";
import DifferentialHelix from "@/components/visualizations/DifferentialHelix";
import RubricHierarchyTower from "@/components/visualizations/RubricHierarchyTower";

const DEMO_REMEDIES = [
  { abbrev: "Puls.", name: "Pulsatilla", score: 28, cycle_analysis: { segment_coverage: 0.72, meets_threshold: true }, srp_density: 0.65, outcome_rate: 0.82 },
  { abbrev: "Ars.", name: "Arsenicum", score: 24, cycle_analysis: { segment_coverage: 0.58, meets_threshold: true }, srp_density: 0.78, outcome_rate: 0.76 },
  { abbrev: "Sep.", name: "Sepia", score: 19, cycle_analysis: { segment_coverage: 0.61, meets_threshold: false }, srp_density: 0.42, outcome_rate: 0.68 },
  { abbrev: "Sulph.", name: "Sulphur", score: 17, cycle_analysis: { segment_coverage: 0.45, meets_threshold: false }, srp_density: 0.55, outcome_rate: 0.71 },
  { abbrev: "Lyc.", name: "Lycopodium", score: 14, cycle_analysis: { segment_coverage: 0.38, meets_threshold: false }, srp_density: 0.33, outcome_rate: 0.64 },
  { abbrev: "Nat-m.", name: "Natrum-mur", score: 12, cycle_analysis: { segment_coverage: 0.52, meets_threshold: true }, srp_density: 0.48, outcome_rate: 0.59 },
  { abbrev: "Calc.", name: "Calcarea", score: 10, cycle_analysis: { segment_coverage: 0.30, meets_threshold: false }, srp_density: 0.28, outcome_rate: 0.55 },
  { abbrev: "Nux-v.", name: "Nux-vomica", score: 8, cycle_analysis: { segment_coverage: 0.41, meets_threshold: false }, srp_density: 0.40, outcome_rate: 0.52 },
];

export default function Page() {
  return (
    <div className="min-h-screen bg-gray-100 p-8 space-y-16">
      <h1 className="text-3xl font-bold text-center mb-8">OOREP 3D Visualization Panels</h1>

      <section id="symptom-constellation">
        <h2 className="text-xl font-semibold mb-4 text-center">1. Symptom Constellation</h2>
        <div className="bg-white rounded-xl shadow p-4 max-w-4xl mx-auto">
          <SymptomConstellation remedies={DEMO_REMEDIES} />
        </div>
      </section>

      <section id="rubric-hierarchy">
        <h2 className="text-xl font-semibold mb-4 text-center">2. Rubric Hierarchy Tower</h2>
        <div className="bg-white rounded-xl shadow p-4 max-w-4xl mx-auto">
          <RubricHierarchyTower remedies={DEMO_REMEDIES} />
        </div>
      </section>

      <section id="remedy-landscape">
        <h2 className="text-xl font-semibold mb-4 text-center">3. Remedy Landscape</h2>
        <div className="bg-white rounded-xl shadow p-4 max-w-4xl mx-auto">
          <RemedyLandscape remedies={DEMO_REMEDIES} />
        </div>
      </section>

      <section id="confidence-cloud">
        <h2 className="text-xl font-semibold mb-4 text-center">4. Confidence Cloud</h2>
        <div className="bg-white rounded-xl shadow p-4 max-w-4xl mx-auto">
          <ConfidenceCloud remedies={DEMO_REMEDIES} />
        </div>
      </section>

      <section id="differential-helix">
        <h2 className="text-xl font-semibold mb-4 text-center">5. Differential Helix</h2>
        <div className="bg-white rounded-xl shadow p-4 max-w-4xl mx-auto">
          <DifferentialHelix remedies={DEMO_REMEDIES} />
        </div>
      </section>

      <section id="concordance-cube">
        <h2 className="text-xl font-semibold mb-4 text-center">6. Concordance Cube</h2>
        <div className="bg-white rounded-xl shadow p-4 max-w-4xl mx-auto">
          <ConcordanceCube remedies={DEMO_REMEDIES} />
        </div>
      </section>
    </div>
  );
}
