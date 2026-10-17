# DATALYZE release verification

Record updated 16 October 2026 for the actual Desktop project at `C:\Users\revan\OneDrive\Documents\Desktop\DATALYZE`. This records implemented behavior and the scope of verification. It does not certify that every analyst activity is equally mature or that the application is deployed to production.

## Release identity and current status

The prepared source is published as [draft pull request #3](https://github.com/revanthjoshua/DATALYZE/pull/3). The original published head, `718b6561018646cbf1a33ce61923da3b2b405a1b`, passed all three jobs in [release CI run 38759806470](https://github.com/revanthjoshua/DATALYZE/actions/runs/38759806470): backend tests, the standard frontend build, and PostgreSQL 18 migration/readiness checks. This was verified on 16 October. The local Desktop source and public branch exclude runtime secrets, databases and uploaded datasets.

A follow-up candidate updates CORS/rate-limit response handling, adds driver-specific 10-second database connection timeouts, and updates frontend dependencies. Its standard local frontend build and production-dependency audit passed; its new CI result must be recorded against its own commit before release. The successful original run does not cover subsequent changes. See [dependency security status](DEPENDENCY_SECURITY.md) for the remaining development-tool warnings.

No Render services have been provisioned. The 18 cloud capability checks in [the acceptance map](POST_DEPLOY_VERIFICATION.md) remain **Pending**.

## Product delivered in the release

- A connected **Brief → Prepare → Explore → Investigate → Share → Monitor** workspace, with separate data collection, metric directory, dashboard, export and administration pages. The inventory simulator is retired, and the dataset assistant identifies itself as rule-based.
- Revision-protected data replacement, complete editor round-trips within the documented limit, recoverable replacement backups and preserved missing values/text identifiers. Malformed records are rejected. Preview application uses the parameters and revision captured by that preview.
- A company dataset library with immutable saved snapshots, checksums, preview/download, activation, archive/restore and validated composite-key joins. Uploading to the library does not replace the active source. One source remains active per company. The final regression checks verify that saving active-source snapshots, activating new or legacy snapshots, and joining them preserve public source columns without adding generated helper columns to the resulting source; legitimate underscore-prefixed columns in raw uploads remain intact. Legacy immutable previews retain their originally stored columns.
- Chained cleaning and transformations, safe arithmetic columns, grouped analysis, formula KPIs, correlations, permutation tests, bootstrap intervals, forecast model comparison and signed segment-contribution investigation with method limits. Statistical association and contribution decomposition are not described as causal proof.
- Saved evidence with source revisions, findings and proposed actions; immutable stakeholder report packages, company-authenticated links and review history. Viewers can read/download but cannot write through the covered API/UI paths.
- Operator-approved database/API snapshot imports, persisted refresh schedules with revision/lease protection, monitoring rules and a durable notification outbox with retry and delivery status. External destinations remain opt-in.
- Health/readiness checks, database migrations, deployment configuration, strict configured origins, email failure handling and security/tenant regression coverage. Invitation return paths, truthful deletion messaging and pasted-data parsing received final UI corrections.

The full feature map, limits and operator settings are in `ANALYST_WORKSPACE.md`.

## Release checks

| Check | Evidence and scope |
| --- | --- |
| Backend suite | The original published head passed **156 tests in 16.59 seconds** in Linux release CI. Earlier Desktop validation passed 156 in 62.97 seconds on 15 October. These tests use an isolated database and mocked email; the follow-up candidate needs its own recorded result. |
| TypeScript | Passed in the original Linux CI run and in the follow-up candidate's standard local `npm run build` on 16 October. |
| Production frontend bundle | The original Linux CI run passed the standard `npm ci` / `npm run build` path with **2,401 modules**. After dependency updates, the standard local build passed on 16 October: **2,228 modules**, **63.79 KB CSS**, **363.39 KB application bundle**. No configuration-loader workaround was needed for that latest build. |
| Frontend dependency audit | The updated candidate returned **zero production-dependency findings** with `npm audit --omit=dev`. The full audit still reports **7 development-tool findings (5 high, 2 moderate)**; see `DEPENDENCY_SECURITY.md`. This is not a claim that every dependency is vulnerability-free. |
| Render manifest | Validated against Render's official Blueprint JSON schema using `jsonschema`, with the latest repeat passing on **15 October**. This validates the manifest's structure; it does not provision services or execute a cloud build. |
| PostgreSQL migration | Original Linux CI upgraded a fresh disposable **PostgreSQL 18** database through **`d91e5f7c201a`**, repeated the upgrade, checked migration head and all model tables, and passed production-mode readiness. Local migration/startup checks also passed earlier. Neither is a migration of a live customer database. |
| Concurrent tenant reads | **3 tenants, 96 profile reads, 8 workers; zero errors and no mixed tenant data.** Latest measured median was **1.349 s**, p95 **2.043 s** while other tests were running. Earlier measurements were **0.279 s / 0.416 s**. These small-fixture runs check concurrency behavior, not production capacity. |
| Concurrent replacements | **6 simultaneous replacements** based on one source revision produced **one success and five 409 stale-revision conflicts**. |
| Real database connector | A read-only PostgreSQL source imported **2 fixture rows**, with the expected sum **30** verified. |
| Real API connector | A live HTTPS public API imported **100 JSON records**. This is a connector fixture, not the user's business system. |
| Invitation delivery | One explicitly authorized invitation was sent from the isolated preview, its token was verified, and the recipient confirmed **Received**. No additional invitation is required merely to repeat this check. |
| Automated notifications | Refresh/outbox behavior is exercised in tests, including failures, retries and stale leases. Tests of provider acceptance use a substitute provider; they do not demonstrate live outbox email/webhook delivery or inbox receipt. |
| Multiple input formats | CSV, XLSX and JSON analyst workflows are covered, including preparation, analysis, evidence, reporting and monitoring; larger editor fixtures verify that saving does not truncate to a preview. |
| Browser verification | On 14 October, the report 5 link returned to its report after administrator login; a Viewer could read the report, while upload/edit/delete controls were disabled; all eight main routes loaded. The public API schedule recorded an unattended check with unchanged content. The fixture schedule was then disabled. On **15 October**, activating **Sales baseline** succeeded and the active dataset header showed **`review_sales.csv`, 80 rows, 6 columns**. See the browser scope below. |

### Build procedure and remaining environment limits

The release uses the standard frontend command, `npm ci && npm run build`; the build includes TypeScript checking. That path passed in Linux CI for the original published head. The follow-up dependency update also passed the standard local build on 16 October. The earlier 13 October programmatic Vite workaround is historical and is no longer needed for the latest local build.

A passing CI build does not establish a successful Render deployment, correct production origins, live email settings or a healthy deployed application. Local Docker execution was not confirmed because the Docker daemon was unavailable; container configuration changes must not be represented as a passed container smoke test.

### Browser evidence and scope

Observed flows included all main navigation destinations rendering; an 80-row preparation preview; saved contribution evidence reopening with reconciled results and caveats; creating and reviewing a stakeholder report; saving and previewing a library snapshot; importing the live 100-row API fixture; enabling its refresh schedule; and monitoring freshness/missingness results. The 14 October pass additionally verified login return paths, Viewer report access and disabled Viewer data writes, and an unattended public API refresh that reported unchanged content. These observations are narrower than an exhaustive check of every button and every role.

On 15 October, the browser confirmed successful activation of **Sales baseline**. The active dataset header showed **`review_sales.csv`, 80 rows, 6 columns**. The legacy immutable snapshot's preview still shows its seven originally stored columns; activation excludes its generated helper column from the active source without rewriting that saved snapshot.

The same browser pass previewed a calculated profit column (`revenue - cost`) on those 80 rows, showing the expected **40** and **50** in the first two rows; the transformation was not applied. A **7-day daily-revenue forecast** ran and saved evidence with its source revision. Linear trend was selected with validation MAE **5.89231**, compared with **24** for last observed value, **38.98141** for recent mean and **40.26667** for weekly seasonality. Per-horizon validation counts of **10 down to 4** and the empirical-range caveats rendered. This confirms the exercised preview, forecast and evidence flows, not forecast accuracy on unseen business data.

The local preview uses a disposable task database, not the user's production database. Its test accounts and fixture data must not be promoted to production. The public-fixture refresh schedule is disabled, and the sales fixture is active for demonstration.

## Recorded deployment choice

Use **Render for the Python API and React static site, Render managed PostgreSQL 18 for application storage, and the existing Resend email integration**. The user delegated the choice; `DEPLOYMENT.md` records it and `render.yaml` prepares it. This is a selected deployment destination, not a claim that it is already live.

The database hosting DATALYZE's accounts, snapshots and jobs is separate from an actual business data source. Public APIs and local database fixtures prove connector behavior only. Until a company system is identified and securely connected, upload actual business data through Data collection.

## Remaining environment-specific work

1. Record the follow-up candidate's successful CI result and exact release commit. Provision the selected services in an authorized account after reviewing the recurring quote, then enter production domains and secrets securely. No hosting purchase or resource creation has been performed by this work.
2. Run migrations and readiness checks in that environment. For existing data, first rehearse against a restored backup in a separate database; never reset the live database.
3. Connect an intended business database/API and intended notification destinations, then verify a supervised refresh and an authorized email/webhook cycle using those actual services while the browser is closed.
4. Validate cloud routing, login/report return paths, invitation links, deployment restart recovery, backup restoration and performance using representative data and concurrent traffic.

**No production database was reset, no production deployment was performed, and no billing commitment was made.** Local tests, live fixture connections and one received invitation do not establish the remaining cloud-specific outcomes.
