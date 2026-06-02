# OORep Case Portal

A practitioner-facing Next.js web frontend for the OORep clinical repertory platform.

## Features

- **Module Dashboard** — Tabbed Mission Control with module picker sidebar, responsive canvas, and report action bar
- **Visual Pipeline Builder** — Drag-and-drop protocol designer using React-Flow
- **Three new visualizations (v3.1):**
  - **Circular Cycle Rings** — Polar segment coverage per remedy
  - **Differential Remedy Radar** — 7-axis comparison chart
  - **Repertorization Sankey Flow** — Symptom-to-remedy routing diagram
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
| `/api/portal/modules` | Module discovery API (40 OORep modules) |
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
