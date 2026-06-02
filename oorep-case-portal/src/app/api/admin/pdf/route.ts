import { NextResponse } from "next/server";
import { execFile } from "child_process";
import { promisify } from "util";
import * as path from "path";
import * as os from "os";
import { readFileSync, existsSync } from "fs";
import { requireAdminSession } from "@/lib/adminAuth";
import { getCaseById, updateCase, PDFS_DIR } from "@/lib/db";

const execFileAsync = promisify(execFile);

export async function POST(request: Request) {
  const auth = requireAdminSession();
  if (!auth.ok) {
    const err = auth as unknown as { ok: false; status: number; message: string };
    return NextResponse.json({ ok: false, error: err.message }, { status: err.status });
  }

  try {
    const body = await request.json();
    const { case_id, mode } = body as { case_id: string; mode: "draft" | "final" };
    if (!case_id) {
      return NextResponse.json(
        { ok: false, error: "case_id required" },
        { status: 400 }
      );
    }

    const doc = getCaseById(case_id);
    if (!doc) {
      return NextResponse.json({ ok: false, error: "Case not found" }, { status: 404 });
    }

    const stamp = new Date().toISOString().replace(/[:.]/g, "-");
    const pdfName = `${doc.case_code}-${mode}-${stamp}.pdf`;
    const pdfPath = path.join(PDFS_DIR, pdfName);

    const home = os.homedir();
    const repertoryPath = path.join(
      home,
      ".hermes",
      "skills",
      "clinic",
      "homeopathic-repertory-oorep",
      "references",
      "homeopathic_repertory.py"
    );

    const repResult = doc.repertory_result || [];

    const pythonScript = `
import json, sys, os, datetime
repertory_path = sys.argv[1]
pdf_path = sys.argv[2]
meta_json = sys.argv[3]

meta = json.loads(meta_json)

from pathlib import Path
OUT = Path(pdf_path)
OUT.parent.mkdir(parents=True, exist_ok=True)

try:
    from fpdf import FPDF
except ImportError:
    os.system("uv pip install fpdf2")
    from fpdf import FPDF

FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

if not os.path.exists(FONT_REG):
    FONT_REG = None
    FONT_BOLD = None

pdf = FPDF(format="Letter")
pdf.set_margins(15, 15, 15)
pdf.set_auto_page_break(auto=True, margin=15)
if FONT_REG:
    pdf.add_font("DejaVu", "", FONT_REG)
    pdf.add_font("DejaVu", "B", FONT_BOLD)
    pdf.set_font("DejaVu", size=10)
else:
    pdf.set_font("Helvetica", size=10)

# Header
pdf.add_page()
if FONT_BOLD:
    pdf.set_font("DejaVu", "B", 16)
else:
    pdf.set_font("Helvetica", "B", 16)
pdf.cell(0, 10, "OORep Case Review", ln=True, align="C")
if FONT_BOLD:
    pdf.set_font("DejaVu", "", 10)
else:
    pdf.set_font("Helvetica", size=10)
pdf.cell(0, 6, f"Case: {meta.get('case_code')}", ln=True)
pdf.cell(0,6, f"Date: {datetime.datetime.utcnow().isoformat(timespec='minutes')}Z", ln=True)
pdf.cell(0,6, f"Practitioner: {meta.get('practitioner_email','')}", ln=True)
pdf.ln(4)

# Chief concern
if FONT_BOLD:
    pdf.set_font("DejaVu", "B", 12)
else:
    pdf.set_font("Helvetica", "B", 12)
pdf.cell(0, 8, "Chief Concern:", ln=True)
if FONT_REG:
    pdf.set_font("DejaVu", "", 10)
else:
    pdf.set_font("Helvetica", size=10)
for line in (meta.get('chief_concern') or '(not provided)').split('\\n'):
    pdf.multi_cell(pdf.epw, 5, line, new_x="LMARGIN", new_y="NEXT")
pdf.ln(4)

# Modalities
if FONT_BOLD:
    pdf.set_font("DejaVu", "B", 12)
else:
    pdf.set_font("Helvetica", "B", 12)
pdf.cell(0, 8, "Modalities / Notes:", ln=True)
if FONT_REG:
    pdf.set_font("DejaVu", "", 10)
else:
    pdf.set_font("Helvetica", size=10)
for line in (meta.get('modalities') or '(not provided)').split('\\n'):
    pdf.multi_cell(pdf.epw, 5, line, new_x="LMARGIN", new_y="NEXT")
pdf.ln(4)

# Case body
if meta.get('body'):
    if FONT_BOLD:
        pdf.set_font("DejaVu", "B", 12)
    else:
        pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Case Details:", ln=True)
    if FONT_REG:
        pdf.set_font("DejaVu", "", 10)
    else:
        pdf.set_font("Helvetica", size=10)
    for line in meta.get('body','').split('\\n'):
        pdf.multi_cell(pdf.epw, 5, line, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

# Repertorization results
rep = meta.get('repertory_result', [] )
if rep:
    if FONT_BOLD:
        pdf.set_font("DejaVu", "B", 12)
    else:
        pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Repertorization Results:", ln=True)
    if FONT_REG:
        pdf.set_font("DejaVu", "", 10)
    else:
        pdf.set_font("Helvetica", size=10)
    pdf.cell(pdf.epw * 0.15, 6, "Rank", border=0)
    pdf.cell(pdf.epw * 0.25, 6, "Abbrev", border=0)
    pdf.cell(pdf.epw * 0.40, 6, "Remedy Name", border=0)
    pdf.cell(pdf.epw * 0.20, 6, "Score", border=0, ln=True)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(1)
    for idx, r in enumerate(rep[:20], start=1):
        pdf.cell(pdf.epw * 0.15, 5, str(idx))
        pdf.cell(pdf.epw * 0.25, 5, str(r.get('abbrev','')))
        pdf.cell(pdf.epw * 0.40, 5, str(r.get('name','')))
        pdf.cell(pdf.epw * 0.20, 5, str(r.get('score','')), ln=True)
    pdf.ln(4)

# Disclaimer
pdf.set_text_color(120,120,120)
if FONT_REG:
    pdf.set_font("DejaVu", "", 8)
else:
    pdf.set_font("Helvetica", size=8)
pdf.multi_cell(pdf.epw, 4,
"This document is a non-diagnostic repertory analysis. It does not constitute medical advice. "
"The prescribing practitioner is solely responsible for diagnosis, remedy selection, and patient care. "
"All case data has been anonymized/submitted for repertory pattern-matching only.",
new_x="LMARGIN", new_y="NEXT")
pdf.set_text_color(0,0,0)

pdf.output(str(OUT))
print(str(OUT))
`;

    const meta = {
      case_code: doc.case_code,
      practitioner_email: doc.practitioner_email,
      practitioner_name: doc.practitioner_name,
      chief_concern: doc.chief_concern,
      modalities: doc.modalities,
      body: doc.body,
      repertory_result: repResult,
    };

    const { stdout } = await execFileAsync(
      "python3",
      ["-c", pythonScript, repertoryPath, pdfPath, JSON.stringify(meta)],
      { timeout: 60000, maxBuffer: 2 * 1024 * 1024 }
    );

    const generatedPath = stdout.trim();

    if (mode === "draft") {
      updateCase(case_id, { status: "draft_ready", draft_pdf_path: generatedPath });
    } else {
      updateCase(case_id, {
        status: "approved",
        final_pdf_path: generatedPath,
      });
    }

    return NextResponse.json({ ok: true, pdf_path: generatedPath, pdf_name: pdfName });
  } catch (err) {
    console.error("[POST /api/admin/pdf]", err);
    return NextResponse.json(
      { ok: false, error: err instanceof Error ? err.message : "PDF generation failed" },
      { status: 500 }
    );
  }
}
