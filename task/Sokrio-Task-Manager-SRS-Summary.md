# Software Requirements Specification (Summary)
## Sokrio Task Manager Add-on — Monthly Planning, Approval, Execution & Achievement Management

**Version:** 1.5 baseline (summarized) | **Status:** Draft for Product & Client Sign-off | **Standard:** IEEE 830 / ISO/IEC/IEEE 29148 | **Default Timezone:** Asia/Dhaka (UTC+06:00), org-configurable | **Audience:** Client, Product, BA, UI/UX, Engineering, QA, DevOps, Security, Support

---

## 1. Introduction & Purpose
The Sokrio Task Manager Add-on is an organisation-scoped enterprise module replacing spreadsheet-based PJP/task planning with governed catalogues, calendar scheduling, measurable subtasks, hierarchy-based approval, execution completion, and month-end achievement reporting. It separates four concepts: **Task classification** (Admin-managed Category/Type/Frequency/Master Task), **Planned task instance** (employee-specific date/route/target/etc.), **Workflow state** (DRAFT→SUBMITTED→APPROVED, or REJECTED/EXPIRED/ABANDONED/VOID), and **Execution/result state** (progress, completion, achievement — tracked separately from workflow).

## 2. Scope
**In scope:** Auth & org context; role-based hierarchy access; configurable monthly Planning/Approval/Execution/Review/Archive windows; List & Calendar plan creation; copy/reuse/presets; Admin-managed catalogues; calendar bulk-add with drag/drop; one-level subtasks with progress roll-up; supervisor task assignment; full-plan submit & selected/full approval; task comments/discussion; execution progress & completion; month-end achievement vs. plan reporting; Team Submission Dashboard; User-wise Task Report; bulk submission reminders; Excel/CSV/PDF export mapped to client PJP formats; user preferences; logging, audit, security, accessibility.
**Out of scope (initial release):** Payroll/incentives/expenses, route optimisation, GPS attendance, CRM replacement, automatic edits to approved fields, recursive subtasks beyond one level, public plan sharing, external calendar sync/native push.

## 3. Business Objectives (selected)
Replace manual planning spreadsheets (≥90% adoption); ≥98% first-pass validation; ≥95% on-time approval decisions; 100% block/audit of approved-field mutation; 100% completion/achievement disposition by archive; ≥40% reduction in next-month prep time; preserve client workbook reconciliation; ≥95% on-time submission via proactive dashboards; enable coaching via comparative achievement data; full task-level audit trail for compliance.

## 4. User Roles
| Role | Scope | Key Permissions |
|---|---|---|
| Team Member | Own/assigned tasks | Create/edit/submit own Draft; manage subtasks/comments/progress/achievement |
| Supervisor | Self + direct reports | Team Member rights + assign Master Tasks, review/approve/return reports' plans |
| Approver | Department | Review/decide submitted plans; no task creation unless dual-roled |
| Admin | Org-wide | Catalogue/config/user/hierarchy mgmt, Approver rights, void, audit/export; cannot self-approve |
| Viewer | Authorised read-only | Dashboards/details/reports only |
| System | Automation | Window transitions, expiry, archive, notifications, reconciliation |

Self-approval is always prohibited; every request enforces org → role → owner/assignee → hierarchy/department → cycle phase → task state → field policy, in order.

## 5. Monthly Cycle & State Model
Phases (default): **Planning/Submission** (Day 1–25, Draft work for month M+1) → **Approval** (until Day 28) → **Execution** (full month M+1) → **Review** (Day 1–5 of M+2, achievement entry) → **Archive** (Day 6 of M+2, locks results). All boundaries use org timezone; a stable `cycle_id` is authoritative, not display labels.

State flow: `DRAFT → SUBMITTED → APPROVED`; `SUBMITTED → REJECTED → DRAFT` (on revision); `SUBMITTED → EXPIRED` at window close; `DRAFT/REJECTED → ABANDONED` at archive if never submitted; `APPROVED → VOID` (Admin only, reasoned). Approved planned fields are immutable; `execution_completed` and `achievement_status` are tracked independently of workflow status.

## 6. Functional Modules
Identity & Access · Cycle Management · Personal Planning (List/Calendar) · Reuse & Bulk Planning · Catalogue (Categories/Types/Master Tasks) · Subtasks & Discussion · Submission & Approval · Team Assignment · Execution & Achievement · Reporting · Administration · Notifications & Preferences.

## 7. Key Screens (S-02 to S-15)
| Screen | Purpose |
|---|---|
| S-02 Dashboard | Tabbed "My Tasks"/"Team Overview" — KPIs, charts, cycle-scoped action items |
| S-03 My Tasks (List) | Full-month plan list — search/filter/sort, submit full plan |
| S-04 My Tasks (Calendar) | Date-first view — bulk multi-add via Master Task picker, drag/drop reschedule |
| S-05 Create/Edit Task | Preset or governed custom task entry with subtasks & attachments |
| S-06 Task Detail | Lifecycle, subtasks, execution-proof attachments, approval history, discussion |
| S-07 Submit Plan Dialog | Validates & atomically submits owner's full reportable plan |
| S-08 Team Plan Review | Supervisor/Approver decisions — approve selected/full, return with reason |
| S-09 Assign Team Task | Supervisor/Admin creates attributed employee-owned Draft for a report |
| S-10 Progress & Execution | Track/complete Approved tasks; attach proof files during execution |
| S-11 Month-End Achievement | Record ACHIEVED/PARTIAL/NOT_ACHIEVED vs. plan; auto-marks at deadline |
| S-12 Reports & Exports | Plan-vs-achievement analysis, client-format Excel/CSV/PDF export |
| S-13 Admin Task Setup | Manage Categories, Task Types, Master Tasks, proposals, workbook import |
| S-14 Users/Hierarchy/Config | User/role/reporting-relationship and cycle/security configuration |
| S-15 Notifications & Prefs | Actionable events, deep links, List/Calendar & channel preferences |
| S-10b Team Submission Dashboard | Supervisor visibility into submission status & achievement per member; Send Reminder, Export |
| S-11b User-wise Task Report | Tabular per-user task audit (dates, remarks, attachments) with export |

## 8. Core Business Rules (highlights)
Approved planned fields are immutable everywhere (409 on write attempt, audited). Self-approval always forbidden. Supervisor authority uses effective-dated hierarchy; submission-time reviewer responsibility persists unless audited reassignment. Category/Type/Frequency are independent stable dimensions; catalogues never contain employee-specific values. Deactivated catalogue items block new use but never rewrite history. Full-plan submission and full approval are atomic; selected approval affects only chosen tasks. Rejection/return requires a 10–500 char reason. Outstanding assigned Drafts block full-plan approval. Subtasks: one level only, equal or custom weights (must total 100). Execution completion (progress=100, `execution_completed=true`) never auto-sets achievement. Unreviewed Approved tasks auto-become NOT_ACHIEVED at Review close. All writes use optimistic locking + idempotency; audit log is append-only and written before success is reported. Zero/null denominators return `N/A`, never a misleading 0%.

## 9. Non-Functional Requirements (highlights)
**Availability** ≥99.9%/month. **Scalability** 10,000 concurrent users, ≥1M tasks/org. **Reliability** RPO ≤15 min, RTO ≤2 hrs. **Accessibility** WCAG 2.2 AA. **Performance**: dashboard p95 ≤2s, first-50-rows p95 ≤2s, standard writes p95 ≤1.5s, bulk 100-task ops p95 ≤3s, in-app notification ≤60s / email ≤5 min. **Security**: TLS 1.2+, AES-256 at rest, Argon2id/bcrypt hashing, MFA/SSO support, 60-min access / 7-day refresh tokens, IDOR/XSS/CSRF/injection protection, signed export URLs ≤15 min expiry, approved-field immutability enforced at DB/transaction level (not just UI).

## 10. Data, API & Audit
REST API base `/api/v1/task-manager`, versioned OpenAPI 3.1, bearer/session auth, `X-Correlation-ID`, idempotency keys on retry-sensitive writes, standard `{data, meta}` / `{error:{code,message,...}}` envelopes. Core entities: Organisation, User, ReportingRelationship, MonthlyCycle, MonthlyPlanSubmission, TaskCategory/Type/MasterTaskPreset, Task, Subtask, TaskComment, ApprovalRecord, Notification, WorkbookMapping, AuditEvent. Every write and high-risk read/export is captured in an immutable, tamper-evident audit trail (actor, org, scope, device/IP, action, entity diff, reason, correlation ID); audit retained ≥5 years, notifications 90 days.

## 11. Acceptance Criteria (representative)
Scope isolation across users/cycles enforced everywhere (rows, counts, exports, APIs). One invalid task blocks whole-plan submission with zero transitions and field-level errors. Every self-owned approval attempt returns 403. Outstanding assigned Draft blocks full approval with a count. Two of four equal subtasks yield 50% progress; custom weights 20+50 yield 70%. Mark Complete → 100% progress, status stays APPROVED, achievement stays unset. Achievement Rate = (Achieved+Partial)/Reportable-Approved × 100 (e.g., 8/10 → 80%). Catalogue deactivation never alters historical tasks/reports. All core flows are keyboard/screen-reader operable at WCAG 2.2 AA.

## 12. Future Scope
Approved-task change requests with reapproval; external calendar sync; native mobile push & offline-first; Sokrio SFA event integration; recurrence-rule engine; workload/capacity optimisation; configurable approval chains/delegation; webhooks/partner APIs; multilingual catalogues; forecasting/anomaly detection.

---
*Condensed from the full Enterprise SRS (v1.5, 30 sections + Appendices A–B covering detailed screen specs, validation rules, error codes, notification matrix, and the authoritative calculation catalogue). Refer to the full document for implementation-level formulas, field-level validation, and per-screen edge-case/error handling.*
