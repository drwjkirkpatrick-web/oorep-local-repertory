import { NextResponse } from "next/server";
import { execFile } from "child_process";
import { promisify } from "util";
import * as path from "path";
import * as os from "os";
import { requireAdminSession } from "@/lib/adminAuth";
import { getCaseById, updateCase } from "@/lib/db";

const execFileAsync = promisify(execFile);

export async function POST(request: Request) {
  const auth = requireAdminSession();
  if (!auth.ok) {
    const err = auth as { ok: false; status: number; message: string };
    return NextResponse.json({ ok: false, error: err.message }, { status: err.status });
  }

  try {
    const body = await request.json();
    const { case_id, symptoms } = body;
    if (!case_id || !symptoms || !Array.isArray(symptoms)) {
      return NextResponse.json(
        { ok: false, error: "case_id and symptoms array required" },
        { status: 400 }
      );
    }

    const doc = getCaseById(case_id);
    if (!doc) {
      return NextResponse.json({ ok: false, error: "Case not found" }, { status: 404 });
    }

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

    const pythonScript = `
import json
import sys
import os
repertory_path = sys.argv[1]
symptoms_json = sys.argv[2]
sys.path.insert(0, os.path.dirname(repertory_path))
from homeopathic_repertory import HomeopathicRepertory

symptoms = json.loads(symptoms_json)
rep = HomeopathicRepertory()
result = rep.repertorize(
    symptoms,
    top_n=20,
    retrieval="hybrid",
    rubrics_per_symptom=10
)
print(json.dumps({"repertorization": result}))
`;

    const { stdout } = await execFileAsync(
      "python3",
      ["-c", pythonScript, repertoryPath, JSON.stringify(symptoms)],
      { timeout: 60000, maxBuffer: 2 * 1024 * 1024 }
    );

    const data = JSON.parse(stdout.trim() || "{}") as {
      repertorization?: Array<{
        abbrev: string;
        name: string;
        score: number;
        match_count: number;
      }>;
    };

    const updated = updateCase(case_id, {
      status: "reviewing",
      repertory_result: data.repertorization || [],
      reviewed_at: new Date().toISOString(),
    });

    return NextResponse.json({ ok: true, result: data.repertorization || [], case: updated });
  } catch (err) {
    console.error("[POST /api/admin/repertorize]", err);
    return NextResponse.json(
      { ok: false, error: err instanceof Error ? err.message : "Repertorization failed" },
      { status: 500 }
    );
  }
}
