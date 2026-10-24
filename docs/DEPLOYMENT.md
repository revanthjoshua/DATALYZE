# DATALYZE free deployment runbook

Decision and release status reviewed **24 October 2026**: the user rejected paid Render services and set a **₹0 hosting budget**. Use the existing **Vercel frontend and backend projects with Neon Free PostgreSQL**, wherever the rebuilt application fits. Preserve the Desktop project, published rebuild, existing domains and production data. The former Render proposal is superseded; `render.yaml` remains a dormant historical alternative and must not be provisioned.

This document prepares a release. The existing Vercel team is confirmed on **Hobby**. Its frontend project is `datalyze-y9n8`, its backend project is `datalyze`, and both use the existing DATALYZE GitHub repository. Neon project `purple-cell-52986724` is confirmed on **Free** (`free_v3`) with PostgreSQL 18. An isolated synthetic Vercel/Neon preview is deployed and has recorded API acceptance results. Production promotion and production migration remain pending. Do not activate trials, paid add-ons or upgrades, and do not downgrade or replace an existing account automatically.

Before verification-branch creation on 19 October, the Neon dashboard showed one existing branch, approximately 0.03 CU-hours and 0.04 GB storage used, with negligible transfer. The account API confirmed a 1 GiB branch logical-size cap, ten allowed branches and a 21,600-second history window. These are observations at that time, not a reservation of future quota.

A separate verification branch has now been created: `codex-release-verification-20261019` (`br-holy-star-azv1fzxn`), from production parent `br-late-base-az4po99q`. Its endpoint uses fixed 0.25 CU and the provider's default suspension setting. The Free plan rejected an explicit suspension override, so the default was retained. Creating this branch did not write to production. The copied production data remains confidential. Its migration rehearsal passed. A separately restored database also passed 17-relation source comparison, repeated migrations and readiness; one inherited company-ID sequence needed repair only in that restore copy. The equivalent production sequence correction remains required. Hosted API tests use a separate synthetic database and distinct credentials, not the confidential production copy.

## Feasibility and limits

The free target can support a small, intermittent analyst workspace with bounded datasets. It cannot provide the former always-running monitoring process or an unrestricted production capacity guarantee. Verify these current provider limits against the actual accounts before deployment:

| Boundary | Limit and practical effect |
| --- | --- |
| Vercel eligibility and allowance | Hobby is for personal, non-commercial use. Its monthly allowance includes 4 active CPU hours, 360 GB-hours of provisioned memory and 100 GB fast data transfer. A commercial company deployment needs a different eligible arrangement; do not silently upgrade. Exhausting free quotas can interrupt availability. [Hobby plan](https://vercel.com/docs/plans/hobby) |
| Function size and execution | Python functions have a 500 MB uncompressed bundle limit. Hobby Fluid Compute provides up to 300 seconds and 2 GB memory per function. The scientific dependency bundle and representative analyses must pass a real Vercel build/runtime test. [Function limits](https://vercel.com/docs/functions/limitations) |
| Uploads and downloads | Vercel limits function request and response bodies to 4.5 MB. DATALYZE caps files and responses at 4,000,000 bytes and complete requests at 4,250,000 bytes on Vercel. Multipart overhead counts toward the request cap. File size does not predict expanded analysis memory. [Function limits](https://vercel.com/docs/functions/limitations) |
| Scheduled monitoring | Hobby cron runs at most daily, with scheduling precision of up to 59 minutes within the scheduled hour. Each invocation consumes function allowance. It cannot promise minute-level alerts or an always-running worker. [Cron limits](https://vercel.com/docs/cron-jobs/usage-and-pricing) |
| Neon capacity | The current Free plan lists 1 GB database storage, 100 CU-hours per project per month, 5 GB public network transfer and 10 branches. Existing and test workloads share project quotas; inspect remaining capacity before a branch or load test. [Neon pricing](https://neon.com/pricing) |
| Neon recovery | Free recovery is limited to up to six hours or 1 GB of changes, with one snapshot. Compute suspends after inactivity. Keep a separate verified export before migration; this limited recovery window is not the only backup. [Neon pricing](https://neon.com/pricing) |

Public plan facts were rechecked on **19 October 2026**. Account-specific observations are recorded above; inspect usage again before branch creation, load tests and promotion. Use the existing free service domains and email arrangement only within their confirmed allowance. A quota or compatibility failure is a reason to reduce the cloud workload or continue that operation locally, not authorization to incur charges.

## Release and validation status

The rebuild is preserved in [draft pull request #3](https://github.com/revanthjoshua/DATALYZE/pull/3), branch `codex/analyst-workspace-rebuild`. Do not deploy old `main` or assume a historical CI result covers a changed commit.

Application commit `c959a021e65b0f076692ba14c165a32ef8e2ddbc` passed [all three CI jobs](https://github.com/revanthjoshua/DATALYZE/actions/runs/39003978728): 167 backend tests, eight frontend login/session tests, the standard production build and production dependency audit, and fresh/repeated PostgreSQL 18 migrations with readiness. Documentation-only commit `66cfbfaf7a5a7083eea3f7e0e3f257c4895be6f1` also passed [its CI run](https://github.com/revanthjoshua/DATALYZE/actions/runs/39023915280). Those results belong to the recorded historical releases. Current source `bbcff1c46ef2113dfb108b35908c6185a38ae47c` has an isolated hosted preview; the recorded adaptation checks include 199 backend tests, 12 existing frontend tests and the standard production build. The original and resumed hosted HTTP runs together cover API behavior underlying all 18 capability areas. They do not establish hosted browser or production acceptance. See the dated evidence below before certifying any subsequent commit.

The same-origin proxy is integrated in the release candidate. All **27 frontend tests and the standard build passed on 24 October** (12 existing cases and 15 proxy cases), with zero vulnerabilities reported by the production dependency audit. OIDC 4.0.3 uses a scoped Zod 4.6.6 override for its CLI helper; follow-redirects is locked at 1.16.1. An installed-helper and function-entry import check passed using a synthetic token without network access. Complete cloud routing and browser checks before promotion.

Keep the evidence in [RELEASE_VERIFICATION.md](RELEASE_VERIFICATION.md). Seven development-tool dependency findings remain recorded in [DEPENDENCY_SECURITY.md](DEPENDENCY_SECURITY.md). The [post-deployment plan](POST_DEPLOY_VERIFICATION.md) supplies the 18 capability checks; none becomes a live pass merely because a local or CI test passed.

## Inspect the existing deployment first

1. Preserve the identified Vercel projects and inspect their domains, production commit, root directories, build settings and deployment protections. Hobby status is confirmed; remaining usage and personal/non-commercial eligibility still need to fit the release. Do not change billing settings.
2. Preserve the identified Neon Free project and inspect its production branch, database, role and current schema. Recheck available capacity before rehearsal. Record identifiers and counts, never credentials or customer rows, in the release notes.
3. Inspect environment variable names and scopes securely. Preserve production secrets, domains and stable signing keys. Preview environments must not inherit the production database or outbound notification credentials accidentally.
4. Confirm how the existing production schema was created and its Alembic revision. Compare it with the rebuilt schema. If schema history is absent or incompatible, prepare and rehearse a data-preserving migration; do not blindly stamp a revision, reset tables or recreate the database.

## Environment settings

Set secret values in the provider's environment controls. Do not publish `.env`, database URLs, API keys, backup exports or local fixture accounts. Preview and production need separate scopes.

Branch-specific preview settings for `codex/analyst-workspace-rebuild` point at the isolated synthetic database, with a separate signing secret, empty source/notification lists and disabled outbound email. That preview uses `vercel_daily` with a separate cron secret to exercise the authenticated cron handler manually. This does not prove that Vercel has triggered a scheduled invocation. These values must not be promoted as production settings. Direct hosted API checks passed. The frontend same-origin proxy and its environment-specific OIDC Trusted Sources connection still require hosted verification and explicit authorization for the access rule; do not disable deployment protection.

| Component | Setting | Required behavior |
| --- | --- | --- |
| Backend project | Root directory | `backend`; inspect the existing project before changing its settings. |
| Backend project | Runtime and build | Python 3.12; `backend/vercel.json` selects FastAPI with Fluid Compute and a 300-second maximum duration. Production installs use `requirements.txt`; `requirements-dev.txt` adds test dependencies. |
| Backend | `ENVIRONMENT` | `production`, including protected previews. |
| Backend | `DATABASE_URL` | SSL-enabled Neon pooled URL for the intended branch; use a distinct preview database. The serverless adaptation uses `NullPool` to avoid retaining client-side connection pools. |
| Backend | `STORAGE_BACKEND` | `db`; serverless local files are not durable application storage. |
| Backend | `SECRET_KEY` | Stable production secret; a separate preview secret. Do not rotate production sessions accidentally. |
| Backend | `FRONTEND_URL` | Exact intended frontend origin, used in invitation/reset links. |
| Backend | `CORS_ORIGINS` | JSON array of exact approved frontend origins. Avoid wildcard preview domains; add the selected preview URL explicitly. |
| Backend | `MAX_UPLOAD_SIZE_BYTES` | At most `4000000` on Vercel; lower configured values are retained. |
| Backend | `MAX_REQUEST_SIZE_BYTES`, `MAX_RESPONSE_SIZE_BYTES` | At most `4250000` and `4000000` respectively on Vercel; these caps are applied when `VERCEL=1`. Larger local limits do not override them. |
| Backend | `DATALYZE_MONITOR_INTERVAL_SECONDS` | `0`; do not start a permanent loop inside Vercel functions. |
| Backend | `DATALYZE_SCHEDULER_MODE` | Default to `manual` during initial setup and migration. The isolated synthetic preview uses `vercel_daily` for its authenticated handler test; actual platform scheduling is still unverified. Enable production daily processing only when intended and verified. |
| Backend | `CRON_SECRET` | A separate random secret of at least 32 characters when daily scheduling is enabled. Keep it separate from `SECRET_KEY`; never place it in URLs or frontend settings. |
| Backend | `DATALYZE_SOURCES_JSON` | `[]` during preview and migration verification. Configure only identified, approved business sources later. |
| Backend | `DATALYZE_NOTIFICATIONS_JSON` | `[]` during preview and migration verification. |
| Backend | `RESEND_API_KEY`, `RESEND_FROM_EMAIL` | Preserve existing production settings securely. Leave delivery disabled in preview; do not send test email without recipient authorization. |
| Frontend project | Root, build, output | `frontend`, `npm ci` / `npm run build`, `dist`; preserve SPA deep-link rewrites. |
| Frontend | `VITE_API_BASE_URL` | `/api/v1` for the prepared same-origin proxy; this public value is embedded at build time. Rebuild after changes. Do not put a platform credential in a `VITE_` setting. |
| Frontend server function | `DATALYZE_API_ORIGIN` | The fixed, allowlisted backend origin for this environment, server-only. Preview must never target production. Keep unset for the initial fail-closed routing probe; configure after routing is observed. |
| Frontend server function | OIDC / Trusted Sources | Resolve a short-lived workload token on each request. Authorize only the intended frontend project and same-environment backend destination after explicit approval; preserve existing rules. No permanent browser bypass secret. |

### Protected frontend API connection

The prepared proxy routes `/api/v1/*` through one frontend Node function in `sin1`, with Fluid Compute and a 300-second duration. It forwards application JWTs and bounded body bytes, keeps the OIDC workload credential server-side, and rejects internal API paths, arbitrary upstream origins and cross-environment origins. It adds an invocation to each API request and consumes the existing free allowance; it does not remove platform payload/runtime limits.

Before adding a Trusted Sources rule, deploy the proxy with `DATALYZE_API_ORIGIN` unset and verify through existing authorized frontend access: `/api/v1/auth/me` returns the proxy's JSON 503 configuration message, `/api/v1/internal/cron` returns its JSON 404, and `/login/admin` still serves the app. This demonstrates the original API path reaches the handler. An HTML fallback or API 404 on the first probe is a routing failure, not successful authentication. Then prepare and authorize the exact preview-to-preview trust rule, configure the server-only origin, and test the actual browser flow. Production-to-production trust is a separate explicit release setting. The 15 local proxy tests do not prove Vercel routing or Trusted Sources acceptance.

Do not configure migrations in a Vercel build command, import handler or application startup. A preview build must never migrate the production database. Use the direct Neon connection securely for the explicit migration operation; keep the runtime on its intended pooled connection.

## Preview, migrate and release without replacing production data

1. Select the exact candidate commit and require its tests, dependency review and build to pass. Deploy a preview from the existing rebuild branch; source publication approval does not mean `main` was merged.
2. Use the existing verification branch above and recheck free quota before additional work. Treat its production-derived copy as confidential, protect the preview and restrict access. Use synthetic datasets and separate acceptance users for feature tests. Keep sources, cron and notifications disabled. Do not create redundant test branches.
3. Check the actual Vercel Python bundle size and function startup. Check `/health/ready`, frontend/backend origin pairing, authenticated report links, request/response size errors and cold-start behavior. If the dependency bundle or workload exceeds free limits, record the failing operation and preserve the working local application.
4. Before any live migration, make a secure backup/export of the existing production database and verify it restores into a separate test environment within available free capacity. Rehearse `alembic upgrade head` there, rerun it to confirm repeatability, and compare schema, tenant/user/report/dataset counts and representative checksums. Never use `drop_all`, seed/reset scripts or a destructive restore against production.
5. Complete the 18 capability checks and tenant/role tests on the preview. Exercise small and near-limit fixtures, joins, statistics, forecasts, saved evidence, reports, permission denial and dataset revisions. Bound concurrency tests to available quotas; record actual latency and failures instead of extrapolating an unlimited capacity claim.
6. Record the current production application deployment and recovery path. Once the candidate and migration rehearsal pass, apply the reviewed migration as one explicit operation using the existing production database, then promote the tested frontend/backend releases. Coordinate writes during migration as required by the actual schema changes. Preserve domains, accounts and datasets.
7. Verify readiness and core user flows on the promoted deployment, then finish the live checks in `POST_DEPLOY_VERIFICATION.md`. Record the exact release, domains, runtime configuration and evidence. Do not remove the prior working deployment or backup before recovery is demonstrated.

Readiness verifies database connectivity and required tables; it does not prove email delivery, business-source access, every role or acceptable performance. Application rollback is separate from database rollback. Redeploy a prior app only if it is compatible with the current schema; recover data into a separate database for review instead of blindly downgrading or overwriting production.

## Sources, notifications and free monitoring

Neon holds DATALYZE's own users, tenant datasets, reports and job state. It does not supply a company's business records. Until a real source is identified, use uploads. Existing public API and database fixtures establish connector behavior only.

Source allowlists and company IDs remain mandatory. Keep read-only database credentials separate from application database credentials. API imports are bounded snapshots without automatic pagination; see [AUTOMATION.md](AUTOMATION.md) for the connector contract. Provider body and runtime limits can be stricter than the general local limits.

The candidate config schedules `GET /api/v1/internal/cron` once daily at **03:17 UTC** (nominally **08:47 Asia/Calcutta**). Hobby timing is approximate within the scheduled hour. Keep production in `DATALYZE_SCHEDULER_MODE=manual` until verification is complete; a configured schedule alone must not be reported as observed execution. To enable daily work, set `DATALYZE_SCHEDULER_MODE=vercel_daily` and a separate random `CRON_SECRET` of at least 32 characters. Vercel sends this secret in the `Authorization: Bearer …` header; unauthenticated and incorrectly authenticated calls must be rejected. The synthetic preview has exercised this enabled handler manually with no external sources or messages; observation of a platform-triggered run remains pending.

The daily cycle has a **240-second work budget**, capped at **two source refreshes, ten company checks and five notification deliveries**. It uses durable leases and exits instead of keeping a background loop alive. Verify authentication, disabled mode, due-job processing, bounded batches, lease recovery and duplicate suppression against isolated data before enabling it. Inspect actual invocation completion and backlog afterward. Work left pending waits for a later cycle, so a large tenant set or failed provider can delay monitoring beyond one day. Manual refresh remains available. Daily processing does not provide continuous alerts.

Keep notifications empty until the destination and live test are authorized. The earlier invitation receipt does not verify a deployed alert or current sender configuration. Check provider acceptance and the intended recipient's receipt separately. Do not route real production notifications to test recipients.

## Security and remaining release gates

Verify rate limits and client-address handling in Vercel's actual proxy environment. An in-process limiter is local to one function instance; it does not establish a global abuse limit across horizontally scaled instances. Preserve application authorization and tenant checks, test rejected origins, and do not trust arbitrary forwarded headers.

Both target accounts' free plans have been verified. The hosted API package, isolated migration rehearsal, recovery comparison and 18 API capability areas now have observed evidence. Remaining gates include applicable Hobby eligibility and current quota, protected browser/OIDC proxy verification, production migration and company-ID sequence correction, production promotion, controlled restart persistence, actual daily invocation, intended business sources/delivery and representative workload performance. Record each as passed, failed, constrained or pending using observed evidence. A working free preview is not evidence of an always-on commercial platform.
