# X-SENTINEL V2 Data Dictionary

Schema revision: `0001_v2_multiuser`.

## `users`
Purpose: stable identity record for durable multi-user ownership and audit attribution.

| Column | Type | Null | Key/Rule |
|---|---|---:|---|
| id | UUID | no | PK |
| email | varchar(320) | no | display/original email |
| normalized_email | varchar(320) | no | UNIQUE; application must lowercase/normalize |
| display_name | varchar(200) | yes | optional |
| is_active | boolean | no | default true |
| created_at/updated_at | timestamptz | no | timestamps |

## `roles`
Purpose: canonical role catalog. Initial values: `admin`, `analyst`, `evaluator`.

## `user_roles`
Purpose: many-to-many RBAC assignment. Composite PK `(user_id, role_id)`.

## `model_versions`
Purpose: bind every durable analysis to an identifiable model/config artifact. Unique `(name, version)`; stores SHA-256 and config hash.

## `analysis_jobs`
Purpose: durable lifecycle of each submitted analysis.

Important rules:
- `request_id` is unique for idempotency/traceability.
- status is constrained to `queued|running|completed|failed|quarantined`.
- input mode is `vector|raw_pe`.
- input payload itself should not be stored as a large DB blob; store hash + artifact URI.

## `analysis_results`
Purpose: one canonical final result per analysis job. Stores final scores/decision, latency, view contributions and evidence URI.

## `detector_scores`
Purpose: normalized M1–M5 score rows. Composite PK `(analysis_job_id, detector_code)` prevents duplicates per detector/job.

## `alerts`
Purpose: SOC alert lifecycle and resolution state.

## `artifacts`
Purpose: metadata pointer to external evidence/model/export objects. Stores URI, SHA-256, MIME type, size and metadata. Large binary content belongs outside PostgreSQL.

## `audit_events`
Purpose: structured durable audit trail. Production policy should make application writes append-only; retention/delete is a separately authorized process.

## `experiment_runs`
Purpose: E0–E5 run metadata, config hash, seed and result URI. **No hidden ground-truth labels or blind manifests may be stored here.**

## Index strategy

Indexes cover request lookup, user/history filtering, status queues, content hashes, alert status, audit time/type/request and experiment code. Add new indexes only from measured query plans; do not preemptively index every JSON field.

## Retention

Retention periods are `[TBD]` until deployment requirements define compliance/storage needs. Deletion of analysis/audit data must be explicit and auditable.
