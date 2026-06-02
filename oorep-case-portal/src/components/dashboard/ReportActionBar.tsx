"use client";

import type { PortalModule, ModuleResult } from "../../lib/portal-types";

export default function ReportActionBar({
  modules,
  results,
}: {
  modules: PortalModule[];
  results: Record<string, ModuleResult>;
}) {
  const includedResults = Object.entries(results).filter(
    ([, r]) => r?.includeInReport && r?.status === "success"
  );

  const generateMarkdownReport = () => {
    const lines: string[] = [
      "# OOREP Clinical Analysis Report",
      `Generated: ${new Date().toISOString()}`,
      "",
      "---",
      "",
    ];

    for (const [modId, r] of includedResults) {
      const mod = modules.find((m) => m.id === modId);
      lines.push(`## ${mod?.name || modId}`);
      lines.push(`**Benefit:** #${mod?.benefit || "N/A"}`);
      lines.push("");
      lines.push("```json");
      lines.push(JSON.stringify(r.data, null, 2));
      lines.push("```");
      lines.push("");
    }

    lines.push("---");
    lines.push("");
    lines.push(
      "*Disclaimer: This report is for educational and reference purposes only and does not constitute a diagnosis or prescription. All remedy recommendations require practitioner review and prescriber_ack.*"
    );

    return lines.join("\n");
  };

  const downloadReport = () => {
    const md = generateMarkdownReport();
    const blob = new Blob([md], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `oorep-report-${Date.now()}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-white border-t p-3 flex items-center justify-between shrink-0">
      <div className="flex items-center gap-4">
        <span className="text-sm text-gray-500">
          {includedResults.length} /{" "}
          {Object.keys(results).filter(
            (k) => results[k]?.status === "success"
          ).length}{" "}
          modules included in report
        </span>
      </div>
      <div className="flex gap-3">
        <button
          onClick={downloadReport}
          className="px-4 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 transition"
        >
          Download Report (.md)
        </button>
        <button
          onClick={() => alert("PDF generation requires server-side rendering.")}
          className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition"
        >
          Generate PDF
        </button>
      </div>
    </div>
  );
}
