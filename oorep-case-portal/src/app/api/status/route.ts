import { NextResponse } from "next/server";
import { getCaseByCode } from "@/lib/db";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const code = searchParams.get("code");
    if (!code) {
      return NextResponse.json({ ok: false, error: "Missing code" }, { status: 400 });
    }
    const doc = getCaseByCode(code.trim().toUpperCase());
    if (!doc) {
      return NextResponse.json({ ok: false, error: "Not found" }, { status: 404 });
    }
    return NextResponse.json({ ok: true, case: doc });
  } catch (err) {
    console.error("[GET /api/status]", err);
    return NextResponse.json({ ok: false, error: "Server error" }, { status: 500 });
  }
}
