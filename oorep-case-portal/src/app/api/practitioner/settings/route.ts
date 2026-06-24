import { NextResponse } from "next/server";
import { getPractitionerSettings, savePractitionerSettings } from "@/lib/db";

export async function GET() {
  try {
    const settings = getPractitionerSettings();
    if (!settings) {
      return NextResponse.json({ ok: true, settings: null });
    }
    return NextResponse.json({ ok: true, settings });
  } catch (err) {
    console.error("[GET /api/practitioner/settings]", err);
    return NextResponse.json({ ok: false, error: "Server error" }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const {
      default_enabled_module_ids,
      default_module_ids,
      layout_density = "comfortable",
      theme = "light",
      auto_run_on_load = false,
      show_visualizations = true,
      show_advanced_panels,
      auto_run_on_save,
    } = body;

    const moduleIds = default_enabled_module_ids ?? default_module_ids;
    if (!Array.isArray(moduleIds)) {
      return NextResponse.json({ ok: false, error: "default_enabled_module_ids array required" }, { status: 400 });
    }

    const settings = savePractitionerSettings({
      default_enabled_module_ids: moduleIds.filter((x: any) => typeof x === "string"),
      layout_density: ["compact", "comfortable", "spacious"].includes(layout_density) ? layout_density : "comfortable",
      theme: ["light", "dark", "system"].includes(theme) ? theme : "light",
      auto_run_on_load: Boolean(auto_run_on_load || auto_run_on_save),
      show_visualizations: Boolean(show_visualizations ?? show_advanced_panels),
    });

    return NextResponse.json({ ok: true, settings });
  } catch (err) {
    console.error("[POST /api/practitioner/settings]", err);
    return NextResponse.json({ ok: false, error: "Server error" }, { status: 500 });
  }
}

export async function PATCH(request: Request) {
  try {
    const body = await request.json();
    const existing = getPractitionerSettings();
    if (!existing) {
      return NextResponse.json({ ok: false, error: "Settings not found" }, { status: 404 });
    }
    const settings = savePractitionerSettings({ ...existing, ...body });
    return NextResponse.json({ ok: true, settings });
  } catch (err) {
    console.error("[PATCH /api/practitioner/settings]", err);
    return NextResponse.json({ ok: false, error: "Server error" }, { status: 500 });
  }
}
