import { NextResponse } from "next/server";
import { isAdminPasswordSet, setAdminPassword, createAdminSession, validateAdminPassword } from "@/lib/adminAuth";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { password, setup } = body;

    if (!password || password.length < 6) {
      return NextResponse.json({ ok: false, error: "Password must be at least 6 characters" }, { status: 400 });
    }

    if (setup) {
      if (isAdminPasswordSet()) {
        return NextResponse.json({ ok: false, error: "Admin password already set" }, { status: 400 });
      }
      setAdminPassword(password);
      const token = createAdminSession();
      const res = NextResponse.json({ ok: true });
      res.cookies.set("admin_session", token, { httpOnly: true, secure: false, sameSite: "lax", path: "/" });
      return res;
    }

    if (!isAdminPasswordSet()) {
      return NextResponse.json({ ok: false, error: "Admin password not set yet" }, { status: 400 });
    }

    if (!validateAdminPassword(password)) {
      return NextResponse.json({ ok: false, error: "Invalid password" }, { status: 401 });
    }

    const token = createAdminSession();
    const res = NextResponse.json({ ok: true });
    res.cookies.set("admin_session", token, { httpOnly: true, secure: false, sameSite: "lax", path: "/" });
    return res;
  } catch (err) {
    console.error("[POST /api/admin/auth]", err);
    return NextResponse.json({ ok: false, error: "Server error" }, { status: 500 });
  }
}
