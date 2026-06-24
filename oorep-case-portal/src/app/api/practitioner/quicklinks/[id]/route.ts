import { NextResponse } from "next/server";
import { updateQuickLink, deleteQuickLink } from "@/lib/db";

export async function PATCH(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const body = await request.json();
    const quicklink = updateQuickLink(params.id, body);
    if (!quicklink) {
      return NextResponse.json({ ok: false, error: "Not found" }, { status: 404 });
    }
    return NextResponse.json({ ok: true, quicklink });
  } catch (err) {
    console.error("[PATCH /api/practitioner/quicklinks/:id]", err);
    return NextResponse.json({ ok: false, error: "Server error" }, { status: 500 });
  }
}

export async function DELETE(
  _request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const ok = deleteQuickLink(params.id);
    if (!ok) {
      return NextResponse.json({ ok: false, error: "Not found" }, { status: 404 });
    }
    return NextResponse.json({ ok: true });
  } catch (err) {
    console.error("[DELETE /api/practitioner/quicklinks/:id]", err);
    return NextResponse.json({ ok: false, error: "Server error" }, { status: 500 });
  }
}
