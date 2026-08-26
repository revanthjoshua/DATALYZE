# Datalyze — From Data to Decisions

**AI-Powered Business Intelligence & Decision Intelligence SaaS Platform**

---

## Core Pipeline Architecture

```
MEASURE ──► DETECT ──► EXPLAIN ──► PREDICT ──► RECOMMEND
```

1. **Measure**: Continuously track defined KPIs from ingested company data on an automated daily cadence.
2. **Detect**: Compare current KPI values against historical baselines, trend lines, and seasonal expectations to flag variance.
3. **Explain**: Investigate contributing dimensions (product, region, channel) to surface probable root causes in plain language.
4. **Predict**: Forecast near-future KPI values with honest confidence intervals.
5. **Recommend**: Translate detection + explanation + forecast into practical operational actions.

---

## Tech Stack

- **Frontend**: React 18, TypeScript, Tailwind CSS, Recharts, Lucide Icons, Vite
- **Backend**: Python 3.11+, FastAPI (async, Pydantic validation), SQLAlchemy ORM
- **Database**: PostgreSQL (with SQLite support for local dev/testing)
- **Multi-Tenancy**: Application-enforced `tenant_id` scoping in repository layer on every query

---

## Running Locally

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

API docs will be available at `http://localhost:8000/docs`.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

App will be available at `http://localhost:5173`.

### 3. Automated Tests & Tenant Isolation

```bash
cd backend
python -m pytest tests/ -v
```
