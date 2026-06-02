import { NextResponse } from "next/server";
import { createCase } from "@/lib/db";
import crypto from "crypto";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { practitioner_email, practitioner_name, chief_concern, modalities, body: caseBody } = body;

    if (!practitioner_email || !practitioner_email.includes("@")) {
      return NextResponse.json({ ok: false, error: "Valid practitioner email required" }, { status: 400 });
    }
    if (!chief_concern || !chief_concern.trim()) {
      return NextResponse.json({ ok: false, error: "Chief concern required" }, { status: 400 });
    }

    const doc = createCase({
      practitioner_email: practitioner_email.trim(),
      practitioner_name: (practitioner_name || "").trim(),
      chief_concern: chief_concern.trim(),
      modalities: (modalities || "").trim(),
      body: (caseBody || "").trim(),
      files: [],
      status: "pending_payment",
      stripe_payment_intent_id: null,
      stripe_customer_email: practitioner_email.trim(),
      paid_at: null,
      reviewed_at: null,
      repertory_result: null,
      draft_pdf_path: null,
      final_pdf_path: null,
      sent_at: null,
    });

    return NextResponse.json({ ok: true, case: doc });
  } catch (err) {
    console.error("[POST /api/cases]", err);
    return NextResponse.json({ ok: false, error: "Server error" }, { status: 500 });
  }
}
