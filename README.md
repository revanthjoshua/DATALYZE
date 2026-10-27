# DATALYZE

DATALYZE is a company-scoped data analyst workspace for preparing data, investigating changes, preserving evidence and sharing decisions. Its main flow is:

**Brief → Prepare → Explore → Investigate → Share → Monitor**

| Stage | Purpose |
| --- | --- |
| Brief | Record the business question, objectives and success measures. |
| Prepare | Clean and transform data, preview changes, and join saved datasets. |
| Explore | Inspect distributions, summaries, dimensions and metric definitions. |
| Investigate | Compare segments, run statistical tests and validated forecast models, and save evidence. |
| Share | Record findings and proposed actions, package evidence into reports, and collect stakeholder reviews. |
| Monitor | Evaluate targets and data quality; optionally refresh approved sources and deliver configured notifications. |

Data collection manages uploads, pasted records, the editor and a saved dataset library. The metric directory, dashboard and reports provide focused views of the same company data. The inventory simulator is retired. Noah is a rule-based dataset assistant; it does not use a language model or execute business actions.

See the [workspace guide](docs/ANALYST_WORKSPACE.md) for the mapping to all 18 analyst activities, supported operations and limits.

## Run locally

Use Python **3.12** and Node **24**. The recorded validation used Python 3.12.14 and Node 24.16.0. The application uses React, TypeScript and Vite, with a FastAPI/SQLAlchemy backend. SQLite supports local use; PostgreSQL is the selected production database.

The commands below use PowerShell from the project directory. Use a local configuration and database. Preserve an existing `.env` file instead of overwriting it, and never run development setup against a production database.

### Backend

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (-not (Test-Path -LiteralPath .env)) { Copy-Item -LiteralPath .env.example -Destination .env }
```

Before starting, review `backend/.env`. The example selects a separate local SQLite file, local origins, database-backed dataset storage, empty source/notification lists and a disabled monitoring worker. If an `.env` already exists, verify these settings explicitly:

```dotenv
ENVIRONMENT=development
DATABASE_URL=sqlite:///./datalyze-local.db
STORAGE_BACKEND=db
CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
FRONTEND_URL=http://localhost:5173
RESEND_API_KEY=
DATALYZE_SOURCES_JSON=[]
DATALYZE_NOTIFICATIONS_JSON=[]
DATALYZE_MONITOR_INTERVAL_SECONDS=0
```

Keep the development-only `SECRET_KEY` from the example for local use. Production requires a separately generated secret. Then initialize the local database and start the API:

```powershell
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --port 8000
```

API documentation: <http://localhost:8000/docs>. Readiness: <http://localhost:8000/health/ready>.

### Frontend

In a second terminal, from the project directory:

```powershell
cd frontend
npm ci
$env:VITE_API_BASE_URL = "/api/v1"
npm run dev
```

Open <http://localhost:5173>, register a company administrator, and upload data through Data collection. The local Vite server forwards `/api` to port 8000. Invitations and password-reset delivery require a configured Resend account; empty credentials do not simulate successful delivery.

## Verification

From `backend`, with its virtual environment activated, install the test dependencies before running the suite. Deployment installs use `requirements.txt`; `requirements-dev.txt` includes that runtime file plus pytest tools.

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
```

This suite isolates its database, email and monitoring configuration. Older standalone audit scripts outside `backend/tests` predate the rebuild and are not the release suite. From `frontend`, run `npm test` for login/session regression checks and `npm run build` for TypeScript checking and the production bundle.

The [release verification record](docs/RELEASE_VERIFICATION.md) links the published release and its CI results, frontend checks and browser workflows, PostgreSQL migration/concurrency checks, live connector fixtures and one confirmed invitation delivery. Standard frontend builds now pass locally and in Linux CI. The [dependency review](docs/DEPENDENCY_SECURITY.md) records remaining build-tool advisories. These results do not establish a completed production rollout or an exhaustive browser test of every control and role.

## Data and analysis boundaries

- Each company has one active dataset and an immutable saved dataset library. Replacement operations use source revisions and preserve recoverable backups; existing analysis can become historical after a replacement.
- The editor supports the complete dataset up to 10,000 rows. Library snapshots and joins are bounded to 100,000 rows; further limits are in the workspace guide.
- Contribution analysis and correlation describe observed relationships, not proven causes. Forecasts compare models on historical validation windows; empirical ranges do not guarantee future coverage.
- Stakeholder links require company membership. Reports capture evidence snapshots and review history; exported files no longer have application access controls.
- Source refresh and notifications require operator-approved connections, destinations and an enabled schedule. Imports are bounded snapshots, without automatic API pagination or incremental synchronization. The browser does not need to remain open when the backend worker is configured and running.

## Deployment

The current budget is **₹0**. The user selected the existing **Vercel frontend/backend with Neon Free PostgreSQL** and rejected the paid Render proposal. On **19 October 2026**, Vercel Hobby was confirmed for frontend `datalyze-y9n8` and backend `datalyze`; Neon Free and PostgreSQL 18 were also confirmed. The root `render.yaml` is retained as a dormant historical configuration; do not provision it. Follow the [free deployment runbook](docs/DEPLOYMENT.md) and [authorization record](docs/DEPLOYMENT_APPROVAL.md).

The free target suits a small, intermittent, personal/non-commercial deployment within account quotas. The Vercel configuration uses Python 3.12/FastAPI, database-backed storage and a 300-second function limit. Files and responses are capped at 4,000,000 bytes; complete requests at 4,250,000 bytes. Monitoring defaults to manual mode, with an opt-in daily cron job and bounded batches. Larger analyses remain available locally. See the runbook for provider limits and unresolved compatibility checks.

An isolated Neon verification branch has been created; production data has not been modified. Verify backup plus migration recovery before changing production. Branch-specific preview settings fail closed until the intended database and URLs are configured; email, sources and notifications remain disabled there. Never run migrations automatically during Vercel builds or function startup. Preserve existing accounts, domains, datasets and secrets; do not copy local fixture users into production or activate paid resources.

The [post-deployment verification plan](docs/POST_DEPLOY_VERIFICATION.md) defines checks for all 18 analyst activities, tenant isolation and recovery. The GitHub workflow runs backend/frontend tests, a production frontend build and fresh PostgreSQL 18 migrations. Historical release checks passed; serverless changes require their own checks and real Vercel build. A production rollout, migration recovery and all 18 hosted checks remain pending until recorded with evidence.
