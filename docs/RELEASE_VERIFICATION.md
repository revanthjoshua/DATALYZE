# DATALYZE release verification

## Free-hosting candidate — reviewed 24 October 2026

The published source baseline is `bbcff1c46ef2113dfb108b35908c6185a38ae47c` on the existing rebuild branch. A same-origin proxy patch is integrated in the Desktop working tree but is not yet published or deployed. The Vercel Hobby and Neon Free targets remain the selected ₹0 deployment approach. No paid Render resources were created. Production promotion and production schema changes are still pending.

- **199 isolated backend tests and 12 existing frontend tests passed** for the published adaptation baseline, along with its standard production frontend build. After integrating the same-origin proxy, **all 27 frontend tests and the standard build passed on 24 October**: the 12 existing cases plus 15 proxy behavior cases. The production dependency audit reported zero vulnerabilities after updating OIDC to 4.0.3, follow-redirects to 1.16.1 and overriding the CLI helper's Zod dependency to 4.6.6. The installed OIDC helper and function entry point also passed a synthetic-token import check without network access. Cloud deployment, hosted routing and browser/OIDC verification remain pending.
- Hosted HTTP tests on an isolated synthetic Vercel/Neon preview now cover the API behavior underlying **all 18 capabilities**. The initial run on **20 October (Asia/Calcutta)** passed 15 of the 18 capability cases; three transport failures interrupted cleaning, joins and dashboard checks. The **23 October** continuation passed those three cases, the role/tenant matrix, editor/delete safety and bounded concurrent reads. The continuation also corrected the runner's role binding and expected malformed-upload status (400). The original errors remain in the evidence rather than being relabelled as passes.
- Numerical fixture checks included total profit **4,260**, mean revenue **135.25**, regional sums **4,020 / 2,472**, seven-day forecasts, contribution change **104 = 80 + 24**, statistical mean difference **64.5**, permutation p **0.0005**, and Pearson r **1**. This establishes exercised synthetic API behavior; it does not establish browser rendering, forecast accuracy on real business data, causal proof or equal maturity of all 18 areas.
- Hosted safety checks covered seven role cases (including an unrecognized role), foreign evidence/comment/metric/report rejection, a **250-row** complete editor round-trip with final identifier `ID-0249`, stale revision **409**, missing revision **428**, invalid upload preserving the active revision, and tenant-isolated deletion. Saved library restoration recovered **48 rows and five public columns**, retaining historical evidence and an immutable report.
- A bounded hosted read check used **six workers and 30 requests**: 15 authenticated identity checks and 15 foreign-report 404 checks, with no mutations or isolation failures. Observed latency was **p50 0.249 s, p95 7.066 s, maximum 7.178 s**. This small synthetic check is not a production capacity guarantee; the long tail remains material.
- Database recovery was exercised in a separate restore database: **17 original relations** matched their source rows/schema after restoration and two repeated migration executions reached `d91e5f7c201a`; readiness passed. Sixteen owned sequences were checked. One inherited company-ID sequence required repair **only in the isolated restore**. The equivalent production sequence repair is still required before releasing writes; production was read-only during recovery verification. No production reset occurred.
- The same-origin frontend proxy is prepared to keep platform OIDC credentials on the server and preserve application authentication. Its hosted routing, authorized Trusted Sources rule, browser login/report return paths, charts and print/PDF checks remain pending. Deployment protection has not been removed.
- Monitoring rules and an authenticated **manual** cron invocation passed against isolated data, with **zero external messages**. An actual platform-triggered daily invocation, real business source refresh and live alert delivery remain pending. The previously authorized invitation was received; it does not need to be resent.

Raw acceptance and recovery evidence is held in the local task workspace. Published notes omit access credentials, database connection strings, backup contents and private fixture accounts. Production data and signing secrets have not been replaced. The detailed API-versus-browser acceptance boundary is recorded in [POST_DEPLOY_VERIFICATION.md](POST_DEPLOY_VERIFICATION.md).

## Historical verification record

The sections below preserve earlier local and CI observations and their dates. They do not supersede the current status above or certify a different commit automatically.

## Release identity and current status

The prepared source is published as [draft pull request #3](https://github.com/revanthjoshua/DATALYZE/pull/3). The original published head, `718b6561018646cbf1a33ce61923da3b2b405a1b`, passed all three jobs in [release CI run 38759806470](https://github.com/revanthjoshua/DATALYZE/actions/runs/38759806470): backend tests, the standard frontend build, and PostgreSQL 18 migration/readiness checks. This was verified on 16 October. The local Desktop source and public branch exclude runtime secrets, databases and uploaded datasets.

Application release `c959a021e65b0f076692ba14c165a32ef8e2ddbc` passed [all three CI jobs](https://github.com/revanthjoshua/DATALYZE/actions/runs/39003978728) on **17 October 2026**: **167 backend tests**, **8 frontend login/session tests**, the standard production build and production-dependency audit, and fresh/repeated PostgreSQL 18 migration with production readiness. That historical CI result certifies this commit; subsequent application and deployment changes require their own recorded verification. The fixes preserve CORS/request-ID/retry headers on 429 responses, bound known database-driver connection setup, update frontend dependencies, and restore report links after session expiry without letting stale authentication responses overwrite a newer login. See [dependency security status](DEPENDENCY_SECURITY.md) for the remaining development-tool warnings.

No Render services have been provisioned. The current isolated hosted API results are recorded above and in [the acceptance map](POST_DEPLOY_VERIFICATION.md); hosted browser checks and production acceptance remain pending.

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
| Backend suite | The original published head passed **156 tests in 16.59 seconds** in Linux release CI. Earlier Desktop validation passed 156 in 62.97 seconds on 15 October. These tests use an isolated database and mocked email; the final application release passed **167 in 14.64 seconds** in [CI](https://github.com/revanthjoshua/DATALYZE/actions/runs/39003978728). |
| TypeScript | Passed in the original Linux CI run and in the follow-up candidate's standard local `npm run build` on 16 October. |
| Production frontend bundle | The original Linux CI run passed the standard `npm ci` / `npm run build` path with **2,401 modules**. After dependency updates, the standard local build passed on 16 October: **2,228 modules**, **63.79 KB CSS**, **364.01 KB application bundle** after the final session-return fix. No configuration-loader workaround was needed for that latest build. |
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

On **17 October**, the current production frontend build was served locally. A clean login reopened `/analysis?report=5`. The disposable preview API was then restarted with a different test signing key to invalidate only preview sessions; reloading the same report redirected to login with the report destination preserved. Signing in again reopened **Regional review v2**, its company-only report link and review history. No production signing key, database or account was changed. Eight automated frontend regressions cover return-path validation and stale-session response guards.

Observed flows included all main navigation destinations rendering; an 80-row preparation preview; saved contribution evidence reopening with reconciled results and caveats; creating and reviewing a stakeholder report; saving and previewing a library snapshot; importing the live 100-row API fixture; enabling its refresh schedule; and monitoring freshness/missingness results. The 14 October pass additionally verified login return paths, Viewer report access and disabled Viewer data writes, and an unattended public API refresh that reported unchanged content. These observations are narrower than an exhaustive check of every button and every role.

On 15 October, the browser confirmed successful activation of **Sales baseline**. The active dataset header showed **`review_sales.csv`, 80 rows, 6 columns**. The legacy immutable snapshot's preview still shows its seven originally stored columns; activation excludes its generated helper column from the active source without rewriting that saved snapshot.

The same browser pass previewed a calculated profit column (`revenue - cost`) on those 80 rows, showing the expected **40** and **50** in the first two rows; the transformation was not applied. A **7-day daily-revenue forecast** ran and saved evidence with its source revision. Linear trend was selected with validation MAE **5.89231**, compared with **24** for last observed value, **38.98141** for recent mean and **40.26667** for weekly seasonality. Per-horizon validation counts of **10 down to 4** and the empirical-range caveats rendered. This confirms the exercised preview, forecast and evidence flows, not forecast accuracy on unseen business data.

The local preview uses a disposable task database, not the user's production database. Its test accounts and fixture data must not be promoted to production. The public-fixture refresh schedule is disabled, and the sales fixture is active for demonstration.

## Recorded deployment choice

Use the existing **Vercel frontend/backend projects and Neon Free PostgreSQL**, within the user's **₹0 budget**, with the existing email arrangement only where authorized. The user rejected the earlier paid Render proposal. `render.yaml` is a dormant historical alternative, not an authorized deployment target. See [DEPLOYMENT.md](DEPLOYMENT.md) for the free-plan limits and release procedure.

The database hosting DATALYZE's accounts, snapshots and jobs is separate from an actual business data source. Public APIs and local database fixtures prove connector behavior only. Until a company system is identified and securely connected, upload actual business data through Data collection.

## Remaining environment-specific work

1. Finish the protected same-origin preview API connection and hosted browser checks: login/report return paths, uploads/downloads, charts, role controls, deep links and print/PDF output. Authorize only the intended environment-specific Trusted Sources relationship; retain deployment protection.
2. Preserve the verified recovery artifact, recheck that it is current enough for release, and apply the reviewed production migration plus the required company-ID sequence correction without replacing production data. Then deploy/promote the tested application with production-scoped configuration and verify readiness. Recovery rehearsal has passed; the live changes have not been performed.
3. Connect an intended business database/API and explicitly authorized notification destinations, then verify a supervised refresh and an email/webhook cycle using those actual services while the browser is closed. Observe a real platform-triggered daily invocation.
4. Complete the controlled restart/redeployment persistence check and performance tests using representative datasets, realistic concurrent reads/writes and a stated latency target. The small hosted read fixture above is not sufficient for a capacity claim.

**No production database was reset, no production deployment was performed, and no billing commitment was made.** Local tests, live fixture connections and one received invitation do not establish the remaining cloud-specific outcomes.
