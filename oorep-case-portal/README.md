# OORep Case Portal

A practitioner-facing Next.js web frontend for the OORep clinical repertory platform.

## Features

- **Module Dashboard** — Tabbed Mission Control with Case Entry, Saved Cases, My Profile, and Quick Links tabs; module picker sidebar, responsive canvas, and report action bar
- **Practitioner Profile & Settings** — Configurable default active modules, auto-run, and preferred potency ladder
- **Quick Links** — Practitioner-managed reference bookmarks with add/delete
- **Case Editing** — Edit saved cases inline via the Saved Cases tab
- **Visual Pipeline Builder** — Drag-and-drop protocol designer using React-Flow
- **32+ Dashboard Panels** — Orphan intake and statistical panels now rendered and registered (patient intake, chief complaint, causation timeline, Thompson sampling, ensemble stacking, Bayesian network, Gaussian process, SPRT, rubric discrimination, question bank, and more)
- **Stripe billing integration** for practitioner subscriptions
- **PDF report generation** from module outputs

## Tech Stack

- Next.js 14.2.3 + React 18 + TypeScript
- Tailwind CSS
- `@xyflow/react` (pipeline builder)
- `d3` (visualization engine)
- `react-draggable` (dashboard panels)

## Routes

| Route | Purpose |
|---|---|
| `/dashboard` | Clinical Mission Control (module picker + canvas + action bar) |
| `/dashboard/pipeline` | Visual Pipeline Builder |
| `/api/portal/modules` | Module discovery API (105 OORep modules) |
| `/api/practitioner/cases` | Case CRUD (GET/POST) |
| `/api/practitioner/cases/[id]` | Single case operations (PATCH/DELETE) |
| `/api/practitioner/profile` | Practitioner profile (GET/POST/PATCH) |
| `/api/practitioner/settings` | Dashboard settings (GET/POST/PATCH) |
| `/api/practitioner/quicklinks` | Quick links (GET/POST) |
| `/api/practitioner/quicklinks/[id]` | Quick link operations (PATCH/DELETE) |
| `/api/admin/repertorize` | Repertorization endpoint |

## Quick Start

```bash
npm install
npm run dev        # localhost:3000
npm run build      # production build
```

## Related

- **Python Repertory Engine:** [drwjkirkpatrick-web/oorep-local-repertory](https://github.com/drwjkirkpatrick-web/oorep-local-repertory)
- **Upstream OOREP:** https://github.com/nondeterministic/oorep

---

Built by Walker Kirkpatrick, ND. Cycles & Segments visualization powered by the method of Dr. Paul Herscu and Dr. Amy Rothenberg, NESH.
