import { NextResponse } from "next/server";
import {
  getPractitionerCaseById,
  updatePractitionerCase,
  deletePractitionerCase,
} from "@/lib/db";

export async function GET(
  _request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const doc = getPractitionerCaseById(params.id);
    if (!doc) {
      return NextResponse.json({ ok: false, error: "Not found" }, { status: 404 });
    }
    return NextResponse.json({ ok: true, case: doc });
  } catch (err) {
    console.error("[GET /api/practitioner/cases/:id]", err);
    return NextResponse.json({ ok: false, error: "Server error" }, { status: 500 });
  }
}

export async function PATCH(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const body = await request.json();
    const doc = updatePractitionerCase(params.id, body);
    if (!doc) {
      return NextResponse.json({ ok: false, error: "Not found" }, { status: 404 });
    }
    return NextResponse.json({ ok: true, case: doc });
  } catch (err) {
    console.error("[PATCH /api/practitioner/cases/:id]", err);
    return NextResponse.json({ ok: false, error: "Server error" }, { status: 500 });
  }
}

export async function DELETE(
  _request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const ok = deletePractitionerCase(params.id);
    if (!ok) {
      return NextResponse.json({ ok: false, error: "Not found" }, { status: 404 });
    }
    return NextResponse.json({ ok: true });
  } catch (err) {
    console.error("[DELETE /api/practitioner/cases/:id]", err);
    return NextResponse.json({ ok: false, error: "Server error" }, { status: 500 });
  }
}
