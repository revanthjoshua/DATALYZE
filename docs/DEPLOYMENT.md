# DATALYZE deployment decision and runbook

Decision recorded on 13 October 2026: use **Render** for the Python API and React static site, **Render managed PostgreSQL 18** for application storage, and the existing **Resend** email integration. The user delegated this choice. This file records the choice so later work keeps the same target.

This is a prepared deployment, not a live deployment. No cloud resource was created, no payment was made, and no existing production database was changed. The root `render.yaml` is the deployment manifest.

## Chosen configuration

| Resource | Configuration | Reason |
| --- | --- | --- |
| API | Render Python, Singapore, `1c-2g`, one instance and one Uvicorn worker | A modest starting size for in-memory data analysis, with an always-running monitoring loop |
| Application database | Render PostgreSQL 18, Singapore, `0.5c-1g`, 5 GB | Relational tenant storage, transactions, durable jobs and notification outbox |
| Frontend | Render Static Site, React build from `frontend/dist` | Separate static delivery and page-route rewrites |
| Email | Existing Resend integration | Invitation receipt has already been confirmed in local verification |
| Runtime | Python 3.12.14 and Node 24.16.0 | Matches the local validation runtimes |

The initial size is a starting point, not a measured production capacity guarantee. Monitor memory, analysis duration, storage and response times before increasing limits or concurrency. The selected API and database are paid services. Review the current total, including storage, traffic and email, in the provider's creation screen before provisioning. [Render pricing](https://render.com/pricing)

The manifest binds the API to Render's assigned port, migrates before starting, checks `/health/ready`, and uses the private database connection. An empty database IP allowlist prevents external database connections. The frontend publishes `./dist` relative to its `frontend` root and rewrites page URLs to `index.html`. Automatic deploys are disabled initially. [Blueprint reference](https://render.com/docs/blueprint-spec), [monorepo paths](https://render.com/docs/monorepo-support), [Python version selection](https://render.com/docs/python-version)

## Access and release status — 17 October 2026

The Render integration is connected, and the user explicitly confirmed Revanth's workspace for inspection and preparation. The last read-only inventory returned no existing services or PostgreSQL instances. Source publication and CI were separately authorized, and [draft pull request #3](https://github.com/revanthjoshua/DATALYZE/pull/3) now contains the rebuild. The old main-branch commit is not the rebuild.

Original release head `718b6561018646cbf1a33ce61923da3b2b405a1b` passed [all three Linux CI jobs](https://github.com/revanthjoshua/DATALYZE/actions/runs/38759806470): 156 backend tests, standard frontend build, and fresh/repeated PostgreSQL 18 migration with production readiness. Application release `c959a021e65b0f076692ba14c165a32ef8e2ddbc` passed [all three CI jobs](https://github.com/revanthjoshua/DATALYZE/actions/runs/39003978728) on **17 October 2026**: **167 backend tests**, **8 frontend login/session tests**, the standard production build and production-dependency audit, and fresh/repeated PostgreSQL 18 migration with production readiness. Documentation-only updates after this commit do not change the verified application. See `RELEASE_VERIFICATION.md` and `DEPENDENCY_SECURITY.md`.

### Planning cost observed on 17 October

The figures below are the public price-page estimate, not a fresh account-specific quote or approval to spend.

The [Render pricing page](https://render.com/pricing), checked on 17 October, listed **$25/month** for API compute `1c-2g` and **$19/month** for PostgreSQL compute `0.5c-1g`: **$44/month in compute**. Database storage is listed at $0.30/GB; allow up to $1.50/month for the requested 5 GB, subject to the provider's included-storage calculation. The static site has no compute charge. A Hobby workspace has no subscription charge; this plan does not authorize an upgrade to a paid workspace subscription. Bandwidth/build overages, tax, foreign-exchange/card charges, domain purchases and email-provider charges are additional if incurred. Confirm the final account-specific quote before creating anything. These figures are a planning estimate, not an agreed purchase or hard billing cap.

No resource has been provisioned, no application has been published to Render, and no recurring charge has been authorized. See `DEPLOYMENT_APPROVAL.md` for the concrete proposed release and approval boundary.

## Production values

Enter values in the hosting dashboard's environment settings. Do not commit `.env`, source connection passwords, API tokens, database exports, or test databases.

| Service | Variable | Value |
| --- | --- | --- |
| API | `DATABASE_URL` | Supplied automatically by the managed database reference |
| API | `SECRET_KEY` | Generated by the manifest; keep it stable across redeploys |
| API | `FRONTEND_URL` | Exact public frontend origin, such as `https://your-assigned-site.onrender.com`, without a trailing slash; used in invitation/reset links |
| API | `CORS_ORIGINS` | JSON array containing that exact origin, e.g. `["https://your-assigned-site.onrender.com"]`; include a custom domain explicitly if used |
| API | `RESEND_API_KEY` | Existing valid Resend credential, entered securely |
| API | `RESEND_FROM_EMAIL` | Sender authorized by the configured Resend account/domain |
| API | `DATALYZE_SOURCES_JSON` | `[]` until an actual business source is connected; see below |
| API | `DATALYZE_NOTIFICATIONS_JSON` | `[]` until intended notification destinations are configured |
| Frontend | `VITE_API_BASE_URL` | Exact public API URL **including `/api/v1`**, e.g. `https://your-assigned-api.onrender.com/api/v1`; this value is public build configuration |

`CORS_ORIGINS` is authoritative. Old hosting domains, localhost, and `FRONTEND_URL` are not added implicitly. The default local configuration still permits localhost and 127.0.0.1. Changing `VITE_API_BASE_URL` requires rebuilding the frontend. Environment values marked `sync: false` are requested during initial Blueprint setup; later updates must be made in the service settings. [Environment behavior](https://render.com/docs/blueprint-spec)

## First deployment

1. Review draft pull request #3 and select the exact release commit after its required checks pass. Source publication has already excluded local datasets and secrets. Connect the reviewed release to the authorized Render account and select its root `render.yaml` as a Blueprint; do not deploy the old main-branch code or assume an earlier CI pass covers later commits.
2. Review the resource names, region and recurring quote before creating the resources. This is the purchase/provisioning boundary; preparing this manifest does not cross it.
3. Enter the production values above. Use final owned domains if already configured. If Render has not yet assigned service URLs, a first provisioning pass can use `https://deployment-pending.invalid` for `FRONTEND_URL`, `["https://deployment-pending.invalid"]` for `CORS_ORIGINS`, and `https://deployment-pending.invalid/api/v1` for `VITE_API_BASE_URL`. Those are deliberately nonfunctional placeholders. Keep the site out of use until the next step is complete.
4. Read the actual assigned URLs from the dashboard, replace any placeholder values, and deploy both services again. Never assume a requested service name guarantees a particular public hostname.
5. Confirm the migration succeeds and the API's `/health/ready` returns 200 with `status: ready`. Verify the frontend uses the intended API host and direct visits to `/analysis` and authenticated report links survive refresh and login.
6. Register a company administrator on the fresh deployment, import a non-sensitive fixture, run preparation, statistics, forecasting and report sharing, then verify a Viewer cannot modify data. Use a second company to confirm tenant separation.
7. Configure actual sources and destinations, perform one authorized notification test, then verify a due monitoring cycle and an automatic refresh while the browser is closed. Check recorded status and provider response; acceptance alone is not proof of inbox delivery.

The readiness probe checks database access and required tables. It does not establish correct email credentials, source permissions, recipient delivery, or complete migration compatibility by itself. Render gates routing on its configured health check. [Health checks](https://render.com/docs/health-checks)

### Client addresses and trusted proxies

The application's rate limiter uses `request.client`, as supplied by the ASGI server. It does not parse raw `X-Forwarded-For` headers itself. Configure the server's trusted proxy IPs for the actual hosting network, using the provider's current guidance, so client addresses can be forwarded only by the intended proxy. Verify in the deployed environment that separate clients are distinguished and that a client-supplied forwarding header cannot change its rate-limit identity. Do not set the trusted proxy allowlist to `*` unless direct access is restricted to trusted proxies. Incorrect trust can let clients evade limits; missing trust can group all clients behind the proxy into one limit.

## Business sources and monitoring

The managed application database stores DATALYZE users, datasets, reports and jobs. It is not a substitute for a company's real business data. Until an actual business system is identified, use uploaded data. The public API used during validation is a connector fixture, not production business data.

Configure `DATALYZE_SOURCES_JSON` as a JSON array of operator-approved connections. Every entry needs a stable `id`, a display `name`, its `type` (`database` or `api`) and the permitted numeric `company_ids`.

- Database entries also need a credentialed `url`, fixed `table`, optional `schema`, and optional `columns`. Prefer PostgreSQL with a dedicated account that can only read the approved tables. Do not reuse the application's database administrator credential as a business-source credential.
- API entries need a fixed HTTPS `url`; optional `headers` hold authentication, `format` can be `json` or `csv`, and `records_key` can identify a top-level JSON array. The current connector does not follow redirects or automatically paginate an API.
- Set `allow_refresh: true` only after reviewing the source. Import it, review the preview, and explicitly enable the schedule from Monitor. Sources are bounded to 20 MB and 100,000 rows; larger or paginated systems need an upstream export or connector extension.

Notifications use `DATALYZE_NOTIFICATIONS_JSON`. Each configured destination requires `id`, `name`, `type` (`email` or `webhook`), `company_ids` and `enabled: true`, plus `recipients` for email or `url` for a webhook. Check the current `automation_service.py` contract when adding optional authentication. Destinations start empty, preventing unintended messages.

The manifest runs the monitoring cycle every 60 seconds. Individual source refresh intervals and monitor rules remain company settings; this does not poll every upstream source every minute. Jobs use persisted leases, revision checks and retries. Manual data changes pause a scheduled source until an administrator reviews and resumes it. Keep one API worker/instance for the initial deployment; test recovery and notification behavior before scaling or separating the scheduler. A stopped service cannot process due jobs until it starts again.

## Migration and recovery

For a fresh environment, the pre-deploy command is `alembic upgrade head`. Existing production data requires a backup and a migration rehearsal against a restored copy before applying that command to the live database. Do not run schema reset, `drop_all`, development seed scripts, or destructive restore commands against production.

Render's paid databases support point-in-time recovery and on-demand exports. Confirm the available recovery window and test restoring into a **separate** database, validating tenant counts and sample datasets before any connection switch. Keep the original intact until the replacement has been checked. [Recovery and backups](https://render.com/docs/postgresql-backups)

Application rollback and database rollback are separate decisions. Redeploy the previous known-good application only when it is compatible with the current schema. Do not blindly downgrade migrations or replace a live database; recover into a separate instance and review the data first.

## Validation boundary

Local evidence includes a real PostgreSQL 18 migration and concurrent tenant checks, a public HTTPS API import, production-mode startup, and user-confirmed invitation receipt. The original published head additionally passed Linux CI, including the standard frontend build and PostgreSQL 18 migration/readiness checks. The follow-up candidate requires its own successful run. On 15 October, `render.yaml` passed repeat validation against Render's official Blueprint JSON schema. Schema validation confirms manifest structure; CI confirms the exercised release checks. Neither verifies account entitlement, resource creation, assigned production domains, customer source credentials, cloud backups or deployment performance. See `RELEASE_VERIFICATION.md` for recorded results and `POST_DEPLOY_VERIFICATION.md` for all 18 pending cloud checks. Those require the authorized deployment and its actual services.
