# Delivery Plan — Đạt Phương Asset Management App

Companion to [`feature-spec.md`](feature-spec.md). This is a sequencing/build plan, not a
functional spec — see that doc for the "what," this doc for the "in what order and how."

## Why this sequencing

The feature spec identifies two governance domains (construction machinery under QT01–04, office/IT
under QT10) with very different cadence and risk:

- Domain B (office/IT) is **high-frequency, low-value, short-cycle** (hours-to-days, SLA-driven) —
  good for proving the request→approval→log pattern quickly and cheaply.
- Domain A (construction machinery) is **low-frequency, high-value, multi-approver** (procurement
  can escalate to the Board) — the workflow is more complex and the cost of a modeling mistake is
  higher, so it benefits from having the pattern already proven in Phase 1.

Building the registry + Domain B first also means the first real users (HCNS/IT) are the same
people who'll do UAT on the historical-data import, since they own today's `DS-Thiết bị VP
2025.xlsx`.

## Decisions log

**2026-07-13 — QT03 ↔ QT10 approval-ceiling conflict.** QT10 lets TGĐ approve office/IT purchases
of any size (no stated ceiling); QT03 caps TGĐ at <300tr and requires Chủ tịch HĐQT (300tr–2 tỷ) or
HĐQT (≥2 tỷ, up to 35% of total assets) beyond that. **Resolved: QT03's value ladder is the
universal ceiling on spending authority, applied on top of whichever process originates the
request** — see feature-spec §1.1 and the engine rule in §3.5 ("Cross-domain ceiling override").
Concretely, QT10's own ">20tr/vụ, no cap → TGĐ" tier is now capped at 300tr; anything at or above
300tr escalates into the QT03 chain regardless of whether it started life as an office/IT ticket.
This must be built into the approval engine from Phase 1 (the QT10 ticket flow ships then), even
though the full QT03 procurement flow itself doesn't ship until Phase 2 — otherwise a large
office/IT ticket in Phase 1 could close on a TGĐ sign-off it shouldn't have.

This decision fixes *who must approve the spend*. It does **not** settle which asset register
(TSCĐ vs. office/CCDC) an item is booked under for depreciation purposes — that's a separate,
still-open classification question (see open question 7 below).

**2026-07-14 — Platform, brand, and auth are reused from `dpg lms/DPG E-learning`, not
re-derived.** `prep/requirements.md` asks for the same UI (color/logo), same multi-language
behavior, and same SSO as that sibling app. Inspecting it directly (rather than guessing) turned
that into concrete decisions — see feature-spec §0: Vue 3 + Vite + Tailwind + Pinia + vue-i18n
frontend; FastAPI + SQLAlchemy/Alembic + Postgres + Redis + MinIO backend, Docker Compose; brand
colors `#D22930`/`#014f6e`/`#F6F1E3`/`#CC9210` + shared `/logo.png`; email+password login with
*optional* Google SSO via `GOOGLE_CLIENT_ID`, mirroring LMS's `/api/auth/google` flow exactly. This
**replaces** the former "Suggested stack (open to override)" section below and **resolves** the
former Auth open question — see the updated stack section and open questions below.

Also decided, following `requirements.md`'s explicit **"(main)"** priority tag on e-signature:
printable-form generation, e-signature capture, cross-format import/export, and the Help-button
guideline archive move from "Phase 3 nice-to-have" into **Phase 1 MVP** — see the revised Phase 1
deliverables below and feature-spec §9–§12.

## Phase 0 — Foundation & decisions (before writing app code)

1. Resolve the open questions in the Open Questions section below — several change the data model.
2. Stand up the asset schema (§3 of feature spec) and the approval-rule-engine tables — get this
   right early since every later phase's workflow reads from it.
3. Import `TB-VP` + `ĐPHA` + non-blank `TB-Bỏ` rows as seed data (see feature-spec §8); this also
   surfaces real data-quality issues (missing asset codes/serials) before they block Phase 1 UAT.
4. Stand up auth + role model (§2 of feature spec) — at minimum: CBNV, Trưởng phòng HCNS, Lãnh đạo
   phụ trách nội chính, TGĐ, Phòng Thiết bị, Admin. The rest of the domain-A roles can be added in
   Phase 2 without a schema change if roles are modeled as data, not code branches.

## Phase 1 — MVP: Registry + Office/IT helpdesk (QT10) + basic allocation (QT01)

Deliverables:
- Platform scaffold matching LMS: header/brand/i18n (VI default, EN toggle), email+Google-SSO auth.
- Asset registry UI (list, filter by dept/category/status/**location**, detail/dossier view) for
  both domains; Excel import (§8) and Excel/PDF export (§9).
- Legal-document attachment upload on asset dossier, incl. condition photos.
- QT10 ticket flow end-to-end: intake → triage → SLA clock (4h in-house / 8h outsourced) → 2-tier +
  TGĐ cost approval (per-incident *and* running monthly cap), **with the QT03 ceiling override
  applied** so a ticket ≥300tr escalates to Chủ tịch HĐQT/HĐQT instead of closing on TGĐ → close
  with bàn giao/nghiệm thu.
- QT01 usage-request + điều động flow for domain-A assets (no procurement/maintenance yet — those
  are Phase 2). Monthly usage report entry (feeds Phase 2 reporting).
- Approval-threshold config screen (Admin) — thresholds must be editable without a deploy, since
  they're owned by a policy document outside this project's source set.
- **Printable form generation + e-signature** (feature-spec §10) wired into both flows shipped this
  phase (QT10 and QT01) — this is the requirements doc's main-priority ask, not deferrable.
- **Help button → guideline archive** (feature-spec §11), reusing LMS's secure/non-downloadable PDF
  viewer for the five *Tài liệu MẬT* procedures.

Exit criteria: HCNS/IT run real office tickets through the app for a full month in parallel with
their current process; SLA and approval-tier logic verified against real cases before the old
process is retired; at least one QT10 ticket has gone through print + e-signature end to end.

## Phase 2 — Domain-A depth: Maintenance (QT02) + Procurement (QT03) + core reporting

Deliverables:
- QT02 small-repair and large-repair/planned-maintenance lanes, incl. nghiệm thu forms and lý lịch
  updates.
- QT03 procurement flow with value-tier routing up to Chủ tịch HĐQT / HĐQT, and the handoff to
  Kế toán for asset-card creation.
- Monthly usage-cost report, annual ca-máy report, quarterly maintenance plan-vs-actual report.
- Software license compliance report (low-effort, high-visibility — data's already in the Excel).
- Google Sheets import/export (feature-spec §9), if the OAuth-scope question below wasn't resolved
  in time for Phase 1.
- User profile document/activity log (feature-spec §12), if not already shipped in Phase 1.

Exit criteria: Phòng Thiết bị stops maintaining the equipment side of the spreadsheet in parallel;
Kế toán confirms asset-card handoff matches their books.

## Phase 3 — Liquidation (QT04) + multi-entity + forecasting + integration

Deliverables:
- QT04 liquidation flow incl. Hội đồng thanh lý workflow, bidding capture, invoice/ledger-removal
  handoff to Kế toán.
- Multi-legal-entity asset transfer (HQ ↔ subsidiaries — confirmed necessary by the `ĐPHA` sheet).
- Replacement/budget forecasting view (reuses Kế hoạch NS năm / UT1-UT2 fields).
- `hethong.datphuong.vn` integration, if decided (see open question 1 below).

## Confirmed stack (reused from `dpg lms/DPG E-learning`)

No app code exists yet in *this* repo, but the sibling `dpg lms/DPG E-learning` project does, and
`requirements.md` requires matching its UI/brand/language/SSO — so the stack is inspected and
reused rather than chosen fresh (see feature-spec §0 for the full rationale):

- **Frontend**: Vue 3 + Vite + Tailwind CSS + Pinia + vue-router + vue-i18n + axios, mirroring
  `frontend/src/{pages,components,stores,i18n,utils}`.
- **Backend**: FastAPI + SQLAlchemy + Alembic + Postgres + Redis + MinIO, mirroring
  `backend/app/{api,core,models,schemas}`; Docker Compose for local/prod parity.
- **Auth**: email+password (JWT access+refresh) + optional Google SSO (`GOOGLE_CLIENT_ID` env var,
  `/api/auth/google` credential exchange) — identical mechanism to LMS's `Login.vue`/`stores/auth.js`.
- **File storage**: MinIO buckets for legal documents, condition photos, and generated/signed forms
  (§10) — same role Postgres+MinIO already play in LMS for course documents.

Still to decide before scaffolding (see open questions): whether this app shares LMS's Postgres
instance/user directory or runs as an independent deployment with its own database and a separately
issued Google SSO session.

### Docker/deployment configuration (mirrored from LMS)

LMS's `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`, and `frontend/nginx.conf`
are a working, already-battle-tested deployment config (it's set up for zero-config startup on
Dokploy, per its own comments) — reuse the same shape rather than designing a new one:

- **Services**: `frontend`, `backend`, `postgres` (16-alpine), `redis` (7-alpine), `minio`, and a
  `db-backup` sidecar that runs a daily `pg_dump` loop and prunes to the 14 newest dumps.
- **Backend Dockerfile**: multi-stage-free `python:3.11-slim`, installs `requirements.txt`, runs
  `alembic upgrade head && uvicorn app.main:app` as the container command — migrations apply on
  every boot, not as a separate manual step.
- **Frontend Dockerfile**: two-stage — `node:20-alpine` builds the Vite bundle, `nginx:alpine`
  serves the built `dist/` and reverse-proxies `/api/` to the `backend` service on the Docker
  network (`proxy_pass http://backend:8000`), with `proxy_request_buffering off` so uploads stream
  through instead of buffering — this app will want the same for legal-document/photo uploads.
- **Config philosophy**: every `docker-compose.yml` value has a built-in default (`${VAR:-default}`)
  so the stack runs with **zero required environment configuration**; only secrets/keys
  (`POSTGRES_PASSWORD`, `SECRET_KEY`, `GOOGLE_CLIENT_ID`) are meant to be overridden per deployment.
  Follow the same pattern here instead of requiring a fully-populated `.env` before first boot.
- **Volumes are pinned by name** (`pg_data2: {name: ${PG_VOLUME_NAME:-dpg-lms-pg-data-v2}}`, etc.),
  not derived from the Compose project name — this is deliberate so data survives renames/redeploys.
  Do the same for this app's volumes, with names distinct from LMS's if the two run as **separate**
  stacks (see open question 10), or shared volume/network wiring if they end up **co-located**.
- **Healthchecks + `depends_on: condition: service_healthy`** gate backend startup on
  Postgres/Redis actually being ready, not just "container started" — carry this over; it's what
  makes `docker compose up` reliably work on first boot instead of racing.

## Risks / things likely to bite if skipped

- **Hardcoding today's thresholds** (300tr/2 tỷ/35tr%, 3tr/20tr, 10tr/50tr, 4h/8h) instead of
  versioned config — these are cited from a separate spending policy not in the source set and will
  drift out of sync with reality.
- **Treating "status" as free text** instead of a controlled enum from day one — the live Excel
  already shows this rotting (inconsistent status strings across sheets).
- **Skipping the multi-entity model** because it "only affects one sheet" — `ĐPHA` shows transfers
  between legal entities already happen; retrofitting this later touches every asset-scoped query.
- **Building Domain A before Domain B** — inverts the natural low-risk-first sequencing and delays
  getting real users (HCNS) into the loop.
- **Re-deriving what LMS already solved** — a from-scratch confidentiality control, PDF-rasterizing
  viewer, or i18n setup would duplicate real, working code for no benefit; §0 exists specifically to
  prevent that. Reuse the LMS mechanisms (or literally share the service, if the two apps end up
  co-located) rather than reimplementing them "slightly differently."
- **Treating the in-app e-signature as legally equivalent to a licensed digital signature** — it's
  an audit trail (actor + timestamp + content hash), not a CA-issued signature. Fine for internal
  approval steps; may not be sufficient for documents with external legal force (vendor contracts
  under QT03/QT04) without also going through the traditional/licensed signing process — see open
  question 8.

## Open questions for the user

1. **Integration**: QT10 step 5 references an existing internal portal `hethong.datphuong.vn` where
   approved records get scanned/logged today. Should this app *replace* that for asset records, or
   *feed into* it (and if so, via what — API, batch export, manual dual-entry)?
2. ~~**Auth**~~ — resolved 2026-07-14: email+password + optional Google SSO, matching LMS (see
   decisions log). Remaining sub-question: is there a company Google Workspace OAuth client this
   app should register under (possibly the *same* client LMS uses), and who owns provisioning it?
3. **Threshold source of truth**: QT03/QT10 cite a separate "Quy chế chi tiêu nội bộ" for the money
   thresholds. Do you have that document (or its current numbers) so the config seed values are
   accurate rather than back-inferred from the QT PDFs?
4. **Scope for v1**: confirm the (now-expanded) Phase 1 cut — registry + QT10 + QT01 + printable
   forms/e-signature + Help archive — is right, or whether e-signature/import-export should be
   trimmed back out of MVP to ship the workflow core faster.
5. **Software license remediation**: several titles in the live sheet are marked "Crack." Is
   surfacing a compliance report enough for v1, or does this need to drive an active remediation
   workflow (e.g., auto-flagged procurement requests)?
6. **Hosting**: on-prem (company already runs `hethong.datphuong.vn`, and presumably LMS, internally)
   vs. cloud. Given the stack is now confirmed to mirror LMS, the default assumption is this app is
   deployed the same way LMS is — confirm that's correct, and whether it's the *same* host/Docker
   Compose stack or a sibling deployment.
7. **TSCĐ vs. office/CCDC classification boundary**: the ceiling conflict (decisions log above) is
   resolved, but which register an asset is *booked* under — TSCĐ (depreciated, Phòng Thiết bị +
   Kế toán) vs. office consumable/CCDC (HCNS) — still has no documented test. Is that a value
   threshold, an asset-category list, or a Kế toán capitalization rule we should pull in separately?
8. **E-signature legal weight**: is the self-built "click/draw to sign + audit trail" mechanism
   (feature-spec §10) sufficient for *all* signed documents in this app, or do documents with
   external legal force (QT03/QT04 mua-bán/thanh lý contracts with an outside counterparty) still
   need a licensed CA-based digital signature (VNPT-CA, Viettel-CA, etc.) on top of it?
9. **Google Sheets API credential**: Sheets import/export (feature-spec §9) needs its own Google
   API credential/OAuth consent separate from the Google *SSO login* credential. Is there an
   existing Google Cloud project/service account for this (possibly the same one backing LMS's
   `GOOGLE_CLIENT_ID`) that should be extended, or does this need its own?
10. **Shared infra with LMS**: should this app share LMS's Postgres instance and user directory
    (true single sign-on, one user table across both internal tools) or run fully independently
    with its own database and its own Google SSO session? Affects Phase 0 schema setup directly.
