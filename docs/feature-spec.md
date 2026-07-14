# Đạt Phương Asset Management App — Feature Specification

Source material: [`prep/data/mission.md`](../prep/data/mission.md) (product vision), five internal
Đạt Phương Group procedures: `QT01_TB` (equipment management), `QT02_TB` (maintenance/repair),
`QT03_TB` (fixed-asset procurement), `QT04_TB` (fixed-asset liquidation), `QT10_HCNS` (office
equipment/IT purchase & repair), the live registry `DS-Thiết bị VP 2025.xlsx`, and
[`prep/requirements.md`](../prep/requirements.md) (platform/UI/workflow requirements — brand,
language, SSO, import/export, printable forms, e-signature). `requirements.md` also points at two
external references that are now load-bearing on this spec, not just inspiration:

- The sibling internal app **`dpg lms/DPG E-learning`** — its frontend/backend stack, brand, and
  i18n are to be *reused*, not re-derived (see §0).
- The commercial Google Sheets template at optimatevn.com ("Quản lý tài sản thiết bị công ty") — a
  reference point for asset-listing structure (assignment log, maintenance log, liquidation log,
  overview dashboard, condition photos, one-click handover-memo generation) that several sections
  below cite directly.

All five procedure PDFs are stamped **"Tài liệu MẬT" / "Lưu hành nội bộ"** (confidential, internal
circulation only) — this is a hard constraint on the app, not a suggestion (see §11).

The company runs **two distinct asset domains with two distinct governance chains**. The app must
model both, not average them into one generic "asset" workflow:

| Domain | Vietnamese scope | Governed by | Owning dept | Approval basis |
|---|---|---|---|---|
| **A. Construction machinery / fixed assets (TSCĐ)** | "Máy - trang thiết bị của công ty" used on project sites | QT01, QT02, QT03, QT04 | Phòng Thiết bị (Equipment Dept.), Phòng Thi công, Phòng Kế hoạch, Phòng Kế toán | Value-tiered, up to HĐQT (Board) |
| **B. Office & IT equipment** | Máy, thiết bị, đồ dùng văn phòng at HQ | QT10_HCNS | Phòng HCNS (HR-Admin), IT staff | Cost-tiered, up to TGĐ; SLA-timed for repairs |

Every feature below is traceable back to a specific procedure step so the app can be audited
against the source documents.

---

## 0. Platform, brand & auth alignment

`requirements.md` requires the same UI (color/logo), the same multi-language behavior, and the same
SSO as `dpg lms/DPG E-learning`. That app already exists and its choices are inspectable — so this
section locks them in as **decisions**, not options, and the rest of this spec assumes them.

**Frontend** — reuse the LMS's stack and folder shape exactly: Vue 3 + Vite, Tailwind CSS, Pinia
(state stores), vue-router, vue-i18n, axios. Mirror `frontend/src/{pages,components,stores,i18n,
utils}`; the asset app's `AppHeader.vue`, `UserAvatar.vue`, `NotificationBell.vue`, and
`GlobalSearch.vue` can be lifted close to verbatim, swapping nav links for asset-app routes.

**Backend** — reuse the LMS's stack: FastAPI, SQLAlchemy + Alembic migrations, Postgres, Redis
(sessions/cache), MinIO (S3-compatible object storage for attachments — legal documents, condition
photos, signed forms), Docker Compose. Mirror `backend/app/{api,core,models,schemas}`.

**Brand** — reuse the LMS's Tailwind palette verbatim: `brand` `#D22930` (red — header bar, primary
CTA), `primary` `#014f6e` (dark teal — page background), plus `cream` `#F6F1E3`, `ochre` `#CC9210`,
and the shared `/logo.png`. Don't invent a new palette or logo treatment for this app.

**Language** — vue-i18n with `vi.json`/`en.json` message files and a header toggle
(🇻🇳 VI / 🇬🇧 EN), same as LMS. **Vietnamese is the default and primary language** — staff already
work from Vietnamese paper forms and BM-numbered fields; English is the secondary toggle, not the
target for translation-first design.

**Auth** — email+password (JWT access + refresh tokens, `/api/auth/login`) **plus optional Google
SSO** via Google Identity Services, gated by a `GOOGLE_CLIENT_ID` env var and exchanged through
`/api/auth/google` — the exact mechanism already running in LMS's `Login.vue` / `stores/auth.js`.
This resolves the former "Auth" open question: Google SSO is additive to password login, not a
replacement for it, and the two apps *could* share one Google OAuth client (confirm with IT — see
plan.md open questions).

**Confidentiality mechanism** — LMS already solved "let staff view a sensitive PDF without being
able to download, print, or right-click-save it": `Document.secure_view` flags a document for
page-by-page image rendering through `SecureDocumentViewer.vue` (backend rasterizes each page,
frontend disables context-menu and never exposes a raw file URL). **Reuse this mechanism as-is**
for the five *Tài liệu MẬT* guideline PDFs (§11) instead of designing a new confidentiality control.

---

## 1. Guideline traceability matrix

| Doc | Process (VN) | Trigger form | App module | Non-negotiable rule |
|---|---|---|---|---|
| QT01_TB | Yêu cầu / điều động / quản lý sử dụng thiết bị | BM01–BM06 | **Allocation & Usage** | Request → Phòng Thi công checks feasibility → Lãnh đạo approves → Phòng Thiết bị either **redeploys existing equipment** or routes to rental/QT03; monthly usage report due, cost rolled up by Phòng Kế hoạch |
| QT02_TB | Bảo dưỡng, sửa chữa thiết bị | BM01–BM08 | **Maintenance & Repair** | Small jobs approved by Trưởng đơn vị sử dụng; jobs beyond unit capability go to Phòng Thiết bị → Kỹ sư máy inspects → cost plan → Lãnh đạo approves → execute → nghiệm thu (acceptance) by role that owns the job size; usage-unit report due before day 5 monthly; Phòng Thiết bị plan report due before day 10 of next quarter |
| QT03_TB | Mua sắm tài sản cố định | BM01–BM05 | **Procurement (capex)** | Approval tier by *value*: **<300tr → TGĐ; 300tr–2 tỷ → Chủ tịch HĐQT; 2 tỷ–35% tổng giá trị TS → HĐQT** (per Quy chế chi tiêu nội bộ, referenced not owned by this doc — must be configurable, not hardcoded) |
| QT04_TB | Thanh lý tài sản cố định | BM01–BM05 | **Liquidation** | Phòng Thiết bị proposes → TGĐ/người được HĐQT ủy quyền approves candidacy → ad-hoc **Hội đồng thanh lý** assesses residual value, solicits bids, issues thanh lý decision → contract & biên bản → Kế toán issues invoice and removes asset from books |
| QT10_HCNS | Mua sắm & sửa chữa/khắc phục máy, TB, đồ dùng văn phòng | BM01–BM04 | **Office/IT Helpdesk** | SLA: small in-house fix ≤ **4 working hours**; large/outsourced fix ≤ **8 working hours** from intake. Cost approval tier: **≤3tr/vụ (≤10tr/month) → Trưởng phòng HCNS; 3tr–20tr/vụ (≤50tr/month) → Lãnh đạo phụ trách nội chính; >20tr/vụ (no monthly cap) → TGĐ**, but see §1.1 — this tier is capped by QT03 above 300tr. Approved records must be scanned and logged to `hethong.datphuong.vn` (existing internal portal — integration question, see §10) |

### 1.1 Resolving the QT03 ↔ QT10 approval-ceiling conflict

QT03 and QT10 both claim procurement authority over the same categories of equipment (§ intro
domain table), and their approval ceilings **contradict each other above roughly 20 triệu**: QT10
gives TGĐ unlimited, uncapped sign-off for office/IT purchases; QT03 caps TGĐ at <300tr and requires
Board-level sign-off beyond that. Left unresolved, a purchase filed as an "office/IT ticket" could
let the TGĐ approve a large spend alone that would have needed Chủ tịch HĐQT or HĐQT sign-off had
it been filed as TSCĐ procurement.

**Decision: QT03's value ladder is the universal ceiling on spending authority, applied on top of
whichever process (QT01–04 or QT10) originates the request.**

| Value of the single purchase (vụ) | Who must sign off | How it plays out |
|---|---|---|
| < 300 triệu | Per the originating process's own tiers | QT10 tickets still route through Trưởng phòng HCNS (≤3tr) → Lãnh đạo phụ trách nội chính (3tr–20tr) → TGĐ (20tr–300tr) exactly as QT10 specifies. QT03 procurement below 300tr is TGĐ-only as QT03 specifies. Nothing changes here. |
| 300tr – 2 tỷ | **Chủ tịch HĐQT** | Escalates out of QT10 into QT03's chain — even if the item is office/IT equipment and even if TGĐ would have signed off under QT10's own (uncapped) wording |
| ≥ 2 tỷ, up to 35% of total asset value | **HĐQT** | Same escalation, full Board |

Mechanically: QT10's *">20tr/vụ, no monthly cap → TGĐ"* tier is **capped at 300tr** by this rule —
TGĐ's uncapped authority under QT10's literal wording never actually applies once value clears the
QT03 floor. A ticket can stay in the QT10 UI/SLA-tracking flow for process purposes, but the
approval engine must route its cost-approval step through the QT03 ladder, not stop at TGĐ, once
the amount reaches 300tr.

This resolves *who must approve the spend* — the higher-risk half of the conflict. It does **not**
resolve the separate question of which asset register (TSCĐ vs. office/CCDC) the item lands in for
depreciation/bookkeeping purposes; that classification question is still open (see `plan.md`).

---

## 2. Roles & permissions

| Role | Domain | Source | Core app permissions |
|---|---|---|---|
| CBNV (any employee) | A + B | all docs | Submit usage/repair/purchase requests for own dept's assets; view own assigned assets & their history |
| Đơn vị sử dụng / Trưởng đơn vị sử dụng (using unit & its head) | A | QT01, QT02 | Request equipment; approve small maintenance costs; submit monthly usage report; nghiệm thu small repairs |
| Ban Điều hành DA / Ban CH Công trình (project & site management boards) | A | QT01 | Same as using unit, at project scope |
| Phòng Thi công (Construction Dept.) | A | QT01 | Validate feasibility of equipment requests; escalate to procurement/rental when internal fleet can't cover |
| Phòng Thiết bị (Equipment Dept.) + Kỹ sư máy (machine engineers) | A | QT01–QT04 | Own the equipment master data & lý lịch (asset dossier); decide redeploy vs. rent; run technical inspections; draft repair/procurement/liquidation proposals; nghiệm thu large repairs; produce ca-máy / cost reports |
| Phòng Kế hoạch (Planning Dept.) | A | QT01 | Monthly roll-up of equipment cost (owned + rented) for project budgeting; monthly capital-draw approval |
| Phòng Kế toán (Accounting Dept.) | A | QT03, QT04 | Create asset card & depreciation on acquisition; issue invoice & remove asset from ledger on liquidation |
| Lãnh đạo phụ trách dự án / Ban TGĐ | A | QT01–QT04 | Approve equipment allocation, maintenance cost, and act inside their value tier for procurement/liquidation |
| Chủ tịch HĐQT | A | QT03 | Approve procurement 300tr–2 tỷ |
| HĐQT (Board) | A | QT03, QT04 | Approve procurement ≥2 tỷ up to 35% of total asset value; authorize liquidation candidacy (or delegate to TGĐ) |
| Hội đồng thanh lý TSCĐ (ad-hoc liquidation council) | A | QT04 | Assess residual value, run bidding, issue thanh lý decision & biên bản |
| Chuyên viên IT (IT staff, under HCNS) | B | QT10 | Triage all office/IT tickets, execute or dispatch to vendor, log SLA clock, close with bàn giao/nghiệm thu form |
| Trưởng phòng HCNS | B | QT10 | Approve office purchase/repair ≤3tr/vụ, ≤10tr cumulative/month |
| Lãnh đạo phụ trách nội chính | B | QT10 | Approve 3tr–20tr/vụ, ≤50tr cumulative/month |
| TGĐ (CEO) | A + B | QT03, QT04, QT10 | Top approver below/without HĐQT: procurement <300tr, liquidation candidacy, office spend >20tr/vụ |

Cross-cutting: an **Admin** role manages department/entity structure, approval-threshold config, and
user-role assignment (see §3.5).

---

## 3. Core data model

### 3.1 Asset
Fields below reconcile the mission's ask ("basic info", "legal papers", "log") with the columns
already in production use inside `DS-Thiết bị VP 2025.xlsx`:

| Field | Source | Notes |
|---|---|---|
| `asset_code` (Mã tài sản) | Excel, e.g. `MTS020` | **Currently blank for most office assets in `TB-VP`** — app must auto-generate on creation; migration needs a backfill pass |
| `name` (Tên vật tư – thiết bị) | Excel | |
| `category` (Nhóm thiết bị) | Excel | Laptop / Desktop / iPad / construction-machine class etc.; drives which QT flow applies (A vs B) |
| `spec` (Cấu hình kỹ thuật cơ bản) | Excel | Free text; long |
| `serial_number` (Số Serial) | Excel | Present only on `TB-VP` sheet, mostly blank — data-quality gap |
| `manufacture_year`, `year_put_in_use` | Excel | Excel stores "năm sử dụng" as an Excel serial date — needs normalization on import |
| `manufacturer` (Hãng sản xuất) | Excel | |
| `original_cost` (Nguyên giá, VNĐ) | Excel | |
| `warranty_months` (Bảo hành) | Excel | |
| `legal_entity` | inferred from `ĐPHA` sheet | Group HQ vs. subsidiary (e.g. Đạt Phương Hội An) — asset can be transferred between entities, must be tracked, not assumed single-company |
| `department` (Phòng ban sử dụng), `holder` (Người sử dụng) | Excel | **Current holder** — mission story #1 |
| `location` (site/project or HQ office) | optimatevn template; not an explicit Excel column today | Domain-A assets move between project sites — `department` alone (an org unit) doesn't capture *where* the asset physically is; template's dashboard filters by location as a first-class dimension alongside dept/category/condition |
| `status` (Tình trạng) | Excel | Đang sử dụng / Đang sửa chữa / Chờ thanh lý / Đã thanh lý / Đã điều động, etc. — needs a controlled enum, not free text |
| `budget_plan_year` / `budget_actual_year` (Kế hoạch–Thực hiện NS năm), `replacement_priority` (UT1/UT2) | Excel | Refresh/replacement planning — feeds a budgeting report, not just registry |
| `purchase_source` (Nơi mua) | Excel | |
| `notes` (Ghi chú) | Excel | |
| `legal_documents[]` | mission story #2 | Attachments: receipt, purchase contract, warranty card, kiểm định (inspection/registration) certificate — required for vehicles/machines needing đăng ký/đăng kiểm per QT01 step 3 |

### 3.2 Asset history / lý lịch (append-only log)
Mission story #1 & #2 ask explicitly for "who is using it, who used to use it, has it ever been
broken down or fixed" and "a log... when was it bought, which unit has been in possession of it".
Model as one append-only `asset_events` table, typed:

- `ACQUIRED` (from QT03 flow)
- `ALLOCATED` / `TRANSFERRED` (điều động — from QT01, carries from-unit/to-unit, decision doc ref)
- `MAINTENANCE` / `REPAIR` (from QT02, carries cost, parts replaced, nghiệm thu ref)
- `STATUS_CHANGE`
- `LIQUIDATED` (from QT04, carries sale price, buyer, invoice ref)
- `COST_REPORTED` (monthly usage cost entries feeding QT01 BM05/BM06)

Every event stores `actor`, `timestamp`, `approval_ref` (link to the request/approval that
authorized it), and optional `attachment[]`. This is what renders as the asset's "lý lịch" screen
and what QT02 step 9 calls updating "lý lịch thiết bị".

Following the optimatevn template's pattern, `ALLOCATED`/`TRANSFERRED` and `MAINTENANCE`/`REPAIR`
events should support **condition photos** as a specific attachment subtype (visual evidence at
handover/return, and before/after repair) — cheap to add now, and it's the one feature of the
reference template with no equivalent anywhere in the QT forms, which are text/signature-only.

A **computed depreciation / residual-value** figure per asset (the template auto-calculates this)
is a useful supplementary display, but **Phòng Kế toán's ledger remains the source of truth** per
QT03 step 5/6 — don't let an in-app estimate silently diverge from the accounting figure; label it
"estimated" and reconcile against Kế toán's number wherever both are shown together.

### 3.3 Software license (office/IT assets only)
The `TB-VP`/`TH` sheets track per-device software with license status embedded in free text (e.g.
`Windows 11 Pro (BQ theo máy)` vs. `AutoCAD 2021 (Crack)`). Model explicitly:

`software_installations`: `asset_id`, `software_name`, `version`, `license_type` (OEM / Volume /
Per-user / **Unlicensed**), `license_ref`. This turns today's implicit compliance risk (several
titles currently marked "Crack" in the live sheet) into a queryable **license-compliance report** —
a natural early win for IT/HCNS.

### 3.4 Request (unified, typed)
One `requests` entity with `type` ∈ {`USAGE`, `ALLOCATION`, `MAINTENANCE_SMALL`,
`MAINTENANCE_LARGE`, `PROCUREMENT`, `LIQUIDATION`, `OFFICE_PURCHASE_REPAIR`}, each with its own
state machine (§5) but sharing: requester, asset(s)/category, cost estimate, current approver,
approval history, SLA deadline (type `OFFICE_PURCHASE_REPAIR` only), linked documents.

### 3.5 Approval rule engine
Thresholds are **cited by the procedures but owned by a separate "Quy chế chi tiêu nội bộ"** (internal
spending policy) that isn't in the provided source set — meaning these numbers *will* change
without a QT document revision. Do not hardcode 300tr/2 tỷ/35%, 3tr/20tr/10tr/50tr, or the
4h/8h SLA windows. Store them as versioned, effective-dated config rows keyed by
`(domain, request_type, tier)`, editable only by Admin, with every request snapshotting the rule
version it was evaluated against (for audit).

**Cross-domain ceiling override (resolves §1.1).** Evaluating a request's required approver is
*not* a single lookup into its own request-type's tier table — it's two lookups whose result is
the more senior of the two:

1. Look up the tier for the request's own `type` (e.g. `OFFICE_PURCHASE_REPAIR` → QT10 tiers).
2. Independently look up where the request's cost falls on the QT03 procurement ladder
   (`< 300tr / 300tr–2 tỷ / ≥ 2 tỷ`), *regardless of request type*.
3. Required approver = whichever of (1) or (2) sits higher in the org chart. Below 300tr, (1)
   always wins trivially (QT03's own ladder bottoms out at TGĐ too). At or above 300tr, (2) always
   wins and the request must carry **both** an HCNS/IT record (for SLA/process tracking) and a
   QT03-chain approval (Chủ tịch HĐQT or HĐQT) before execution — it cannot close on a TGĐ sign-off
   alone.

This makes the override a property of the rule engine's evaluation logic, not a one-off exception
hardcoded into the QT10 ticket flow — so it applies uniformly however many request types get added
later.

---

## 4. Workflows

### 4.1 Equipment usage & allocation — QT01
`Đơn vị sử dụng` submits `USAGE` request → `Phòng Thi công` checks feasibility against fleet
(pass/fail loop back to requester) → Lãnh đạo phê duyệt → branch:
- **Có thể điều động** (redeployable): Phòng Thiết bị issues Quyết định điều động → Lãnh đạo
  approves the decision → transport organized → receiving unit signs biên bản bàn giao (BM03) →
  asset status flips to allocated, `ALLOCATED` event logged.
- **Không thể điều động**: routed to rental (unit sources & negotiates rental contract itself) or
  to §4.3 procurement.

Ongoing: receiving unit owns a **monthly usage report** (BM04, due before day 5) → Phòng Thiết bị
computes usage cost (BM05) → Phòng Kế hoạch aggregates owned+rented cost for project budget
approval. Phòng Thiết bị closes each year with a ca-máy/repair-value report by machine group (BM06).

### 4.2 Maintenance & repair — QT02
Two parallel lanes gated by size:
- **Small** (within unit capability): unit requests (BM01) → Trưởng đơn vị sử dụng approves cost →
  unit executes → unit's own kỹ thuật viên does nghiệm thu (BM04).
- **Large** (exceeds unit capability) *or* **planned/major maintenance**: Phòng Thiết bị's kỹ sư máy
  inspects (BM02) and drafts cost plan (BM03) → Trưởng phòng Thiết bị reviews (loop back if
  unsuitable) → Lãnh đạo approves → execution supervised jointly by kỹ sư máy + vận hành → kỹ sư
  máy does nghiệm thu (BM04).

Reporting cadence: unit's monthly usage/status report (reuses QT01 BM04) before day 5; Phòng Thiết
bị's quarterly plan-execution report (BM07) before day 10 of the next quarter. All large-repair
content updates the asset's lý lịch (§3.2).

### 4.3 Fixed-asset procurement — QT03
Phòng Thiết bị drafts đề xuất đầu tư (BM01) → routed to the correct approver **by value tier**
(§3.5) → once approved, Phòng Thiết bị researches spec/vendor options, issues Quyết định mua sắm
(BM02) for TGĐ sign-off → sources supplier, negotiates, contract signed → asset delivered to using
unit + technology handover → for items needing đăng ký/đăng kiểm, Phòng Thiết bị tracks that
separately (BM05) → Phòng Kế toán creates the asset card & starts depreciation → Phòng Thiết bị
opens the lý lịch (BM04) and the asset enters the QT01 lifecycle.

### 4.4 Fixed-asset liquidation — QT04
Phòng Thiết bị proposes liquidation candidates from underperforming assets (BM01, backed by repair-cost
history) → TGĐ / HĐQT-delegate approves candidacy → **Hội đồng thanh lý** assesses residual
condition (BM02) → issues Quyết định thanh lý (BM03) → sets/approves sale price (BM04) → runs
bidding, signs mua-bán contract, produces biên bản thanh lý (BM05) → Phòng Thiết bị hands over the
physical asset; Phòng Kế toán issues invoice **and removes the asset from the ledger** — this is
the one flow that ends an asset's lifecycle rather than logging an event onto it.

### 4.5 Office/IT equipment — purchase, repair, incident — QT10
Any staff or dept raises a ticket (BM01) → IT/HCNS staff triage into **repair/incident** vs.
**new purchase/parts-replacement-with-cost** lanes:
- **Repair/incident**: SLA clock starts on intake — 4 working hours if fixable in-house, 8 if it
  needs an outside vendor. No cost approval needed unless parts are purchased.
- **Purchase / paid repair**: cost routed to the correct approval tier (§3.5, cost-per-incident +
  running monthly total, both checked) — **and, per §1.1's cross-domain override, re-checked against
  the QT03 value ladder**; if the amount is ≥300tr the request escalates to Chủ tịch HĐQT/HĐQT and
  cannot close on a TGĐ sign-off → on approval, purchase contract (BM02) if applicable → execute →
  close with bàn giao/nghiệm thu (BM03 for purchases, BM04 for incident fixes) → HCNS admin scans &
  files, and — pending a decision (see plan.md open questions) — pushes the record to
  `hethong.datphuong.vn`.

The SLA clock, the "≤ X/vụ **and** ≤ Y cumulative this month" check, and the QT03 ceiling override
are the three pieces of QT10 logic most likely to be silently wrong if implemented informally; all
three need first-class support in the approval engine, not ad-hoc code in a controller.

---

## 5. Reporting & dashboards

Derived directly from named BM forms plus the Excel's existing planning columns — these are not
speculative additions:

- **Asset register / lý lịch view** — per-asset dossier: profile, current holder, full event
  history, attached legal docs, running repair cost. (QT01 BM04, QT03 BM04)
- **Monthly usage-cost report** — by asset & by project, owned vs. rented split. (QT01 BM05)
- **Annual ca-máy / repair-value report by machine group.** (QT01 BM06)
- **Maintenance plan vs. execution** — quarterly, by Phòng Thiết bị. (QT02 BM06/BM07)
- **Depreciation / book-value view** — sourced from Kế toán's asset card, read-only mirror in-app.
- **Replacement/refresh planner** — reuses the Excel's Kế hoạch NS năm / Thực hiện NS năm /
  UT1-UT2 fields to forecast next-year office-equipment budget.
- **Software license compliance report** — per device / per department, flags non-`OEM`/`Volume`
  licenses (today's "Crack" entries) for remediation.
- **SLA compliance dashboard (Office/IT)** — open tickets vs. 4h/8h targets, breach alerts.
- **Approval queue** — per-role inbox of pending requests at their tier.
- **Overview dashboard** (per optimatevn template) — total asset count, in-use vs. in-storage, total
  original cost vs. estimated residual value, charts by category/department/**location**/condition,
  quick filters. This is the closest thing to a "home screen" for Phòng Thiết bị and HCNS.

---

## 6. Feature list

**MVP** — `requirements.md` explicitly marks e-signature as a **"(main)"** priority and asks for
import/export as a cross-cutting capability, not an afterthought, so both are pulled forward here
rather than deferred to a later phase:
- Platform alignment (§0): LMS-matching brand/header/i18n, email+Google-SSO auth
- Asset registry (domain A + B, single schema) with manual entry + Excel import (§9)
- Asset dossier / lý lịch timeline (read + auto-logged events, incl. condition photos)
- Legal document attachments per asset
- Office/IT ticket flow (QT10) end-to-end, incl. SLA clock and 2-tier+TGĐ approval
- Equipment usage request + điều động (QT01) end-to-end
- Role-based access control matching §2
- Configurable approval-threshold engine (§3.5)
- **Printable form generation + e-signature capture** on every request type shipped in MVP (§10)
- **Import/export** for Excel and PDF at minimum; Google Sheets if the OAuth-scope question (see
  plan.md) resolves in time (§9)
- **Help button → guideline archive**, reusing the secure-viewer pattern (§11)

**Phase 2**
- Maintenance/repair flow (QT02) for domain-A assets, incl. nghiệm thu forms
- Procurement flow (QT03) with value-tier routing to Chủ tịch HĐQT / HĐQT
- Monthly/annual reports (usage cost, ca-máy, maintenance plan-vs-actual)
- Software license compliance report
- Google Sheets import/export, if not already shipped in MVP
- User profile document/activity log (§12), if not already shipped in MVP

**Phase 3**
- Liquidation flow (QT04) incl. Hội đồng thanh lý workflow and bidding capture
- Multi-legal-entity transfer support (HQ ↔ subsidiaries, per `ĐPHA` sheet)
- Replacement/budget forecasting view
- Integration with `hethong.datphuong.vn` (pending decision, see plan.md open questions)

---

## 7. Non-functional requirements

- **Confidentiality**: source procedures are marked *Tài liệu MẬT / Lưu hành nội bộ*. The app is
  internal-only — no public internet exposure without VPN/SSO, no anonymous access, and the
  procedures themselves are served in-app through the same **secure, non-downloadable viewer**
  used for other confidential material (§0, §11), not as a plain file download.
- **Vietnamese-first UI**; all field labels here are given in Vietnamese-with-English-gloss to match
  what staff already know from the paper forms — don't retranslate into generic English terms.
- **Immutable audit trail** on `asset_events` and on every approval decision (who, when, against
  which threshold-config version).
- **Configurable, effective-dated approval thresholds** (§3.5) — not constants in code.
- **SLA timers** measured in *working hours*, not wall-clock — needs a working-calendar service.
- **Document storage** for scanned legal papers/contracts with reasonable retention (QT10 references
  a separate `QĐ11_HCNS` records-retention policy not in the provided set — flag for follow-up).
- **Signed-document integrity**: once a form is e-signed (§10), its content and signature metadata
  become immutable — corrections require a new superseding document, not an edit in place.

---

## 8. Data migration from `DS-Thiết bị VP 2025.xlsx`

| Sheet | Meaning | Migration action |
|---|---|---|
| `TB-VP` | Active office/IT equipment (173 rows) | Primary import source for domain-B assets + software_installations |
| `TB-Bỏ` | Retired/disposed office equipment (sparse — many placeholder blank rows) | Import non-blank rows as `status = LIQUIDATED/RETIRED`; skip template placeholders |
| `ĐPHA` | Equipment liquidated to/held by subsidiary Đạt Phương Hội An | Import as domain-A/legal-entity-transferred assets; confirms multi-entity requirement |
| `TH` | Software-license-focused subset/duplicate of `TB-VP` | Do not import as separate assets — reconcile as source for `software_installations`, not a fifth asset list |

Known data-quality gaps to resolve during import (not to silently carry forward): missing
`asset_code` and `serial_number` on most `TB-VP` rows, Excel serial-date values in
"năm sử dụng", free-text `status`/`repair` fields that need mapping to controlled enums.

---

## 9. Universal import/export

`requirements.md` asks for "a unique template that supports import and export [of] Google Sheets,
Excel, PDF ... files" for asset listings — i.e., the registry shouldn't just do a one-time Excel
migration (§8); it needs a standing, bidirectional exchange format.

**Design**: define one canonical internal schema (§3.1's `Asset` fields) and treat every external
format as an *adapter* onto/from it, rather than writing N special-case import scripts:

| Format | Import | Export | Notes |
|---|---|---|---|
| **Excel (.xlsx)** | Column-mapped, per §8 | Full registry or filtered view, in the same column layout staff already read (so Phòng Thiết bị/HCNS can keep working in Excel if they want to, without losing app-side history) | Highest priority — this is today's actual working format |
| **Google Sheets** | Same column mapping as Excel, via Sheets API | Live-updating export (a Sheet the app writes to, not a one-time snapshot) | Requires a Google API credential/OAuth scope decision — separate from the Google *SSO* login credential (see plan.md open questions); don't conflate the two |
| **PDF** | Not a structured-data import target — treat as *attachment ingestion* (legal docs, contracts) rather than trying to parse asset rows out of a PDF | Generated output only: the printable forms in §10, and read-only registry snapshots/reports | Matches how PDF is actually used across the QT docs (as a document artifact, not a data table) |

The optimatevn template's column layout (asset ID/type/serial/purchase-date/supplier/cost,
assignment fields, maintenance log, liquidation log) is a second reference point for the Excel
column mapping, alongside the live `DS-Thiết bị VP 2025.xlsx` — reconcile the two rather than
picking one arbitrarily where they differ.

---

## 10. Printable forms & e-signature

`requirements.md`, §"Request": *"Any action with the asset mentioned in the guideline... are
conveniently processible via the app UI. Then the form (generate a template) can also be printed.
The form will follow the company guideline (who to send for confirmation)... Create an option for
e-signature (main)."* This is the single most load-bearing requirement in that file — it's marked
main priority — and it connects directly to work already done in §1–§4:

**Printable forms**: every request type in §3.4/§4 maps to a specific BM-numbered paper form (BM01
"đề nghị", BM02 "quyết định", BM03/BM04 "biên bản", etc. — see the traceability matrix in §1).
When a request is submitted, the app generates that form pre-filled from the request/asset data, in
the layout staff already recognize, and routes it to the *correct next signer per that request's
approval chain* (§3.5) — this is what "follow the company guideline (who to send for confirmation)"
means concretely: the routing isn't a generic "send for approval" button, it's the same
role/tier logic already specified for that QT process. The generated form must remain printable
(PDF) even after e-signing, for staff who need a physical copy.

**E-signature**: each approval step captures a signature (typed name confirmation at minimum,
drawn/uploaded signature image as an enhancement) bound to `actor`, `timestamp`, and a hash of the
document content at signing time — stored alongside the `approval_ref` already modeled in §3.2/§3.4,
so a signed form is just a rendered view of data the approval engine already has, not a separate
subsystem to keep in sync.

**Open question this raises** (see plan.md): a self-built "click to sign" control is an *audit
trail*, not necessarily a legally-binding digital signature under Vietnam's e-transaction law. For
purely internal approvals (allocation, small maintenance, office tickets) that's almost certainly
sufficient. For documents with external legal force — e.g. the QT03/QT04 mua-bán/thanh lý
contracts, which involve an outside counterparty — confirm whether those still need a licensed
CA-based digital signature (e.g. VNPT-CA, Viettel-CA) *in addition to* the in-app signature, or
whether the in-app one is only ever used for the internal approval steps and the contract itself is
signed the traditional way outside the app.

---

## 11. Help / guideline archive

`requirements.md`, §"Archive": the five QT PDFs in `prep/data/` must be reachable from a **Help
button on the app's taskbar** (i.e., always-available from `AppHeader`, not buried in a settings
page). Since they're marked *Tài liệu MẬT*, serve them through the same secure, non-downloadable
viewer described in §0/§7 — this mirrors LMS's staff-facing "Archive" page's document tab almost
exactly, down to the pattern of gating it by role (LMS shows it only to `moderator`/`admin`; this
app should gate it by whichever roles are authorized to see confidential internal procedures,
likely everyone above CBNV — confirm during Phase 0).

Content: the five procedures as-is (QT01–04_TB, QT10_HCNS), organized by domain (A vs. B, §intro
table) so a user looking for "how do I request a repair" lands on the right document without
needing to already know the QT numbering scheme.

---

## 12. User profile document/activity log

`requirements.md`, §"Request", last line: *"Any document made is saved in the logs for the unique
asset as well as the relevant user profile."* §3.2 already models the asset-side half of this
(`asset_events`, append-only, per-asset). The **user-side half is a distinct view**, not just the
inverse query: a "My Documents" section on the user's profile page (mirroring LMS's `Profile.vue`
pattern) listing every request/form/signature the user has authored or signed, across *all* assets
— useful both as a personal work log and as the natural place an auditor would look to answer "what
has this person done in the system," independent of which asset(s) were involved.

Implementation-wise this is a query (`asset_events` / `requests` filtered by `actor`), not a second
data model — keep it that way rather than duplicating storage.
