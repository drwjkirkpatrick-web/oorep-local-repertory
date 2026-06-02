import { NextResponse } from "next/server";
import { updateCase, getCaseById } from "@/lib/db";
import { assertStripe, stripe } from "@/lib/stripe";

export async function POST(request: Request) {
  try {
    assertStripe();
    const body = await request.json();
    const { payment_intent_id, case_id } = body;

    if (!payment_intent_id || !case_id) {
      return NextResponse.json({ ok: false, error: "Missing fields" }, { status: 400 });
    }

    const intent = await stripe!.paymentIntents.retrieve(payment_intent_id);

    if (intent.status !== "succeeded") {
      return NextResponse.json({ ok: false, error: `Payment status: ${intent.status}` }, { status: 400 });
    }

    const doc = getCaseById(case_id);
    if (!doc) return NextResponse.json({ ok: false, error: "Case not found" }, { status: 404 });

    updateCase(case_id, { status: "paid", paid_at: new Date().toISOString() });

    return NextResponse.json({ ok: true, status: "paid" });
  } catch (err: any) {
    console.error("[POST /api/payment/confirm]", err);
    return NextResponse.json({ ok: false, error: err?.message || "Server error" }, { status: 500 });
  }
}
