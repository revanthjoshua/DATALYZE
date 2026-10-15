# DATALYZE analyst workspace

The rebuild lives in the Desktop DATALYZE project. The workspace connects analysis decisions, source data, preparation, evidence, stakeholder review and monitoring. This guide describes implemented behavior and verified limits; it does not certify a production deployment.

## Product flow

Start at **Analyst Workspace**: **Brief → Prepare → Explore → Investigate → Share → Monitor**. Use **Data collection** to upload, paste, edit and manage saved datasets. Use **Metric directory** to inspect definitions, **Dashboard** for current metrics and history, **Reports** for exports, and **Metric alerts** for detected issues. Company and personal settings serve administration. The inventory simulator is retired; inventory tables can use the general analysis workflow.

| Analyst activity | Implemented behavior |
| --- | --- |
| 1. Understand the problem | Save the business question, decision, success measure and stakeholders. |
| 2. Collect | Upload files or pasted records; preview and import operator-approved database/API snapshots; retain additional datasets in a company library. |
| 3. Clean | Preview a sequence of deduplication, whitespace, missing-value and type operations before applying it. |
| 4. Transform | Chain filters, sorting, renaming, text changes, date parts and safe arithmetic formulas; preview validated composite-key joins. |
| 5. Explore | Inspect missingness, duplicates, distributions, summaries, distinct values and correlations. |
| 6. Define KPIs | Inspect numeric metrics and save reusable formula rules with sum/mean, target and direction. |
| 7. Analyze | Run explicit grouped sum, mean, median, minimum, maximum and count. |
| 8. Find trends | Inspect daily totals, moving averages and historical charts; compare forecast models using observed validation errors. |
| 9. Detect problems | Inspect observed-data anomaly signals and target/readiness alerts. |
| 10. Investigate causes | Reconcile signed segment contributions, inspect date coverage and drill into changes; separate row-volume, mean-value and entry/exit components. This is observational evidence, not proof of cause. |
| 11. Use statistics | Pearson correlation, two-sided permutation tests and bootstrap intervals with stated assumptions. |
| 12. Visualize | Distribution, historical, forecast and KPI charts. |
| 13. Build dashboards | Company-scoped current metrics and date-filtered history. |
| 14. Preserve insights | Save results with method, parameters, source revision and limitations; identify historical evidence after source changes. |
| 15. Recommend actions | Record evidence-linked findings, proposed actions, owners, validation measures and progress. Business actions remain human decisions. |
| 16. Report | Download escaped HTML evidence/report packages and CSV metric exports; print HTML to PDF in the browser. |
| 17. Communicate | Share authenticated company report links, discussion, review decisions and review history. |
| 18. Monitor | Evaluate formula targets and freshness/missingness rules; optionally refresh a source and deliver configured email/webhook notifications without an open browser. |

## Data lifecycle and preparation

A company has **one active dataset and a library of saved snapshots**. Uploading to the library leaves the active dataset unchanged. Save the active dataset, upload another snapshot, preview/download it, activate it, archive/restore it, or join it to the active source. Snapshots are immutable and checksum-checked. Archive changes visibility; it does not free storage. The library allows 100 snapshots and 200 MB per company, including archived snapshots. Each snapshot supports up to 100,000 rows, 500 columns and 20 MB.

Saving active-source snapshots, activating new or legacy snapshots, and joining them preserve public source columns without adding generated internal helper columns to the resulting source. Legacy immutable previews retain their originally stored columns. Legitimate underscore-prefixed columns supplied in raw uploads are preserved. Regression tests cover this distinction.

Successful active-source replacements, including editor saves, preparation, joins, activation and connected imports, back up the previous source before replacing generated analytics. Saved briefs, evidence, findings and reports remain available; evidence is marked historical when its revision differs from the active source. Explicit active-dataset deletion removes that source, its backups and ordinary associated evidence/analytics. It retains saved library datasets, stakeholder report packages and reviews, briefs, monitoring settings and formula rules.

The editor loads the complete editable dataset up to 10,000 rows. Larger datasets are rejected for editing instead of saving a truncated preview. Edits and preparation require the original source revision; concurrent or stale writes return a conflict. PostgreSQL replacements lock the company row. A preparation preview binds the operations and revision that will be applied, and supports up to 20 steps.

Joins support left, inner and outer joins; one to five matching key columns; and explicit one-to-one, many-to-one, one-to-many or many-to-many relationships. Missing keys, unexpected duplicates for the selected relationship and conflicting output names are rejected. Both inputs and the projected result are limited to 100,000 rows. The preview reports matched/unmatched rows and expansion before application. Many-to-many expansion must be deliberately selected.

Text identifiers with leading zeros, literal `NA`/`null` strings and missing numeric values are preserved by the ingestion path. Malformed delimited/JSONL input is rejected instead of silently skipped. PDF support extracts text only, without OCR. Excel currently selects one sheet; use separate uploads for additional sheets. Connected snapshots are bounded at 20 MB; source-version backups at 50 MB.

## Analysis and sharing limits

Forecasting requires at least 12 consecutive dated daily observations and a horizon of 1–30 days. Last observed value, recent mean and linear trend compete in rolling-origin validation across the requested horizons. Weekly seasonality joins the comparison at 28 consecutive days. Model selection weights each supported horizon equally. The result includes per-horizon sample counts and errors. Ranges use observed horizon residuals where sufficient, otherwise scaled one-step errors; they are empirical ranges, **not guaranteed 95% coverage**. Calendar gaps require explicit preparation; future external events and structural changes are not modeled.

Contribution investigation compares totals per observed day, reports missing calendar days and reconciles segment changes. Row-volume and mean-per-row components only describe the source's row grain; rows are not automatically transactions. New/disappearing segments are identified separately. Drilldown supports up to five exact filters through the API; the workspace currently exposes one. Statistical tests assume independent observations and do not apply multiple-testing correction. Correlation, anomaly signals and contribution scores do not establish causation.

Stakeholder report packages capture 1–20 selected evidence records, up to 2 MB, with an immutable summary/evidence snapshot and an append-only review history. Links require company membership. Invite external stakeholders as Viewers for reading/downloading; permitted analysis roles create reports and record reviews. There are no anonymous public links. Exported files lose login protection after download.

The dataset assistant is a **rule-based lookup**. It does not use a language model, browse the web, execute business actions or invent confidence scores. The legacy metric health badge compares recent observations using a fixed adverse-change threshold; use a saved formula target in Monitor for an explicit business objective.

## Deployment and operator configuration

The selected deployment target is **Render for the API and static frontend, Render managed PostgreSQL 18 for application storage, and Resend for email**. This decision is recorded in `DEPLOYMENT.md`; the root `render.yaml` prepares those resources. The target has been chosen, but the cloud resources have not been provisioned. Uploaded data remains the business-data source until an actual company database or API is connected.

Back up the target database before deployment and apply the repository's Alembic migrations through **`d91e5f7c201a`**. This includes analysis records, refresh jobs and the notification outbox. Use **`GET /health/ready`** to check database connectivity and required tables: it returns 503 when unavailable or migrations are missing. It is a readiness check, not a complete schema audit. The frontend container proxies `/api/` to the backend; the development Compose ports bind to loopback.

Set `DATABASE_URL`, `ENVIRONMENT`, `FRONTEND_URL`, trusted `CORS_ORIGINS` and other required application settings for the actual environment. Keep secrets in server configuration. Email requires `RESEND_API_KEY` and an authorized `RESEND_FROM_EMAIL`. Failed invitation/reset sends preserve previously valid state. Provider acceptance alone does not prove inbox delivery.

### Database/API connections

Set `DATALYZE_SOURCES_JSON` to an array of operator-approved connections with an `id`, `name`, `type` and explicit numeric `company_ids`. The browser receives connection names and capabilities, not credentials. Users cannot supply arbitrary SQL or connection URLs.

API connections use an HTTPS `url`, optional `headers`, `format` (`json` or `csv`) and optional top-level JSON `records_key`. JSON must resolve to an array of objects. Redirects are rejected. Database connections use a SQLAlchemy `url`, `table`, optional `schema` and optional `columns`. Give each source a dedicated read-only account and a tenant-specific table/view. PostgreSQL also uses a read-only transaction and a query timeout. Required drivers and endpoint permissions must exist in the deployment environment.

Illustrative configuration; replace placeholders in secure server configuration:

```json
[
  {
    "id": "sales-api",
    "name": "Approved sales feed",
    "type": "api",
    "company_ids": [123],
    "url": "https://approved-source.example/records",
    "headers": {"Authorization": "Bearer <server-secret>"},
    "format": "json",
    "allow_refresh": true
  }
]
```

Preview stores an exact snapshot; applying it verifies the active revision and imports that snapshot. Connections are bounded full-snapshot imports, without automatic pagination or incremental synchronization. Configure only the company mapping and endpoint that the operator intends to expose.

### Unattended refresh and notifications

Monitor works on demand by default. To run unattended cycles in a long-lived backend, set `DATALYZE_MONITOR_INTERVAL_SECONDS` to 60–86,400; `0` disables the in-process worker. Alternatively, schedule `python -m app.services.monitor_runner` with the same deployment database/configuration; it performs one cycle. A serverless deployment needs that external scheduler. Choose one scheduling mechanism for ordinary operation.

Each cycle refreshes due sources, evaluates saved monitoring rules and delivers queued notifications. A company administrator must explicitly enable a refresh schedule after importing/reviewing the source, and the source must have `allow_refresh: true`. A company has one active-source schedule, with an interval of 300–86,400 seconds. Changes outside the schedule pause automatic replacement until the administrator reviews and resumes it. Unchanged source content avoids repeated replacement after the source hash is established. Failures back off and expose a status; leases and revision checks protect concurrent workers.

Notifications are opt-in. Set `DATALYZE_NOTIFICATIONS_JSON` to approved email/webhook destinations with `enabled: true` and explicit `company_ids`. Email entries require `recipients` plus the Resend settings. Webhook entries require an approved HTTPS `url` and optional secret `headers`. For example:

```json
[
  {
    "id": "operations-email",
    "name": "Operations alerts",
    "type": "email",
    "company_ids": [123],
    "enabled": true,
    "recipients": ["approved-recipient@example.com"]
  }
]
```

Monitoring state changes, recoveries and source-refresh failure incidents enter a durable outbox. Delivery retries up to five attempts with a stable idempotency key; receiver/provider behavior determines duplicate suppression. The UI distinguishes pending, retrying, accepted, failed and blocked. Accepted means provider acceptance, not confirmed inbox delivery. Removing/disabling a destination blocks its queued delivery. No destination means no external notification is sent.

## Verification and remaining deployment work

Automated acceptance tests use `backend/tests`, an isolated database and mocked email delivery. They cover tenant boundaries and roles, revision conflicts, rollback, complete editor round-trips, parsing, preparation/joins, saved libraries, statistics/forecasts, source import/refresh, notifications, report escaping/reviews and CSV/XLSX/JSON workflows. Run them with an explicit test environment outside a directory that would load production `.env` settings. Older standalone audit scripts outside this suite predate the rebuild.

Recorded external/local integration checks include:

- A fresh disposable **PostgreSQL 18** database migrated to `d91e5f7c201a` and passed production-mode startup locally.
- Across **3 isolated tenants**, **96 profile reads with 8 workers** returned no errors or mixed tenant data. The latest local run, while other tests were running, measured median latency of 1.349 seconds and p95 of 2.043 seconds. An earlier run measured 0.279 and 0.416 seconds respectively. These small-fixture smoke tests verify the exercised concurrency behavior; the varying timings do not establish production capacity.
- **6 simultaneous replacements** using one revision yielded one successful write and five stale-revision conflicts.
- A real read-only PostgreSQL source imported **2 rows**, with the expected sum of **30** verified.
- A live HTTPS public API imported **100 JSON records**.
- One explicitly authorized invitation was sent from the isolated preview; its token was verified, and the recipient confirmed **Received**.

The final backend suite passed **156 tests in 62.97 seconds on 15 October 2026**, including the library helper-column regression checks. TypeScript/build validation and local browser checks supplement the backend suite. See the release verification record for their evidence and scope.

**No production database was reset and no production deployment was performed.** Render and managed PostgreSQL are the selected, prepared destination; they have not been provisioned. Production rollout still requires the authorized hosting account and resource setup, secure production values, migration and readiness checks, an actual business database/API source, intended notification destinations, a supervised refresh/notification cycle, and performance validation against representative production data and traffic. Local checks and a delivered test invitation do not establish those environment-specific outcomes. See `DEPLOYMENT.md` for the recorded choice and rollout procedure, and `RELEASE_VERIFICATION.md` for the release evidence and remaining checks.
