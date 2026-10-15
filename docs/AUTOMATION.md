# Scheduled refresh and notifications

Apply migrations before starting the new worker (`alembic upgrade head`). The automation migration is `d91e5f7c201a`. Settings below are deliberately disabled by default. Use environment variables or the deployment secret manager; never commit credentials to the repository.

## Source access and scheduling

`DATALYZE_SOURCES_JSON` is a JSON array of administrator-approved connections. Each source needs a unique `id` (letters, digits, underscore or hyphen), `name`, `type` (`api` or `database`) and an explicit list of numeric `company_ids`. API connections accept only fixed HTTPS URLs, optional request `headers`, `format` (`json` or `csv`) and an optional top-level `records_key`. Database connections use a fixed `url`, `table`, optional `schema`, and optional `columns`. Database credentials should have SELECT-only access. SQLite connections enable query-only mode; PostgreSQL connections use read-only transactions with a 30 second statement timeout. Sources are limited to 100,000 rows and 20 MB.

Add `"allow_refresh": true` only to sources approved for scheduled replacement. This flag alone does not start a schedule. A company administrator first imports and reviews the source, then enables the schedule in Monitor. Intervals range from 5 minutes to 24 hours. Each company has one automatic refresh schedule because it has one active dataset.

`PUT /api/v1/sources/{id}/schedule` accepts `enabled`, `interval_seconds` and `expected_revision`. Activation requires the exact current dataset revision. An edit, upload, restore or manual replacement pauses the schedule; the administrator must review the current source and explicitly resume. Successful refresh creates the same transactional backup as manual replacement. Identical consecutive snapshots do not replace the dataset or invalidate analysis. A failed connection leaves the prior data intact and retries with bounded exponential backoff. A refresh checkpoint commits atomically with its dataset. Expiring database leases prevent concurrent workers from claiming the same refresh.

## Running unattended

Set `DATALYZE_MONITOR_INTERVAL_SECONDS` to 60–86400 to run checks inside a continuously running backend. `0` (default) disables that worker. A production scheduler may instead invoke `python -m app.services.monitor_runner` at the desired frequency. A browser does not need to remain open. Serverless instances that sleep or terminate cannot guarantee an in-process schedule; use an external scheduled job there. Source refresh and outbound notifications use durable database leases. Readiness-check history may contain duplicate transition records if multiple independent readiness workers run simultaneously; use one readiness worker per deployment.

## Explicit notification destinations

`DATALYZE_NOTIFICATIONS_JSON` is a JSON array. No destinations are enabled by default. Each needs `id`, optional `name`, `enabled: true`, `company_ids` and `type`:

* `webhook`: fixed approved HTTPS `url`, optional `headers`. Receives JSON with a stable `id` and monitoring event data. The receiver must deduplicate by `id` or the `Idempotency-Key` header.
* `email`: `recipients` (1–20 explicitly approved email addresses). Uses the configured `RESEND_API_KEY` and `RESEND_FROM_EMAIL`. The sender domain and recipients must be permitted by the provider.

Notification data includes the affected check values and dataset revision, so destinations must be authorized to receive that company's data. URLs, headers, credentials and recipient addresses are not returned by the status endpoint.

Alerts and recoveries are queued when check status or thresholds change, not on every poll. A refresh failure queues one notification per incident. Outbox entries use a unique event/company/destination key and retry with the same provider idempotency key. States are `pending`, `retrying`, `accepted`, `failed` (after five attempts) or `blocked` (destination removed/disabled). `accepted` means the destination confirmed acceptance; it is not proof of email inbox delivery. Ambiguous network failures may be retried; webhook receivers must honor deduplication. Disabled or removed destinations never receive queued messages. Terminal failed/blocked events are retained for review and are not silently retried.

`GET /api/v1/sources/automation/status` shows the current tenant's schedule, configured destination labels and the latest 30 notification states. All authenticated company members can review status; schedule changes require a company administrator. External delivery and live source connectivity must be verified with the deployment's approved credentials and destinations.
