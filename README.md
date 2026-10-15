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

From `backend`, with its virtual environment activated:

```powershell
python -m pytest tests -q
```

This suite isolates its database, email and monitoring configuration. Older standalone audit scripts outside `backend/tests` predate the rebuild and are not the release suite. From `frontend`, run `npm run build` for TypeScript checking and the production bundle.

The [release verification record](docs/RELEASE_VERIFICATION.md) records **156 passing backend tests on 15 October 2026**, frontend checks and browser workflows, local PostgreSQL migration/concurrency checks, live connector fixtures and one confirmed invitation delivery. It also explains the Windows sandbox build workaround and the limits of those checks. These are local verification results, not a completed production rollout or an exhaustive browser test of every control and role.

## Data and analysis boundaries

- Each company has one active dataset and an immutable saved dataset library. Replacement operations use source revisions and preserve recoverable backups; existing analysis can become historical after a replacement.
- The editor supports the complete dataset up to 10,000 rows. Library snapshots and joins are bounded to 100,000 rows; further limits are in the workspace guide.
- Contribution analysis and correlation describe observed relationships, not proven causes. Forecasts compare models on historical validation windows; empirical ranges do not guarantee future coverage.
- Stakeholder links require company membership. Reports capture evidence snapshots and review history; exported files no longer have application access controls.
- Source refresh and notifications require operator-approved connections, destinations and an enabled schedule. Imports are bounded snapshots, without automatic API pagination or incremental synchronization. The browser does not need to remain open when the backend worker is configured and running.

## Deployment

The [post-deployment verification plan](docs/POST_DEPLOY_VERIFICATION.md) defines concrete checks for all 18 analyst activities, tenant isolation and recovery. The GitHub workflow in `.github/workflows/verify.yml` runs isolated backend tests, the standard Linux frontend build, and fresh PostgreSQL 18 migrations; inspect its run results before deploying.

The chosen target is **Render API + Render static frontend + Render PostgreSQL 18 + Resend**. The root [render.yaml](render.yaml) prepares those services. Follow the [deployment runbook](docs/DEPLOYMENT.md) for production settings, migration, backups, trusted proxies, costs and first-deployment checks; see [automation configuration](docs/AUTOMATION.md) for refresh and notification setup.

Cloud resources have not been provisioned by this rebuild. A live rollout still needs an authorized hosting account, review of recurring costs, securely configured production values and validation against actual business sources. Local test accounts, databases and tenant datasets must not be published or promoted to production. Keep `.env` and credentials out of Git.
