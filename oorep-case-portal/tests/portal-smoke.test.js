/**
 * Smoke test for the Next.js Case Portal dashboard routes.
 *
 * Run: node --test tests/portal-smoke.test.js
 * Requires the dev server running at http://localhost:3000
 */

const assert = require("node:assert");
const test = require("node:test");

const BASE = process.env.PORTAL_URL || "http://localhost:3000";

async function fetchJSON(path) {
  const res = await fetch(`${BASE}${path}`);
  const text = await res.text();
  try { return { status: res.status, data: JSON.parse(text) }; }
  catch { return { status: res.status, data: text }; }
}

test.describe("Portal API smoke tests", () => {
  test("/api/portal/modules returns 40 modules", async () => {
    const { status, data } = await fetchJSON("/api/portal/modules");
    assert.strictEqual(status, 200);
    assert.ok(data.ok);
    assert.strictEqual(data.modules.length, 40);
    const ids = data.modules.map((m) => m.id);
    assert.ok(ids.includes("repertorize"), "has repertorize");
    assert.ok(ids.includes("cycles"), "has cycles");
    assert.ok(ids.includes("red_flags"), "has red_flags");
    assert.ok(ids.includes("approval_gate"), "has approval_gate");
  });

  test(" every module has required fields", async () => {
    const { status, data } = await fetchJSON("/api/portal/modules");
    assert.strictEqual(status, 200);
    for (const m of data.modules) {
      assert.ok(m.id, "module has id");
      assert.ok(m.name, "module has name");
      assert.ok(m.category, "module has category");
      assert.ok(m.benefit !== undefined, "module has benefit");
      assert.ok(m.route, "module has route");
      assert.ok(Array.isArray(m.inputs), "module has inputs array");
      assert.ok(Array.isArray(m.outputs), "module has outputs array");
    }
  });
});
