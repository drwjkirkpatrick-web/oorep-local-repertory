import { NextResponse } from "next/server";
import { listPractitionerCases, createPractitionerCase } from "@/lib/db";

export async function GET() {
  try {
    const cases = listPractitionerCases();
    return NextResponse.json({ ok: true, cases });
  } catch (err) {
    console.error("[GET /api/practitioner/cases]", err);
    return NextResponse.json({ ok: false, error: "Server error" }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { patient_pseudonym, chief_concern, modalities, body: caseBody } = body;

    if (!chief_concern || !chief_concern.trim()) {
      return NextResponse.json({ ok: false, error: "Chief concern required" }, { status: 400 });
    }

    const doc = createPractitionerCase({
      patient_pseudonym: (patient_pseudonym || "").trim(),
      chief_concern: chief_concern.trim(),
      modalities: (modalities || "").trim(),
      body: (caseBody || "").trim(),
    });

    return NextResponse.json({ ok: true, case: doc });
  } catch (err) {
    console.error("[POST /api/practitioner/cases]", err);
    return NextResponse.json({ ok: false, error: "Server error" }, { status: 500 });
  }
}
