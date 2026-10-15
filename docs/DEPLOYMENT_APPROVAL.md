# DATALYZE deployment approval

Prepared 15 October 2026 from the actual Desktop project. This document describes the proposed next action; it does not authorize a purchase or claim a live deployment.

## Release to deploy

Use the reviewed analyst-workspace release from `revanthjoshua/DATALYZE`, with `render.yaml` at its root. Do not deploy the old main branch until it contains that release. The release preserves the existing code history and excludes local `.env` files, local databases, uploaded datasets, build output and test-runtime files.

Application validation: 156 backend tests passed, TypeScript and the local production bundle passed, and the verification record describes browser, fixture connector and PostgreSQL concurrency checks. Linux CI and the first cloud deployment must be inspected separately; a prepared workflow is not a passed run.

## Proposed resources

| Resource | Region / size | Recurring price shown on 15 October |
| --- | --- | --- |
| Public authenticated API `datalyze-api` | Singapore, 1 CPU / 2 GB, one instance | $25/month compute |
| Private application database `datalyze-db` | Singapore, PostgreSQL 18, 0.5 CPU / 1 GB, 5 GB storage | $19/month compute plus storage |
| Public frontend `datalyze-web` | Render static site | No compute charge |

The compute subtotal is **US$44/month**. At the listed $0.30/GB storage rate, reserve up to **US$1.50/month** for 5 GB, subject to included storage. This gives an estimated resource subtotal of up to **US$45.50/month**, before taxes and usage charges. Use the confirmed existing workspace without upgrading its subscription. A paid workspace subscription, if already active, may be charged separately; verify that account setting before provision. [Current Render pricing](https://render.com/pricing)

Do not treat this estimate as an enforced billing cap. No optional add-ons, additional instances, custom-domain purchase or paid workspace upgrade are included. Stop for a revised decision if the account quote differs materially.

## Execution after approval

1. Confirm the reviewed release commit and successful required checks; use manual deploys initially.
2. Confirm the account quote and create the resources from the Blueprint, with database external access disabled.
3. Configure final public origins and securely enter production secrets. No secrets belong in the repository or chat. Do not copy the preview test database or its accounts.
4. Run the fresh database migrations, readiness, routing, authenticated report links, role/tenant and restart checks. Use synthetic or explicitly approved data for the first smoke test.
5. Connect intended business sources and notification destinations only after they are identified and authorized. Uploads remain available until then. The public API fixture is not a company's business source.

The user has confirmed workspace inspection and preparation only. Creating paid services and publishing this deployment remain pending approval of the account-specific cost and action.
