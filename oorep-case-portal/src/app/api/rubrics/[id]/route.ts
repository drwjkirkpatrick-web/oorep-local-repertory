import { NextResponse } from "next/server";
import { execFile } from "child_process";
import { promisify } from "util";
import * as path from "path";
import * as os from "os";

const execFileAsync = promisify(execFile);

export async function GET(request: Request, { params }: { params: { id: string } }) {
  const { id } = params;
  if (!id) {
    return NextResponse.json({ ok: false, error: "rubric_id required" }, { status: 400 });
  }

  try {
    const repertoryDir = path.join(os.homedir(), "projects", "oorep-local-repertory", "oorep");
    const pythonScript = `
import json, sys, os
sys.path.insert(0, "${repertoryDir}")
from homeopathic_repertory import HomeopathicRepertory

rubric_id = int(sys.argv[1])
rep = HomeopathicRepertory()

remedies = rep.get_remedies_for_rubric(rubric_id)
rubric = rep.get_rubric_by_id(rubric_id)

print(json.dumps({
    "rubric": rubric,
    "remedies": remedies[:50]  # cap at 50 for bandwidth
}))
`;

    const { stdout } = await execFileAsync(
      "python3",
      ["-c", pythonScript, id],
      { cwd: repertoryDir, timeout: 15000, maxBuffer: 2 * 1024 * 1024 }
    );
    const data = JSON.parse(stdout.trim() || "{}");
    return NextResponse.json({ ok: true, ...data });
  } catch (err) {
    console.error("[GET /api/rubrics/:id]", err);
    return NextResponse.json(
      { ok: false, error: err instanceof Error ? err.message : "Rubric fetch failed" },
      { status: 500 }
    );
  }
}
