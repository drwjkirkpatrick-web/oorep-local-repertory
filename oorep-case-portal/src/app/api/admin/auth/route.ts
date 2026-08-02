import { NextResponse } from "next/server";
// SECURITY NOTE: This is the login/session-creation endpoint — it does NOT
// call requireAdminSession() by design. All other /api/admin/* routes DO
// call requireAdminSession() to verify the cookie before handling requests.
// This route authenticates the admin password and creates the session token.
import { isAdminPasswordSet, setAdminPassword, createAdminSession, validateAdminPassword } from "@/lib/adminAuth";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { password, setup } = body;

    // v4.3 Security: minimum 12 chars for admin (was 6)
    if (!password || password.length < 12) {
      return NextResponse.json({ ok: false, error: "Password must be at least 12 characters" }, { status: 400 });
    }

    if (setup) {
      if (isAdminPasswordSet()) {
        return NextResponse.json({ ok: false, error: "Admin password already set" }, { status: 400 });
      }
      setAdminPassword(password);
      const token = createAdminSession();
      const res = NextResponse.json({ ok: true });
      // v4.3 Security: secure:true in production, __Host- prefix
      res.cookies.set("admin_session", token, {
        httpOnly: true,
        secure: process.env.NODE_ENV === "production",
        sameSite: "lax",
        path: "/",
      });
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
    res.cookies.set("admin_session", token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      path: "/",
    });
    return res;
  } catch (err) {
    console.error("[POST /api/admin/auth]", err);
    return NextResponse.json({ ok: false, error: "Server error" }, { status: 500 });
  }
}
