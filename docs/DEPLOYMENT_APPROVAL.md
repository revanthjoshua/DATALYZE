# DATALYZE deployment authorization and budget

Updated **19 October 2026** from the user's explicit decision: **hosting budget ₹0; do not create paid Render services.** The former Render purchase proposal is rejected and superseded. No Render service was provisioned by this rebuild.

## Authorized direction

Use the user's existing Vercel frontend/backend and Neon Free PostgreSQL wherever technically feasible. The Vercel team is verified on Hobby, with frontend project `datalyze-y9n8` and backend project `datalyze` linked to the existing GitHub repository. Neon project `purple-cell-52986724` is verified on Free (`free_v3`), running PostgreSQL 18. Continue within those free plans while preserving the rebuild, repository, domains and production data. This record does not claim a completed deployment or production migration.

The rebuild branch now has isolated preview environment settings: database and application URLs fail closed until real preview values are selected, source/notification lists are empty, and email is disabled. After Free-plan and usage inspection, verification branch `codex-release-verification-20261019` (`br-holy-star-azv1fzxn`) was created from production parent `br-late-base-az4po99q`. Its endpoint uses fixed 0.25 CU and default suspension. No production data was written. Treat the copied branch as confidential and recheck quota before further work; migration rehearsal, recovery and live verification are still pending.

Source publication to the separate branch and draft pull request with CI remains authorized. Use [draft pull request #3](https://github.com/revanthjoshua/DATALYZE/pull/3), branch `codex/analyst-workspace-rebuild`. Preserve release history; do not deploy old `main` or treat the source-publication approval as a completed merge.

## Spending and data boundary

- No paid services, plan upgrades, trials that require a later charge, paid add-ons or domain purchases are authorized. Do not create the dormant `render.yaml` Blueprint.
- Verify the current Vercel/Neon plans and available quotas before deploying or creating a test branch. Do not downgrade an existing account automatically. Stop any action that would incur charges.
- Vercel Hobby is restricted to personal, non-commercial use. Free eligibility must fit the intended deployment; a commercial use case is not permission to upgrade. [Vercel Hobby](https://vercel.com/docs/plans/hobby)
- Preserve production data and secrets. Preview tests use isolated database/environment settings and disabled outbound integrations. Before a live migration, verify a secure backup and a data-preserving rehearsal against a separate copy. No production reset or destructive restore is authorized.
- Existing email delivery evidence does not authorize new recipient messages. Keep refresh sources and notification destinations empty until their actual systems and intended recipients are known and authorized.

## Concrete free release sequence

1. Finish inspection of deployed commits, domains, environment scopes and schema revision in the identified free projects; recheck quota before using it.
2. Validate the Vercel adaptation and its Python bundle on an isolated preview, within the actual accounts' free allowance.
3. Back up production and rehearse migration/recovery without modifying the original database.
4. Run the 18 capability, tenant, role and bounded performance checks on the preview. Explain constraints and fix demonstrated failures.
5. Apply the verified release/migration to the existing deployment, preserve accounts and data, and record live verification results.

The detailed configuration, free-hosting constraints and recovery procedure are in [DEPLOYMENT.md](DEPLOYMENT.md). The candidate keeps scheduling in manual mode until explicitly configured for daily operation, with a separate cron secret and bounded processing. Free resources can pause or reject work at their limits; they do not promise unlimited datasets, minute-level monitoring or uninterrupted availability. See the current [Vercel function limits](https://vercel.com/docs/functions/limitations), [daily cron constraints](https://vercel.com/docs/cron-jobs/usage-and-pricing) and [Neon Free plan](https://neon.com/pricing).

## Evidence preserved

Application release `c959a021e65b0f076692ba14c165a32ef8e2ddbc` passed [CI](https://github.com/revanthjoshua/DATALYZE/actions/runs/39003978728): 167 backend tests, eight frontend session tests, production build/dependency audit and PostgreSQL 18 migration/readiness. Documentation-only release `66cfbfaf7a5a7083eea3f7e0e3f257c4895be6f1` also passed [CI](https://github.com/revanthjoshua/DATALYZE/actions/runs/39023915280). These remain historical results, not proof that later serverless changes passed or that a live rollout occurred.

[RELEASE_VERIFICATION.md](RELEASE_VERIFICATION.md) retains the local, fixture connector and browser evidence. [DEPENDENCY_SECURITY.md](DEPENDENCY_SECURITY.md) records remaining development-tool findings. All 18 hosted checks in [POST_DEPLOY_VERIFICATION.md](POST_DEPLOY_VERIFICATION.md) remain pending until observed on the released service.
