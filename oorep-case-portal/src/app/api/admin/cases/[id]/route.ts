import { NextResponse } from "next/server";
import { requireAdminSession } from "@/lib/adminAuth";
import { getCaseById, updateCase } from "@/lib/db";

export async function GET(
  _request: Request,
  { params }: { params: { id: string } }
) {
  const auth = requireAdminSession();
  if (!auth.ok) {
    const err = auth as unknown as { ok: false; status: number; message: string };
    return NextResponse.json({ ok: false, error: err.message }, { status: err.status });
  }

  try {
    const doc = getCaseById(params.id);
    if (!doc) return NextResponse.json({ ok: false, error: "Not found" }, { status: 404 });
    return NextResponse.json({ ok: true, case: doc });
  } catch (err) {
    console.error("[GET /api/admin/case]", err);
    return NextResponse.json({ ok: false, error: "Server error" }, { status: 500 });
  }
}

export async function PATCH(
  request: Request,
  { params }: { params: { id: string } }
) {
  const auth = requireAdminSession();
  if (!auth.ok) {
    const err = auth as unknown as { ok: false; status: number; message: string };
    return NextResponse.json({ ok: false, error: err.message }, { status: err.status });
  }

  try {
    const body = await request.json();
    const doc = updateCase(params.id, body);
    if (!doc) return NextResponse.json({ ok: false, error: "Not found" }, { status: 404 });
    return NextResponse.json({ ok: true, case: doc });
  } catch (err) {
    console.error("[PATCH /api/admin/case]", err);
    return NextResponse.json({ ok: false, error: "Server error" }, { status: 500 });
  }
}
