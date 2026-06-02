# OORep Case Portal — Session Notes

## Project Location
`/home/walker/projects/oorep-case-portal`

## How to Resume
```bash
cd /home/walker/projects/oorep-case-portal
NEXT_TELEMETRY_DISABLED=1 npx next dev --port 3456
```
Or for production:
```bash
npm run build
npm start
```

## Tech Stack
- Next.js 14.2.3 + React 18 + TypeScript
- Tailwind CSS v4
- File-based JSON DB (no SQLite)
- Stripe API (PaymentIntents)
- Python execFile (OOREP repertorization + fpdf2 PDF)

## File Inventory
```
src/
  lib/
    db.ts           — JSON DB (cases, upload, PDF dirs)
    adminAuth.ts    — PBKDF2 password hash + session cookies
    stripe.ts       — Stripe client + PRICE_CENTS=4900
    upload.ts       — sanitizeFilename + FILES_DIR
  app/
    page.tsx                          — Landing page
    layout.tsx                        — Root layout + metadata
    globals.css                       — Tailwind + theme vars
    submit/page.tsx                   — Case submission form
    status/page.tsx                   — Suspense wrapper
    status/StatusPage.tsx             — Case status tracker
    admin/login/page.tsx             — Admin login
    admin/page.tsx                   — Case queue dashboard
    admin/review/[id]/page.tsx        — Review, repertorize, PDF, send
    api/
      cases/route.ts                  — POST create case
      upload/route.ts                — POST file attach
      status/route.ts                — GET by case_code
      payment/
        intent/route.ts              — POST Stripe PI
        confirm/route.ts             — POST confirm payment
      admin/
        auth/route.ts                — POST login / first-time setup
        cases/route.ts               — GET list cases (filterable)
        cases/[id]/route.ts          — GET/PATCH single case
        repertorize/route.ts         — POST run OOREP Python
        pdf/route.ts                — POST generate PDF
```

## Data Dir
`~/.hermes/data/oorep-case-portal/`
- `cases/*.json` — Case documents
- `files/` — Uploaded attachments
- `pdfs/` — Generated PDFs
- `.admin_pass_hash` — Hashed admin password
- `.admin_sessions.json` — Active sessions

## Environment Variables Needed
- `STRIPE_SECRET_KEY` — Required for payments to work

## Build Status
✅ Compiles clean (Next.js 14.2.3)
✅ All smoke tests pass
⚠ Dev server: port 3456

## Next Steps Checklist

### A. Payment & Upload
- [ ] Install Stripe.js for frontend (currently uses manual PI flow)
- [ ] Add real Stripe Elements checkout in `/submit`
- [ ] File upload test on `/submit` currently sends files after case creation — verify upload API works end-to-end with real files
- [ ] `assertStripe()` throws if secret missing — add graceful "payment unavailable" UI

### B. Admin Authentication
- [ ] Add middleware `/middleware.ts` protecting `/admin/*` routes server-side
- [ ] Admin logout button in dashboard
- [ ] Session expiry warning/redirect

### C. Review Workflow
- [ ] OOREP Python script path: confirm `~/.hermes/skills/clinic/homeopathic-repertory-oorep/` scripts match exec call in `/api/admin/repertorize/route.ts`
- [ ] PDF generator script: confirm Python + fpdf2 installed, script path matches exec call in `/api/admin/pdf/route.ts`
- [ ] Add download endpoint `/api/admin/pdf/download?id=` to serve generated PDFs
- [ ] Status page: add PDF download link when `status === "sent"`

### D. Practitioner UX
- [ ] Email notification to practitioner on case creation (optional SMTP)
- [ ] Status checker improvements: add case detail view after search
- [ ] Landing page copy: add real testimonials, practitioner FAQ, sample report snippet

### E. Production
- [ ] Wire `STRIPE_SECRET_KEY` into environment
- [ ] Choose production port and configure reverse proxy (nginx/Caddy)
- [ ] Enable `next start` and `output: "standalone"` on prod
- [ ] Backups: add `~/.hermes/data/oorep-case-portal/` to nightly backup

### F. Testing
- [ ] Full walkthrough: submit → pay (Stripe test mode) → upload → admin login → review → repertorize → draft PDF → final PDF → mark sent → status check
- [ ] Test edge cases: empty case, missing modalities, admin without password set
