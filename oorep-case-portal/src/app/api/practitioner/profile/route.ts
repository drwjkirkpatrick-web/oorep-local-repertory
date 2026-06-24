import { NextResponse } from "next/server";
import { getPractitionerProfile, savePractitionerProfile } from "@/lib/db";

export async function GET() {
  try {
    const profile = getPractitionerProfile();
    if (!profile) {
      return NextResponse.json({ ok: true, profile: null });
    }
    return NextResponse.json({ ok: true, profile });
  } catch (err) {
    console.error("[GET /api/practitioner/profile]", err);
    return NextResponse.json({ ok: false, error: "Server error" }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { name, email, clinic, license_number, default_potency, default_repertory_method } = body;

    if (!name || !name.trim()) {
      return NextResponse.json({ ok: false, error: "Name required" }, { status: 400 });
    }
    if (!email || !email.trim()) {
      return NextResponse.json({ ok: false, error: "Email required" }, { status: 400 });
    }

    const profile = savePractitionerProfile({
      name: name.trim(),
      email: email.trim(),
      clinic: (clinic || "").trim() || null,
      license_number: (license_number || "").trim() || null,
      default_potency: (default_potency || "").trim() || null,
      default_repertory_method: (default_repertory_method || "").trim() || null,
    });

    return NextResponse.json({ ok: true, profile });
  } catch (err) {
    console.error("[POST /api/practitioner/profile]", err);
    return NextResponse.json({ ok: false, error: "Server error" }, { status: 500 });
  }
}

export async function PATCH(request: Request) {
  try {
    const body = await request.json();
    const existing = getPractitionerProfile();
    if (!existing) {
      return NextResponse.json({ ok: false, error: "Profile not found" }, { status: 404 });
    }
    const profile = savePractitionerProfile({ ...existing, ...body });
    return NextResponse.json({ ok: true, profile });
  } catch (err) {
    console.error("[PATCH /api/practitioner/profile]", err);
    return NextResponse.json({ ok: false, error: "Server error" }, { status: 500 });
  }
}
