# DATALYZE deployment approval

Updated 17 October 2026 from the actual Desktop project. This document describes the proposed next action; it does not authorize a purchase or claim a live deployment.

## Release to deploy

Use the reviewed analyst-workspace release from [draft pull request #3](https://github.com/revanthjoshua/DATALYZE/pull/3) in `revanthjoshua/DATALYZE`, with `render.yaml` at its root. Do not deploy the old main branch until it contains that release. The release preserves the existing code history and excludes local `.env` files, local databases, uploaded datasets, build output and test-runtime files.

Original release head `718b6561018646cbf1a33ce61923da3b2b405a1b` passed [all three Linux CI jobs](https://github.com/revanthjoshua/DATALYZE/actions/runs/38759806470): 156 backend tests, standard frontend build, and fresh/repeated PostgreSQL 18 migration with production readiness. Application release `c959a021e65b0f076692ba14c165a32ef8e2ddbc` passed [all three CI jobs](https://github.com/revanthjoshua/DATALYZE/actions/runs/39003978728) on **17 October 2026**: **167 backend tests**, **8 frontend login/session tests**, the standard production build and production-dependency audit, and fresh/repeated PostgreSQL 18 migration with production readiness. Documentation-only updates after this commit do not change the verified application. Full dependency audit still reports seven development-tool findings, documented in `DEPENDENCY_SECURITY.md`. The verification record also preserves bounded browser, fixture connector and concurrency evidence. No cloud deployment has been verified.

## Proposed resources

| Resource | Region / size | Recurring price shown on 17 October |
| --- | --- | --- |
| Public authenticated API `datalyze-api` | Singapore, 1 CPU / 2 GB, one instance | $25/month compute |
| Private application database `datalyze-db` | Singapore, PostgreSQL 18, 0.5 CPU / 1 GB, 5 GB storage | $19/month compute plus storage |
| Public frontend `datalyze-web` | Render static site | No compute charge |

These are public prices observed on **17 October**, not an account-specific quote. The compute subtotal is **US$44/month**. At the listed $0.30/GB storage rate, reserve up to **US$1.50/month** for 5 GB, subject to included storage. This gives an estimated resource subtotal of up to **US$45.50/month**, before taxes and usage charges. Use the confirmed existing workspace without upgrading its subscription. A paid workspace subscription, if already active, may be charged separately; verify that account setting before provision. [Current Render pricing](https://render.com/pricing)

Do not treat this estimate as an enforced billing cap. No optional add-ons, additional instances, custom-domain purchase or paid workspace upgrade are included. Stop for a revised decision if the account quote differs materially.

## Execution after approval

1. Confirm the reviewed release commit and successful required checks; use manual deploys initially.
2. Confirm the account quote and create the resources from the Blueprint, with database external access disabled.
3. Configure final public origins and securely enter production secrets. No secrets belong in the repository or chat. Do not copy the preview test database or its accounts.
4. Run the fresh database migrations, readiness, routing, authenticated report links, role/tenant and restart checks. Use synthetic or explicitly approved data for the first smoke test.
5. Connect intended business sources and notification destinations only after they are identified and authorized. Uploads remain available until then. The public API fixture is not a company's business source.

The user has approved workspace inspection/preparation and public source publication with a draft pull request and CI. This does **not** authorize paid hosting. Creating paid services and publishing the Render deployment remain pending approval of the account-specific cost and action. All 18 cloud capability checks in `POST_DEPLOY_VERIFICATION.md` remain Pending.
