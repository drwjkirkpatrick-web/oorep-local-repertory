import { NextResponse } from "next/server";
import { execFile } from "child_process";
import { promisify } from "util";
import * as path from "path";
import * as os from "os";

const execFileAsync = promisify(execFile);

export async function GET(request: Request, { params }: { params: { abbrev: string } }) {
  const { abbrev } = params;
  if (!abbrev) {
    return NextResponse.json({ ok: false, error: "abbrev required" }, { status: 400 });
  }

  try {
    const repertoryDir = path.join(os.homedir(), "projects", "oorep-local-repertory", "oorep");
    const pythonScript = `
import json, sys, os
sys.path.insert(0, "${repertoryDir}")
from homeopathic_repertory import HomeopathicRepertory

abbrev = sys.argv[1]
rep = HomeopathicRepertory()

remedy = rep.get_remedy_by_abbrev(abbrev)
if not remedy:
    print(json.dumps({"error": "Not found"}))
    sys.exit(0)

print(json.dumps({"remedy": remedy}))
`;

    const { stdout } = await execFileAsync(
      "python3",
      ["-c", pythonScript, abbrev],
      { cwd: repertoryDir, timeout: 15000, maxBuffer: 2 * 1024 * 1024 }
    );
    const data = JSON.parse(stdout.trim() || "{}");
    if (data.error) {
      return NextResponse.json({ ok: false, error: data.error }, { status: 404 });
    }
    return NextResponse.json({ ok: true, ...data });
  } catch (err) {
    console.error("[GET /api/remedies/:abbrev]", err);
    return NextResponse.json(
      { ok: false, error: err instanceof Error ? err.message : "Remedy fetch failed" },
      { status: 500 }
    );
  }
}
