# Task Manager Module — Monthly Planning, Approval, Execution & Achievement

**Cart-free, van-free — pure workflow module — Implementation Specification**

*Sokrio Technology Limited · tenant-scoped module (all tenants) · Internal Technical Document*

> Modeled on `Van_Sales_Implementation.docx`'s format and depth. Where Van Sales needed a second
> per-tenant MySQL database and a connection-switching middleware, Task Manager does not — see
> §2 for why. Source material: `Sokrio-Task-Manager-Detailed-SRS.docx` (v1.5), `Sokrio-Task-Manager-
> All-Screens.pdf`, `task-manager-app.html` (prototype — visual reference only, several behaviors
> deliberately not copied, see §5.10 and Appendix C), and this repo's own prior research in
> `dev-story/doc/{business-srs,ui-spec,dev-plan}.md`, which this document supersedes.

---

## 1. Overview

This document is the complete implementation specification for the **Task Manager Module** within
the Sokrio DMS platform. It replaces spreadsheet-based monthly field-force planning (PJP —
Permanent Journey Plan) with a governed, in-app workflow covering catalogue management, monthly
plan creation (list + calendar), hierarchy-based submission and approval, subtask-driven execution
progress, and month-end achievement reporting.

It is an **org-scoped (tenant) module only** — no landlord/admin-panel surface, no separate
per-tenant database, no new mobile app connector. It ships inside `sokrio-server`'s existing
tenant MySQL database and `sokrio-app-frontend`.

Four concepts stay deliberately separate through the whole design — this separation drives the
schema in §4:

1. **Task classification** — Admin-managed Category → Type → Master Preset catalogue.
2. **Planned task instance** — an employee-specific date/target/owner/assignee row.
3. **Workflow state** — `DRAFT → SUBMITTED → APPROVED`, or `REJECTED` / `EXPIRED` / `ABANDONED` /
   `VOID`.
4. **Execution/result state** — `progress`, `execution_completed`, `achievement_status` — tracked
   independently of workflow state. Approval does not imply completion; completion does not imply
   achievement.

---

## 2. Database Architecture & Connection Layer

### 2.1 Single-Database Convention — no `_task` database

Unlike Van Sales (which provisions a dedicated `{tenantDb}_van` MySQL database because vendor/beat/
settlement data is high-volume, mobile-app-originated, and operationally separate from the core
DMS), Task Manager's data is:

- Low-to-moderate write volume (a few dozen tasks per user per month, not GPS-ping-frequency).
- Read/joined constantly against tenant-native entities that already live in the main tenant DB —
  `users`, `departments`, `territories`, `roles`/`permissions` — every list/dashboard/report query
  needs these joins.
- Naturally relational: generated/computed columns (subtask weight roll-up denominators, optimistic
  lock versions), `UNIQUE` constraints (one `user_supervisors` active row per user, comment nesting
  depth), and foreign keys with cascading integrity are a better fit for a single relational schema
  than a second database with cross-DB joins.

**Decision: all Task Manager tables live in the existing tenant MySQL connection**
(`TenantManager::CONN_TENANT = 'tenant'`), migrated via the standard `php artisan tenant:migrate
{dbName?}` command — no new Artisan command, no new connection config entry, no new middleware.

> **Architecture note (flag for Tech Lead sign-off):** `db-schema.md` documents that several
> comparable *workflow* domains in this codebase — `Claim`, `Complaint` — are stored in **MongoDB**
> (`App\Models\MongoDB\Claim\*`), not MySQL, following an older per-tenant-Mongo convention for
> transactional domains. Task Manager deliberately does **not** follow that precedent, for the
> relational-integrity reasons above — this matches the *newer* MySQL-relational convention seen in
> `van_*` and `central_entities` tables (`->foreignId()->constrained()`, generated columns). This is
> a real fork in the codebase's own conventions, not an oversight; it is listed as Open Item #1 in
> §10 so it gets an explicit sign-off rather than being assumed.

### 2.2 Model Base Pattern

No middleware or lazy-connection dance is needed — the tenant connection is already the Laravel
`database.default` for any authenticated tenant request (set by the existing `tenant` middleware
via `TenantManager::reconnect()`, same as every other tenant-scoped module). Models declare the
connection explicitly anyway, matching this codebase's existing convention (e.g. `App\Models\
Department\Department`):

```php
<?php

namespace App\Models\TaskManager;

use Illuminate\Database\Eloquent\Model;

class Task extends Model
{
    protected $connection = 'tenant';
    // ... fillable, casts, relations — see §4.7
}

// Every other Task Manager model (TaskCategory, TaskType, MasterTaskPreset,
// MasterTaskPresetSubtask, TaskManagerSetting, MonthlyCycle, TaskSubtask, TaskComment,
// TaskAttachment, TaskSavedPlan, TaskSavedPlanItem, UserSupervisor) follows the same pattern —
// no shared abstract base class is needed since there's no per-request connection-name
// resolution to centralize (unlike Van Sales' VanSalesModel, which exists specifically to
// encode the fmcg_van routing).
```

### 2.3 Route Registration

New domain-split route file, following the existing `acl.php` / `claim.php` / `order.php` / `van.php`
pattern rather than crowding `api.php`:

```php
// routes/api.php

Route::middleware(['auth:sanctum', 'tenant'])
    ->group(base_path('routes/task_manager.php'));
```

```php
// routes/task_manager.php
// Every route additionally gated by a specific `permission:` middleware entry — see §8's
// endpoint table for the exact constant per route. No module-assignment gate is needed (unlike
// Van Sales' CheckModuleAssigned) since Task Manager ships to every tenant, not an opt-in add-on
// — confirm this against Open Item #2 in §10 before Phase 1 ships, in case Product wants it
// gated as a paid add-on after all.

Route::prefix('task-manager')->group(function () {
    Route::apiResource('categories', TaskCategoryController::class)
        ->middleware('permission:viewTaskCategory,createTaskCategory,updateTaskCategory,deleteTaskCategory');
    // ... remaining routes, see §8
});
```

### 2.4 Migration Commands

No new Artisan commands. Task Manager migrations are ordinary tenant migrations:

```
# Standard tenant migration — no Task-Manager-specific command exists or is needed
php artisan tenant:migrate {dbName?}
```

---

## 3. Module Provisioning & Permissions

### 3.1 Provisioning

No `ProvisionTaskManagerDatabase`-style job is needed — the 13 tables (§4) are created for every
tenant the first time `tenant:migrate` runs after this module's migrations land, exactly like any
other core-schema addition. There is no per-org opt-in step unless Open Item #2 (§10) resolves in
favor of gating this as a licensed add-on, in which case a lightweight `org_modules` flag check
(reusing the existing landlord `modules`/`org_modules` tables Van Sales already established the
pattern for) would be added to the route middleware — not a second database.

### 3.2 Menus & Permission Gates

All roles, permissions, and access control live entirely in the tenant `Acl\Role`/`Acl\Permission`
system — exactly like every other Sokrio tenant module, and exactly like Van Sales' §5.2 pattern of
keeping RBAC in the main app rather than duplicating it.

- Task Manager navigation group visible in `sokrio-app-frontend` only when the authenticated user
  holds `viewTask` (or any of the module's permission constants — see §8).
- Sub-menu/action gates: `viewTaskCategory`, `createTask`, `updateTask`, `approveTaskPlan`,
  `assignTask`, `recordTaskAchievement`, `viewTeamTaskDashboard`, `taskPlanReport`,
  `userWiseTaskReport`, `manageTaskSettings` — full list in §8.
- No new role table, no fixed role enum. The SRS's "Team Member / Supervisor / Approver / Admin /
  Viewer" are **usage patterns** — typical permission bundles an org composes via the existing Role
  system — not literal DB rows, consistent with `acl-auth`'s established design in this workspace.

### 3.3 Permission Constants

Added to `App\Models\Acl\Permission` **and** `config/permissions.php`'s `abilities` array (both
required — a class constant alone does not register the permission). Checked against the existing
376-constant list in `.claude/_context/permission-list.md`; no near-duplicates found.

```php
// app/Models/Acl/Permission.php — additions

const VIEW_TASK_CATEGORY        = 'viewTaskCategory';
const CREATE_TASK_CATEGORY      = 'createTaskCategory';
const UPDATE_TASK_CATEGORY      = 'updateTaskCategory';
const DELETE_TASK_CATEGORY      = 'deleteTaskCategory';
const VIEW_TASK_TYPE            = 'viewTaskType';
const CREATE_TASK_TYPE          = 'createTaskType';
const UPDATE_TASK_TYPE          = 'updateTaskType';
const DELETE_TASK_TYPE          = 'deleteTaskType';
const VIEW_MASTER_TASK_PRESET   = 'viewMasterTaskPreset';
const CREATE_MASTER_TASK_PRESET = 'createMasterTaskPreset';
const UPDATE_MASTER_TASK_PRESET = 'updateMasterTaskPreset';
const DELETE_MASTER_TASK_PRESET = 'deleteMasterTaskPreset';
const VIEW_TASK                 = 'viewTask';
const CREATE_TASK               = 'createTask';
const UPDATE_TASK               = 'updateTask';
const DELETE_TASK               = 'deleteTask';
const APPROVE_TASK_PLAN         = 'approveTaskPlan';
const ASSIGN_TASK               = 'assignTask';
const RECORD_TASK_ACHIEVEMENT   = 'recordTaskAchievement';
const VIEW_TEAM_TASK_DASHBOARD  = 'viewTeamTaskDashboard';
const TASK_PLAN_REPORT          = 'taskPlanReport';
const USER_WISE_TASK_REPORT     = 'userWiseTaskReport';
const MANAGE_TASK_SETTINGS      = 'manageTaskSettings';
const VOID_TASK                 = 'voidTask';   // seeded now; endpoint ships in Phase 2 (§9)
```

---

## 4. Database Schema — tenant connection

All 13 tables below live in the existing tenant MySQL database, created via ordinary tenant
migrations. Key column legend: PK = Primary Key, FK = Foreign Key, UNIQUE = unique index,
INDEX = non-unique index, GEN = generated/computed column.

### 4.1 `task_categories`

Admin-managed top-level classification. Never contains employee-specific values (business rule:
catalogues stay generic, tasks hold the specifics).

| Column | Type / Constraint | Key | Notes |
|---|---|---|---|
| id | BIGINT UNSIGNED AUTO_INCREMENT | PK | |
| name | VARCHAR(100) NOT NULL | | e.g. "Merchandising" |
| code | VARCHAR(30) NOT NULL | UNIQUE | Stable machine key, independent of `name` |
| color | VARCHAR(7) NULL | | Hex, for UI chips/bars |
| sort_order | SMALLINT UNSIGNED DEFAULT 0 | | Display order |
| is_active | TINYINT(1) DEFAULT 1 | | Deactivation blocks new use, never rewrites history |
| created_by | BIGINT UNSIGNED NOT NULL | FK→users | |
| created_at / updated_at | TIMESTAMP NULL | | |

### 4.2 `task_types`

| Column | Type / Constraint | Key | Notes |
|---|---|---|---|
| id | BIGINT UNSIGNED AUTO_INCREMENT | PK | |
| task_category_id | BIGINT UNSIGNED NOT NULL | FK→task_categories | |
| name | VARCHAR(100) NOT NULL | | |
| code | VARCHAR(30) NOT NULL | UNIQUE | |
| frequency | ENUM('daily','weekly','monthly') NOT NULL | | Informational default only — does not drive recurrence generation in v1 (see §10 Future Scope) |
| is_active | TINYINT(1) DEFAULT 1 | | |
| created_at / updated_at | TIMESTAMP NULL | | |

### 4.3 `master_task_presets`

Reusable templates a team member picks from when building a plan, or a supervisor picks when
assigning a task.

| Column | Type / Constraint | Key | Notes |
|---|---|---|---|
| id | BIGINT UNSIGNED AUTO_INCREMENT | PK | |
| task_type_id | BIGINT UNSIGNED NOT NULL | FK→task_types | |
| task_category_id | BIGINT UNSIGNED NOT NULL | FK→task_categories | Denormalized for query speed — category is derivable via type, kept directly for list/filter performance |
| title | VARCHAR(150) NOT NULL | | |
| objective | TEXT NULL | | |
| default_priority | ENUM('low','medium','high','critical') NOT NULL | | |
| default_target | DECIMAL(10,2) NULL | | Prefilled, editable per task instance |
| is_active | TINYINT(1) DEFAULT 1 | | |
| created_by | BIGINT UNSIGNED NOT NULL | FK→users | |
| created_at / updated_at | TIMESTAMP NULL | | |

### 4.4 `master_task_preset_subtasks`

Template subtask list copied (not referenced) onto a `Task` when created from this preset —
`tasks.master_task_preset_id` is a snapshot source, never a live reference (catalogue edits must
never retroactively alter already-planned tasks).

| Column | Type / Constraint | Key | Notes |
|---|---|---|---|
| id | BIGINT UNSIGNED AUTO_INCREMENT | PK | |
| master_task_preset_id | BIGINT UNSIGNED NOT NULL | FK→master_task_presets | |
| title | VARCHAR(150) NOT NULL | | |
| sort_order | SMALLINT UNSIGNED DEFAULT 0 | | |
| created_at / updated_at | TIMESTAMP NULL | | |

### 4.5 `task_manager_settings`

One row per tenant. Drives §6's phase-transition job.

| Column | Type / Constraint | Key | Notes |
|---|---|---|---|
| id | BIGINT UNSIGNED AUTO_INCREMENT | PK | |
| planning_start_day | TINYINT UNSIGNED DEFAULT 1 | | Day-of-month, planning window opens |
| planning_end_day | TINYINT UNSIGNED DEFAULT 25 | | Submission cutoff |
| approval_end_day | TINYINT UNSIGNED DEFAULT 28 | | Unresolved Submitted → Expired after this |
| review_start_day | TINYINT UNSIGNED DEFAULT 1 | | Day of month M+2 |
| review_end_day | TINYINT UNSIGNED DEFAULT 5 | | Day of month M+2 |
| timezone | VARCHAR(50) DEFAULT 'Asia/Dhaka' | | All boundaries evaluated in this org timezone |
| future_horizon_months | TINYINT UNSIGNED DEFAULT 1 | | How many months ahead planning is open |
| created_at / updated_at | TIMESTAMP NULL | | |

### 4.6 `monthly_cycles`

One row per calendar month per tenant. `cycle_id` (the row's `id`) is the authoritative reference
everywhere — `period` is a display label only, never used for phase logic.

| Column | Type / Constraint | Key | Notes |
|---|---|---|---|
| id | BIGINT UNSIGNED AUTO_INCREMENT | PK | Authoritative `cycle_id` |
| period | DATE NOT NULL | UNIQUE | First-of-month, display label |
| status | ENUM('planning','approval','execution','review','archived') NOT NULL | INDEX | |
| locked_at | TIMESTAMP NULL | | Set on archive |
| created_at / updated_at | TIMESTAMP NULL | | |

Rows are created lazily (find-or-create on first task write for a period) or by the daily
`AdvanceMonthlyCyclePhase` command (§6.1), which also advances `status` for all existing rows.

### 4.7 `tasks`

The core entity. Carries planned fields (immutable once Approved), workflow state, and
execution/achievement state as independent column groups per the four-concept split in §1.

| Column | Type / Constraint | Key | Notes |
|---|---|---|---|
| id | BIGINT UNSIGNED AUTO_INCREMENT | PK | |
| monthly_cycle_id | BIGINT UNSIGNED NOT NULL | FK→monthly_cycles | |
| task_category_id | BIGINT UNSIGNED NOT NULL | FK→task_categories | |
| task_type_id | BIGINT UNSIGNED NULL | FK→task_types | |
| master_task_preset_id | BIGINT UNSIGNED NULL | FK→master_task_presets | Snapshot source, not a live reference |
| owner_id | BIGINT UNSIGNED NOT NULL | FK→users, INDEX | Whose plan this belongs to |
| assignee_id | BIGINT UNSIGNED NULL | FK→users | Defaults to `owner_id` if null |
| created_by | BIGINT UNSIGNED NOT NULL | FK→users | |
| assigned_by | BIGINT UNSIGNED NULL | FK→users | Set only on supervisor-assigned tasks — see §5.5 |
| title | VARCHAR(150) NOT NULL | | Planned field — locked at Approved |
| objective | TEXT NULL | | Planned field |
| priority | ENUM('low','medium','high','critical') NOT NULL | | Planned field |
| planned_date | DATE NOT NULL | | Planned field |
| department_id | BIGINT UNSIGNED NULL | FK→departments | The SRS's "distributor/outlet" — reuses the existing `Department` model, not a new entity |
| planned_target | DECIMAL(10,2) NULL | | Planned field |
| actual_target | DECIMAL(10,2) NULL | | Execution-phase field |
| remarks | TEXT NULL | | |
| status | ENUM('draft','submitted','approved','rejected','expired','abandoned','void') DEFAULT 'draft' | INDEX | |
| rejection_reason | TEXT NULL | | 10–500 chars, required on reject/return |
| progress | TINYINT UNSIGNED DEFAULT 0 | | Derived from subtasks when any exist — see §5.7 |
| execution_completed | TINYINT(1) DEFAULT 0 | | |
| execution_completed_at | TIMESTAMP NULL | | |
| execution_completed_by | BIGINT UNSIGNED NULL | FK→users | |
| achievement_status | ENUM('pending','achieved','partially_achieved','not_achieved') DEFAULT 'pending' | | Never equals owner's own self-recording — see §5.9 |
| achievement_recorded_by | BIGINT UNSIGNED NULL | FK→users | |
| achievement_recorded_at | TIMESTAMP NULL | | |
| achievement_locked_at | TIMESTAMP NULL | | Set by the archive job — see Open Item #3, §10 |
| submitted_at | TIMESTAMP NULL | | |
| approved_at | TIMESTAMP NULL | | |
| approved_by | BIGINT UNSIGNED NULL | FK→users | Can never equal `owner_id` — enforced server-side |
| voided_at | TIMESTAMP NULL | | |
| voided_by | BIGINT UNSIGNED NULL | FK→users | Admin only |
| void_reason | TEXT NULL | | Required when voided |
| version | INT UNSIGNED DEFAULT 1 | | Optimistic lock — every write increments, checked on write |
| created_at / updated_at | TIMESTAMP NULL | | |
| deleted_at | TIMESTAMP NULL | | Soft delete |

Indexes: `(monthly_cycle_id, owner_id)`, `(monthly_cycle_id, status)`, `(assignee_id, status)`.

### 4.8 `task_subtasks`

One level only — no recursive subtasks (out of scope per SRS §2). Roll-up logic in §5.7.

| Column | Type / Constraint | Key | Notes |
|---|---|---|---|
| id | BIGINT UNSIGNED AUTO_INCREMENT | PK | |
| task_id | BIGINT UNSIGNED NOT NULL | FK→tasks | |
| title | VARCHAR(150) NOT NULL | | |
| sort_order | SMALLINT UNSIGNED DEFAULT 0 | | |
| weight | DECIMAL(5,2) NULL | | NULL = equal-weight roll-up; if set, all of a task's subtask weights must sum to exactly 100.00 |
| is_done | TINYINT(1) DEFAULT 0 | | |
| completed_by | BIGINT UNSIGNED NULL | FK→users | |
| completed_at | TIMESTAMP NULL | | |
| created_at / updated_at | TIMESTAMP NULL | | |

### 4.9 `task_comments`

Exactly one level of replies, enforced server-side (§5.10). Tombstoned on delete, never hard-deleted.

| Column | Type / Constraint | Key | Notes |
|---|---|---|---|
| id | BIGINT UNSIGNED AUTO_INCREMENT | PK | |
| task_id | BIGINT UNSIGNED NOT NULL | FK→tasks, INDEX | |
| user_id | BIGINT UNSIGNED NOT NULL | FK→users | |
| parent_id | BIGINT UNSIGNED NULL | FK→task_comments | Must reference a top-level comment (`parent_id IS NULL`); a reply-to-reply is rejected server-side |
| body | TEXT NOT NULL | | Blanked on delete |
| edited_at | TIMESTAMP NULL | | |
| deleted_at | TIMESTAMP NULL | | Tombstone — row and thread position survive |
| created_at / updated_at | TIMESTAMP NULL | | |

### 4.10 `task_attachments`

| Column | Type / Constraint | Key | Notes |
|---|---|---|---|
| id | BIGINT UNSIGNED AUTO_INCREMENT | PK | |
| task_id | BIGINT UNSIGNED NOT NULL | FK→tasks | |
| uploaded_by | BIGINT UNSIGNED NOT NULL | FK→users | |
| disk_path | VARCHAR(500) NOT NULL | | S3/Spaces path, matches existing upload convention |
| file_name | VARCHAR(255) NOT NULL | | |
| file_size | BIGINT UNSIGNED NOT NULL | | Bytes |
| mime_type | VARCHAR(100) NOT NULL | | |
| created_at / updated_at | TIMESTAMP NULL | | |

Upload only enabled when `status = approved` AND current user is owner/assignee AND within the
Execution window (execution-proof attachments); reviewing roles see the list read-only.

### 4.11 `task_saved_plans` / 4.12 `task_saved_plan_items`

"Reuse a plan" — a lighter-weight stand-in for the SRS's `SavedMonthlyPlan` entity (see Open Item
#4, §10, on whether multiple named plans should actually be exposed in the UI).

| `task_saved_plans` | Type / Constraint | Key | Notes |
|---|---|---|---|
| id | BIGINT UNSIGNED AUTO_INCREMENT | PK | |
| owner_id | BIGINT UNSIGNED NOT NULL | FK→users | |
| name | VARCHAR(100) NOT NULL | | |
| created_at / updated_at | TIMESTAMP NULL | | |

| `task_saved_plan_items` | Type / Constraint | Key | Notes |
|---|---|---|---|
| id | BIGINT UNSIGNED AUTO_INCREMENT | PK | |
| task_saved_plan_id | BIGINT UNSIGNED NOT NULL | FK→task_saved_plans | |
| task_category_id | BIGINT UNSIGNED NOT NULL | FK→task_categories | |
| task_type_id | BIGINT UNSIGNED NULL | FK→task_types | |
| master_task_preset_id | BIGINT UNSIGNED NULL | FK→master_task_presets | |
| title | VARCHAR(150) NOT NULL | | |
| department_id | BIGINT UNSIGNED NULL | FK→departments | |
| default_target | DECIMAL(10,2) NULL | | |
| priority | ENUM('low','medium','high','critical') NOT NULL | | |
| created_at / updated_at | TIMESTAMP NULL | | |

### 4.13 `user_supervisors`

The SRS's `ReportingRelationship` — answers "whose plan can I approve/assign," independent of the
Department/Territory hierarchy (which answers "where does this org's data live"). See §5.5 for how
this scopes approval.

| Column | Type / Constraint | Key | Notes |
|---|---|---|---|
| id | BIGINT UNSIGNED AUTO_INCREMENT | PK | |
| supervisor_id | BIGINT UNSIGNED NOT NULL | FK→users | |
| user_id | BIGINT UNSIGNED NOT NULL | FK→users | The direct report |
| effective_from | DATE NOT NULL | | |
| effective_to | DATE NULL | | NULL = currently active |
| status | ENUM('active','inactive') DEFAULT 'active' | | |
| created_at / updated_at | TIMESTAMP NULL | | |

App-enforced (not DB-enforced) invariant: a given `user_id` has at most one row with
`effective_to IS NULL AND status = 'active'` at a time.

> **Before building this table** (flagged in `dev-plan.md`, carried forward as Open Item #5, §10):
> check whether an equivalent direct-report/reporting-line table already exists elsewhere in the
> codebase (e.g. under HR/attendance/target modules) — this must not become a second, divergent
> source of truth for "who reports to whom."

---

## 5. Core Workflow — Deep Dives with Reference Implementation

### 5.1 Catalogue Management

Standard admin CRUD on `task_categories` → `task_types` → `master_task_presets` (+ template
`master_task_preset_subtasks`). Deactivation (`is_active = 0`) blocks new selection but must never
rewrite or hide already-planned tasks that reference a since-deactivated category/type/preset —
enforced by never cascading `is_active` checks onto existing `Task` rows, only onto the
create/picker endpoints.

### 5.2 Monthly Cycle State Machine

A single daily scheduled command reads `task_manager_settings` per tenant and advances every
`monthly_cycles` row, plus sweeps task-level phase-boundary transitions.

```php
<?php

namespace App\Console\Commands;

use App\Models\TaskManager\MonthlyCycle;
use App\Models\TaskManager\Task;
use App\Models\TaskManager\TaskManagerSetting;
use Illuminate\Console\Command;
use Illuminate\Support\Facades\DB;

class AdvanceMonthlyCyclePhase extends Command
{
    protected $signature = 'task-manager:advance-cycle-phase';

    /**
     * Runs once daily, per tenant (dispatched per-org via the existing tenant-loop
     * scheduler pattern). All boundary comparisons use the org's configured timezone —
     * never server/UTC time — per SRS phase-window rules.
     */
    public function handle(): void
    {
        $settings = TaskManagerSetting::first();
        $today = now($settings->timezone);

        DB::connection('tenant')->transaction(function () use ($settings, $today) {

            // 1. Unresolved Submitted tasks past the approval window → Expired.
            //    Owner cannot self-revive; only Admin Void remains (Phase 2).
            if ($today->day > $settings->approval_end_day) {
                Task::whereHas('monthlyCycle', fn ($q) => $q->where('status', 'approval'))
                    ->where('status', 'submitted')
                    ->update(['status' => 'expired']);
            }

            // 2. Draft/Rejected tasks that were never submitted, at archive → Abandoned.
            if ($today->day === /* archive day, from cycle */ 6) {
                Task::whereHas('monthlyCycle', fn ($q) => $q->where('status', 'review'))
                    ->whereIn('status', ['draft', 'rejected'])
                    ->update(['status' => 'abandoned']);

                // 3. Unreviewed Approved tasks at archive → auto NOT_ACHIEVED (audited).
                //    achievement_locked_at guards against silent overwrite — see §5.9 and
                //    Open Item #3.
                Task::whereHas('monthlyCycle', fn ($q) => $q->where('status', 'review'))
                    ->where('status', 'approved')
                    ->where('achievement_status', 'pending')
                    ->update([
                        'achievement_status' => 'not_achieved',
                        'achievement_locked_at' => now(),
                    ]);
            }

            // 4. Advance monthly_cycles.status for every row whose period's phase window
            //    has changed, based on $settings' day thresholds.
            MonthlyCycle::query()->cursor()->each(function (MonthlyCycle $cycle) use ($settings, $today) {
                $cycle->update(['status' => $cycle->resolvePhase($settings, $today)]);
            });
        });
    }
}
```

### 5.3 Personal Planning — List & Calendar, Reuse & Bulk Add

Standard CRUD against `tasks` scoped to `monthly_cycle_id + owner_id`. Calendar bulk-add
(multi-select Master Preset picker → one task per selected date) reuses the same atomic-transaction
pattern as full-plan submit (§5.4) — either all requested task rows are created, or none are, with
field-level errors per rejected row.

"Copy Previous Month" and "Use Saved Plan" (`task_saved_plans`) both materialize into fresh
`Draft` `tasks` rows for the target cycle — they never reference or mutate the source month's
already-existing tasks.

### 5.4 Full-Plan Submission — Atomic

"Submit Full Plan" transitions every eligible `Draft`/`Rejected` task for the owner+cycle to
`Submitted` in one transaction. On any single task failing validation (missing weight sum, missing
required field), zero tasks transition — the whole action fails with per-task field errors.

```php
<?php

namespace App\Services\TaskManager;

use App\Models\TaskManager\Task;
use Illuminate\Support\Facades\DB;
use Illuminate\Validation\ValidationException;

class TaskPlanService
{
    /**
     * Atomically submits every Draft/Rejected task for $ownerId in $cycleId.
     * Zero transitions on any single-task validation failure — never a partial submit.
     */
    public function submitFullPlan(int $ownerId, int $cycleId): void
    {
        $tasks = Task::where('monthly_cycle_id', $cycleId)
            ->where('owner_id', $ownerId)
            ->whereIn('status', ['draft', 'rejected'])
            ->with('subtasks')
            ->get();

        $errors = [];
        foreach ($tasks as $task) {
            $weighted = $task->subtasks->whereNotNull('weight');
            if ($weighted->isNotEmpty() && round((float) $weighted->sum('weight'), 2) !== 100.00) {
                $errors[$task->id] = "Subtask weights for \"{$task->title}\" must sum to 100.";
            }
        }
        if ($errors) {
            throw ValidationException::withMessages($errors); // 422 — nothing transitions
        }

        DB::connection('tenant')->transaction(function () use ($tasks) {
            foreach ($tasks as $task) {
                $task->update([
                    'status' => 'submitted',
                    'submitted_at' => now(),
                    'version' => $task->version + 1,
                ]);
            }
        });
    }
}
```

### 5.5 Approval — Full-Plan Block on Outstanding Assigned Tasks

"Approve Full Plan" must reject with a clear count if the owner has any `Draft`/`Rejected` task
where `assigned_by IS NOT NULL` — a supervisor-assigned task the owner hasn't yet actioned.
"Approve Selected" on the ready subset is always allowed. There is no separate `plan.status`
column — plan state is always derived from the owner+cycle's task rows.

```php
class TaskPlanService
{
    // ...

    public function approveFullPlan(int $ownerId, int $cycleId, int $approverId): void
    {
        if ($ownerId === $approverId) {
            abort(403, 'Self-approval is not permitted.'); // BR-06, enforced regardless of role
        }

        $outstandingAssigned = Task::where('monthly_cycle_id', $cycleId)
            ->where('owner_id', $ownerId)
            ->whereNotNull('assigned_by')
            ->whereIn('status', ['draft', 'rejected'])
            ->count();

        if ($outstandingAssigned > 0) {
            abort(422, "{$outstandingAssigned} supervisor-assigned task(s) have not yet been "
                . 'actioned by the owner — resolve those before approving the full plan.');
        }

        DB::connection('tenant')->transaction(function () use ($ownerId, $cycleId, $approverId) {
            Task::where('monthly_cycle_id', $cycleId)
                ->where('owner_id', $ownerId)
                ->where('status', 'submitted')
                ->update([
                    'status' => 'approved',
                    'approved_at' => now(),
                    'approved_by' => $approverId,
                ]);
        });
    }
}
```

Assigning a task to a direct report (`ASSIGN_TASK`) is **not** an approval — it creates a normal
owner-owned `Draft` with `assigned_by` + an assignment note; it still flows through the full
submit → approve cycle like any self-planned task.

### 5.6 Approved-Field Immutability

Once `status = approved`, planned fields (`title`, `task_category_id`, `task_type_id`,
`planned_date`, `planned_target`, `department_id`, `priority`) can never be edited by anyone,
including Admin — enforced in the service layer with a `409`, not a disabled UI button. Only
`progress`, subtask completion, `execution_completed*`, attachments, and (during the Review window)
achievement fields may still change.

```php
class TaskController extends Controller
{
    public function update(UpdateTaskRequest $request, Task $task)
    {
        $lockedFields = ['title', 'task_category_id', 'task_type_id', 'planned_date',
                          'planned_target', 'department_id', 'priority'];

        if ($task->status === 'approved'
            && array_intersect($lockedFields, array_keys($request->validated()))) {
            abort(409, 'Approved planned fields are immutable.');
        }

        $task->update($request->validated());

        return TaskResource::make($task);
    }
}
```

### 5.7 Subtask Progress Roll-Up

Manual progress input is only usable when a task has zero subtasks (business rule: any subtask
row present means `progress` is fully derived, never manually set).

```php
<?php

namespace App\Services\TaskManager;

use App\Models\TaskManager\Task;

class TaskProgressService
{
    public function recompute(Task $task): int
    {
        $subtasks = $task->subtasks;

        if ($subtasks->isEmpty()) {
            return $task->progress; // manual slider value, untouched here
        }

        $weighted = $subtasks->whereNotNull('weight');

        if ($weighted->isNotEmpty()) {
            // Weighted roll-up: Σ(weight_i × done_i). Weights must sum to 100 to be a valid
            // Submit/Approve state (enforced at submit time, §5.4) — mid-edit sums under 100
            // are allowed to save as Draft.
            $progress = (int) round($weighted->sum(fn ($s) => $s->is_done ? $s->weight : 0));
        } else {
            // Equal-weight roll-up, round-half-up.
            $done = $subtasks->where('is_done', true)->count();
            $progress = (int) round(($done / $subtasks->count()) * 100);
        }

        $task->update(['progress' => $progress]);

        return $progress;
    }
}
```

### 5.8 Execution — Mark Complete

Mark Complete does **not** set achievement — it atomically sets `progress = 100`, all subtasks
`is_done = true`, `execution_completed = true` + actor/time. Achievement is a distinct, later
action (§5.9).

### 5.9 Achievement Recording

Achievement must be a real recorded action with actor + timestamp — never silently derived and
displayed as if saved (a gap in the interactive prototype, deliberately not carried into the real
build — see Appendix C).

```php
<?php

namespace App\Services\TaskManager;

use App\Models\TaskManager\Task;

class TaskAchievementService
{
    /**
     * Records achievement for an Approved task during the Review window.
     * Validated against final progress per SRS Appendix B.10.1:
     *   progress = 100        → ACHIEVED
     *   0 < progress < 100    → PARTIALLY_ACHIEVED
     *   progress = 0          → NOT_ACHIEVED
     * The caller-supplied $status must match this derivation — it is a confirmation
     * action, not a free-text override.
     */
    public function record(Task $task, string $status, int $recorderId): void
    {
        if ($task->owner_id === $recorderId) {
            abort(403, 'Self-recording achievement is not permitted.'); // BR-06 applies here too
        }
        if ($task->status !== 'approved') {
            abort(422, 'Only Approved tasks can have achievement recorded.');
        }
        if ($task->achievement_locked_at !== null) {
            abort(409, 'Achievement is locked — see the reopen decision in Open Item #3.');
        }

        $expected = match (true) {
            $task->progress === 100 => 'achieved',
            $task->progress > 0     => 'partially_achieved',
            default                 => 'not_achieved',
        };
        if ($status !== $expected) {
            abort(422, "Recorded status must match derived outcome ({$expected}).");
        }

        $task->update([
            'achievement_status' => $status,
            'achievement_recorded_by' => $recorderId,
            'achievement_recorded_at' => now(),
        ]);
    }
}
```

### 5.10 Comments — One-Level Nesting, Tombstone Delete

A reply's `parent_id` must point at a top-level comment (`parent_id IS NULL`); replying to a reply
is rejected server-side with a `422` — the interactive prototype does not enforce this, so it must
not be treated as a reference for backend behavior, only for the UI's visual thread layout.

```php
class TaskCommentController extends Controller
{
    public function store(StoreTaskCommentRequest $request, Task $task)
    {
        if ($parentId = $request->input('parent_id')) {
            $parent = TaskComment::findOrFail($parentId);
            if ($parent->parent_id !== null) {
                abort(422, 'Replies may only be one level deep.');
            }
        }

        return TaskCommentResource::make(
            $task->comments()->create($request->validated() + ['user_id' => auth()->id()])
        );
    }

    public function destroy(TaskComment $comment)
    {
        abort_unless($comment->user_id === auth()->id(), 403);

        $comment->update(['body' => '', 'deleted_at' => now()]); // tombstone, not a hard delete
    }
}
```

---

## 6. Reporting & Analytics

| Report / View | Description | Format | Scope |
|---|---|---|---|
| My Dashboard | KPI cards (awaiting approval, approved, achievement rate, total), category bar, last-month outcome donut, cycle timeline | In-page | Own tasks, current cycle |
| Team Dashboard | Real Department/Territory hierarchy filter, team KPIs, submission-status-by-area, achievement distribution | In-page | `viewTeamTaskDashboard` scope |
| Category Allocation | Plan breakdown by category — always full-plan scope, ignores active list filters (business rule 13) | In-page | Cycle + owner/team |
| Plan vs Achievement Summary | Achievement Rate = (Achieved+Partial) / Reportable-Approved × 100 | Excel / CSV / PDF | Selected past cycle, archived cycles frozen/labeled "Final" |
| User-wise Task Report | Per-user, per-task table — created/due/completed dates, remarks, attachment count+download | Excel / PDF / Print | `userWiseTaskReport` scope |
| Team Submission Dashboard | Supervisor visibility into per-member submission status; Send Reminder (stubbed until Notification Centre ships, §9), Export | Excel | Direct reports (`user_supervisors`) or department-wide |

Zero/null denominators return `N/A`, never a misleading 0% (carried from the SRS's calculation
governance rules — Appendix B of the original SRS is authoritative for any future formula change).

---

## 7. System Settings

Stored in `task_manager_settings` (§4.5), one row per tenant, editable via the Configuration screen
(`manageTaskSettings`).

| Setting | Label | Default | Type |
|---|---|---|---|
| planning_start_day | Planning window start day | 1 | Integer (day of month) |
| planning_end_day | Planning window end day (submission cutoff) | 25 | Integer |
| approval_end_day | Approval window end day | 28 | Integer |
| review_start_day | Review window start day (month M+2) | 1 | Integer |
| review_end_day | Review window end day (month M+2) | 5 | Integer |
| timezone | Org timezone for all phase boundaries | Asia/Dhaka | Timezone string |
| future_horizon_months | How many months ahead planning is open | 1 | Integer (months) |

---

## 8. API Endpoint Reference

All endpoints below are prefixed with `/task-manager`. Middleware stack:
`auth:sanctum → tenant → permission:<constant>` — no connection-switching middleware is needed
(§2).

| Method | Endpoint | Description | Permission |
|---|---|---|---|
| GET / POST | `/categories` | List / create Task Categories | `viewTaskCategory` / `createTaskCategory` |
| PATCH / DELETE | `/categories/{id}` | Update / deactivate a category | `updateTaskCategory` / `deleteTaskCategory` |
| GET / POST | `/types` | List / create Task Types | `viewTaskType` / `createTaskType` |
| PATCH / DELETE | `/types/{id}` | Update / deactivate a type | `updateTaskType` / `deleteTaskType` |
| GET / POST | `/presets` | List / create Master Task Presets (+ template subtasks) | `viewMasterTaskPreset` / `createMasterTaskPreset` |
| PATCH / DELETE | `/presets/{id}` | Update / deactivate a preset | `updateMasterTaskPreset` / `deleteMasterTaskPreset` |
| GET / POST | `/tasks` | List (filter/sort/search) / create a task | `viewTask` / `createTask` |
| GET / PATCH / DELETE | `/tasks/{id}` | Task detail / update / delete | `viewTask` / `updateTask` (+ ownership) |
| POST | `/plans/submit` | Atomic full-plan submit (§5.4) | `createTask` (+ ownership) |
| POST | `/plans/{ownerId}/approve-selected` | Approve chosen tasks only | `approveTaskPlan` |
| POST | `/plans/{ownerId}/approve-full` | Atomic full-plan approve, blocked on outstanding assigned tasks (§5.5) | `approveTaskPlan` |
| POST | `/plans/{ownerId}/return` | Return for revision — reason required, 10–500 chars | `approveTaskPlan` |
| POST | `/tasks/{id}/assign` | Supervisor/Admin creates an attributed Draft for a direct report | `assignTask` |
| PATCH | `/tasks/{id}/progress` | Manual progress update (zero-subtask tasks only, §5.7) | `updateTask` (+ ownership) |
| POST | `/tasks/{id}/complete` | Mark Complete (§5.8) | `updateTask` (+ ownership) |
| POST | `/tasks/{id}/achievement` | Record achievement (§5.9) | `recordTaskAchievement` |
| GET / POST | `/tasks/{id}/subtasks` | List / add subtasks | `viewTask` / `updateTask` |
| PATCH / DELETE | `/tasks/{id}/subtasks/{subId}` | Update / remove a subtask | `updateTask` |
| GET / POST | `/tasks/{id}/comments` | List / post comments (one-level replies, §5.10) | `viewTask` / `createTask` |
| PATCH / DELETE | `/tasks/{id}/comments/{cid}` | Edit / tombstone-delete own comment | own comment only |
| GET / POST | `/tasks/{id}/attachments` | List / upload execution-proof attachments | `viewTask` / `updateTask` (+ owner/assignee + Execution window) |
| DELETE | `/tasks/{id}/attachments/{aid}` | Remove own upload | uploader only |
| GET | `/calendar` | Calendar-view task set for a cycle | `viewTask` |
| POST | `/calendar/bulk-add` | Atomic multi-date bulk-add from Master Preset picker | `createTask` |
| GET | `/dashboard` | My Tasks dashboard KPIs | `viewTask` |
| GET | `/dashboard/team` | Team Overview dashboard | `viewTeamTaskDashboard` |
| GET | `/reports/summary` | Plan vs achievement summary export | `taskPlanReport` |
| GET | `/reports/user-wise` | User-wise task report export | `userWiseTaskReport` |
| GET / POST | `/saved-plans` | List / save a named plan | `createTask` (+ ownership) |
| POST | `/saved-plans/{id}/apply` | Materialize a saved plan into Draft tasks for a cycle | `createTask` (+ ownership) |
| DELETE | `/saved-plans/{id}` | Delete a saved plan | ownership only |
| GET / PATCH | `/settings` | View / update cycle-window configuration | `manageTaskSettings` |
| GET / POST | `/supervisors` | List / create direct-report links | `manageTaskSettings` (verify no equivalent endpoint exists first — Open Item #5) |

---

## 9. Implementation Timeline & Status

| Phase | Tasks | Status |
|---|---|---|
| Phase 1a — DB + Models | 13 migrations (§4) + Eloquent models/relations | Pending |
| Phase 1b — Backend API | Permission constants + seeding, controllers/services/routes (§3, §5, §8), `AdvanceMonthlyCyclePhase` daily command | Pending |
| Phase 1c — Frontend | Dashboard, My Tasks (List/Calendar), Team Dashboard, Approvals, Progress & Review, Reports, User-wise Report, Task Types, Configuration — wired to real endpoints, no mock data anywhere | Pending |
| Phase 1d — Tests | Feature tests per controller + explicit tests for the easy-to-regress rules: self-approval 403, approved-field immutability 409, atomic submit rollback, approve-full block on outstanding assigned task, subtask weight-sum validation, one-level comment nesting rejection | Pending |
| Phase 2 — Deferred | Notification Centre, Workbook Import (Preview→mapping/diff→Commit), Admin Void endpoint/UI (schema ships in Phase 1), full append-only audit trail, org-wide hierarchy analytics polish, WCAG 2.2 AA deep pass | Not started |

Per this repo's Do Not rules: DB/model, backend API, and frontend phases are built and confirmed
**one at a time**, never combined in one shot.

---

## 10. Open Items & Decisions Required

| # | Item | Owner | Due |
|---|---|---|---|
| 1 | Sign off on MySQL-relational (not per-tenant Mongo, unlike `Claim`/`Complaint`) as the storage layer — see architecture note in §2.1 | Tech Lead | TBD |
| 2 | Confirm whether Task Manager ships to every tenant by default, or is gated as a licensed add-on (affects §3.1 provisioning) | Product | TBD |
| 3 | Decide whether a late achievement edit after archive auto-sets `NOT_ACHIEVED` should be allowed via an explicit Admin-only "reopen" action, or stay permanently locked — affects whether `achievement_locked_at` needs an "unlock" endpoint in Phase 1 | Product | TBD |
| 4 | Confirm whether the UI should expose multiple named saved plans, or just "overwrite the one reusable plan" — `task_saved_plans` already supports multiple, confirm `ui-spec.md` matches | Product / UI | TBD |
| 5 | Verify no equivalent direct-report/reporting-line table already exists elsewhere in the codebase before building `user_supervisors` | Backend | Start of Phase 1b |
| 6 | Confirm the exact list of near-duplicate permission checks against `.claude/_context/permission-list.md` at build time (checked once during this research pass — recheck if the constant list has moved) | Backend | Start of Phase 1b |
| 7 | Notification Centre delivery channel/timing (email/in-app/SMS) — needed before "Send Reminder" on the Team Submission Dashboard can be un-stubbed | Product | Phase 2 kickoff |

---

## Appendix A — Glossary

| Term | Definition |
|---|---|
| PJP | Permanent Journey Plan — the spreadsheet-based process this module replaces |
| Cycle | One calendar month's Planning→Approval→Execution→Review→Archive lifecycle, keyed by `monthly_cycles.id` (the authoritative `cycle_id`), not the display `period` label |
| Master Task Preset | Admin-managed reusable task template; snapshotted (not live-referenced) onto tasks created from it |
| Direct Report | A user whose plan a given supervisor can approve/assign, per an active `user_supervisors` row |
| Achievement | An explicit, recorded month-end outcome (Achieved / Partially Achieved / Not Achieved) for an Approved task — independent of `execution_completed` |
| Approved-field immutability | Once a task is Approved, its planned fields can never be edited by anyone, enforced with a 409 at the service layer |
| Full-Plan Submit | Atomic transition of every eligible Draft/Rejected task for an owner+cycle to Submitted in one transaction |
| Category Allocation | The plan-by-category breakdown, always computed against the full plan regardless of active list filters |

## Appendix B — Revision History

| Ver | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-08-17 | Sokrio R&D | Initial `business-srs.md`/`ui-spec.md`/`dev-plan.md` research pass from source SRS + screens + prototype |
| 2.0 | 2026-08-19 | Sokrio R&D | Full rewrite into Van-Sales-format Implementation Specification — DB architecture rationale, per-table schema, reference-implementation code for the six trickiest business rules, full endpoint reference, phased timeline, open items. Supersedes `dev-plan.md` as the authoritative build reference. |

## Appendix C — Prototype Fidelity Notes (do not copy into the real build)

The interactive prototype (`task-manager-app.html`) diverges from this spec in several places —
treat it as visual/interaction reference only:

- Team Dashboard's hierarchy filter is a hardcoded Region→Area→Territory tree with
  `Math.random()`-generated KPIs — the real build uses actual Department/Territory data (§4.7,
  §6).
- Achievement outcome is derived live from `progress` and never actually saved — §5.9 requires an
  explicit, recorded action.
- Self-approval/attachment-edit gating checks a role-**name** string, not ownership + permission —
  §5.5/§5.6 use ownership+permission checks exclusively.
- No `weight` field on subtasks (equal-weight only), no EXPIRED/ABANDONED/VOID states anywhere in
  its JS — §4.8 and §4.7 add both.
- Comment nesting depth is not enforced — §5.10 enforces it server-side.
