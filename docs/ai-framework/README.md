# BASH OS — AI Consulting Framework (planning)

This folder holds the design for turning the bashconsultants repo into an
all-in-one, AI-augmented **consulting operating system** — built on top of the
static site, powered by Claude, and reusable by other consultants.

The architecture is the brand: a **deterministic, git-versioned, scriptable
foundation** with a **Claude AI overlay** that proposes and drafts while humans
and CI decide what ships.

## Documents

| File | What it covers | Status |
|---|---|---|
| [`PLAN.md`](./PLAN.md) | Master plan: vision, layered architecture, capability modules, governance, distribution, phased roadmap | Draft |
| `ARCHITECTURE.md` | Diagrams + architecture decision records (ADRs) | _planned (Phase 0)_ |
| `AUTONOMY-POLICY.md` | The semi-autonomous blast-radius rules (Green / Yellow / Red) | _planned (Phase 0)_ |
| `ADOPT.md` | "Fork this for your own practice" adoption guide | _planned (Phase 4)_ |

## Locked decisions

- **Hosting:** GitHub Pages → AI runs at build-time (CI agents) + local authoring tools; no serverless runtime.
- **Phase 1:** Content Studio (idea → draft → review → publish), built deepest first.
- **Autonomy:** Semi-autonomous — AI auto-commits low-risk changes; customer-facing/business-critical changes go through PR review.

Start with [`PLAN.md`](./PLAN.md).
