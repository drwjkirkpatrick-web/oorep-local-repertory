import { NextResponse } from "next/server";
import { listQuickLinks, createQuickLink } from "@/lib/db";

export async function GET() {
  try {
    const quicklinks = listQuickLinks();
    return NextResponse.json({ ok: true, links: quicklinks });
  } catch (err) {
    console.error("[GET /api/practitioner/quicklinks]", err);
    return NextResponse.json({ ok: false, error: "Server error" }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { practitioner_id, label, url, category = "reference", sort_order = 0 } = body;

    if (!label || !label.trim()) {
      return NextResponse.json({ ok: false, error: "label required" }, { status: 400 });
    }
    if (!url || !url.trim()) {
      return NextResponse.json({ ok: false, error: "url required" }, { status: 400 });
    }

    const quicklink = createQuickLink({
      practitioner_id: (practitioner_id || "").trim(),
      label: label.trim(),
      url: url.trim(),
      category: ["remedy", "rubric", "reference", "custom"].includes(category) ? category : "reference",
      sort_order: typeof sort_order === "number" ? sort_order : 0,
    });

    return NextResponse.json({ ok: true, link: quicklink });
  } catch (err) {
    console.error("[POST /api/practitioner/quicklinks]", err);
    return NextResponse.json({ ok: false, error: "Server error" }, { status: 500 });
  }
}
