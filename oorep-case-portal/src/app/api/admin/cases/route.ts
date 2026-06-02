import { NextResponse } from "next/server";
import { requireAdminSession } from "@/lib/adminAuth";
import { listCases, listCasesFiltered } from "@/lib/db";

export async function GET(request: Request) {
  const auth = requireAdminSession();
  if (!auth.ok) {
    const err = auth as unknown as { ok: false; status: number; message: string };
    return NextResponse.json({ ok: false, error: err.message }, { status: err.status });
  }

  try {
    const { searchParams } = new URL(request.url);
    const status = searchParams.get("status") || undefined;
    const cases = status ? listCasesFiltered(status as any) : listCases();
    return NextResponse.json({ ok: true, cases });
  } catch (err) {
    console.error("[GET /api/admin/cases]", err);
    return NextResponse.json({ ok: false, error: "Server error" }, { status: 500 });
  }
}
