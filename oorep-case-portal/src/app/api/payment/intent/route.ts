import { NextResponse } from "next/server";
import { assertStripe, stripe, PRICE_CENTS } from "@/lib/stripe";
import { getCaseByCode, updateCase } from "@/lib/db";

export async function POST(request: Request) {
  try {
    assertStripe();
    const body = await request.json();
    const { case_code, practitioner_email, practitioner_name } = body;

    const caseDoc = getCaseByCode(case_code);
    if (!caseDoc) return NextResponse.json({ ok: false, error: "Case not found" }, { status: 404 });

    const intent = await stripe!.paymentIntents.create({
      amount: PRICE_CENTS,
      currency: "usd",
      metadata: { case_code, case_id: caseDoc.id, practitioner_email, practitioner_name },
      receipt_email: practitioner_email,
    });

    updateCase(caseDoc.id, { stripe_payment_intent_id: intent.id });

    return NextResponse.json({ ok: true, client_secret: intent.client_secret });
  } catch (err: any) {
    console.error("[POST /api/payment/intent]", err);
    return NextResponse.json({ ok: false, error: err?.message || "Stripe error" }, { status: 500 });
  }
}
