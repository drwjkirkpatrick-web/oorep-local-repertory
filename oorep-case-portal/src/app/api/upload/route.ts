import { NextResponse } from "next/server";
import { existsSync, mkdirSync, writeFileSync } from "fs";
import path from "path";
import os from "os";
import { getCaseByCode, FILES_DIR } from "@/lib/db";

export async function POST(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const caseCode = searchParams.get("case_code");

    let caseDoc = null;
    if (caseCode) {
      caseDoc = getCaseByCode(caseCode);
      if (!caseDoc) {
        return NextResponse.json({ ok: false, error: "Case not found" }, { status: 404 });
      }
    }

    const form = await request.formData();
    const files = form.getAll("file") as File[];
    if (!files || files.length === 0) {
      return NextResponse.json({ ok: false, error: "No files" }, { status: 400 });
    }

    const uploaded: { name: string; relative_path: string; type: string; size: number }[] = [];

    for (const file of files) {
      const safeName = file.name.replace(/[^a-zA-Z0-9._-]/g, "_").slice(0, 120);
      const subdir = caseCode || "practitioner-uploads";
      const relative = path.join(subdir, `${Date.now()}_${safeName}`);
      const outPath = path.join(FILES_DIR, relative);
      mkdirSync(path.dirname(outPath), { recursive: true });
      const buffer = Buffer.from(await file.arrayBuffer());
      writeFileSync(outPath, buffer);
      uploaded.push({ name: file.name, relative_path: relative, type: file.type || "application/octet-stream", size: file.size });
    }

    if (caseDoc && caseDoc.id) {
      const { updateCase } = await import("@/lib/db");
      updateCase(caseDoc.id, { files: [...(caseDoc.files || []), ...uploaded] });
    }

    return NextResponse.json({ ok: true, files: uploaded });
  } catch (err) {
    console.error("[POST /api/upload]", err);
    return NextResponse.json({ ok: false, error: "Server error" }, { status: 500 });
  }
}
