import { NextResponse } from "next/server";
import { execFile } from "child_process";
import { promisify } from "util";
import * as path from "path";
import * as os from "os";

const execFileAsync = promisify(execFile);

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.get("q");
  if (!query) {
    return NextResponse.json({ ok: false, error: "q (query param) required" }, { status: 400 });
  }

  try {
    const repertoryDir = path.join(os.homedir(), "projects", "oorep-local-repertory", "oorep");
    const pythonScript = `
import json, sys, os
sys.path.insert(0, "${repertoryDir}")
from homeopathic_repertory import HomeopathicRepertory

query = sys.argv[1]
rep = HomeopathicRepertory()

results = rep.search_rubrics(query, limit=20)
out = []
for r in results:
    out.append({
        "id": r.get("id"),
        "fullpath": r.get("fullpath"),
        "source": r.get("source"),
        "match_score": r.get("_match_score"),
    })
print(json.dumps({"results": out}))
`;

    const { stdout } = await execFileAsync(
      "python3",
      ["-c", pythonScript, query],
      { cwd: repertoryDir, timeout: 15000, maxBuffer: 2 * 1024 * 1024 }
    );
    const data = JSON.parse(stdout.trim() || "{}") as { results: any[] };
    return NextResponse.json({ ok: true, results: data.results });
  } catch (err) {
    console.error("[GET /api/rubrics]", err);
    return NextResponse.json(
      { ok: false, error: err instanceof Error ? err.message : "Search failed" },
      { status: 500 }
    );
  }
}
