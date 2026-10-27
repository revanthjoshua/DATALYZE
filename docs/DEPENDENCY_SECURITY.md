# Frontend dependency security status

Updated 17 October 2026 for the follow-up release candidate in the Desktop DATALYZE project. This is the scope of the observed dependency audit, not a guarantee that the application has no vulnerabilities.

## Updated candidate

The frontend updates Axios to 1.20.0, React Router to 7.18.4, Vite to 7.3.7 and the React Vite plugin to 5.2.0. The lockfile records the resolved dependency tree. The standard local `npm run build` passed, including TypeScript: 2,228 modules, 63.79 KB CSS and a 364.01 KB application bundle after the final session-return fix.

`npm audit --omit=dev` returned **zero production-dependency findings**. The full audit still returned **7 development-tool findings: 5 high and 2 moderate**. These are the observed npm classifications, not an assertion that a development dependency can never affect a release.

## Remaining findings and limits

The remaining audit paths include Tailwind CSS 3.4.19 dependencies involving `braces` at or below 3.0.3 and `postcss-selector-parser` below 7.1.6. The audited dependency path did not offer a compatible fix for all of these findings. Do not force an untested transitive version or describe the full audit as clean.

This release retains Tailwind 3. Migrating to Tailwind 4 changes the build configuration and styling behavior, so it needs a separate compatibility review and visual regression pass. Track the remaining advisories until patched compatible dependencies are available or that migration is validated.

Use the development/build tooling only with reviewed repository source. Do not compile untrusted CSS or attacker-supplied glob patterns, and keep development servers bound to loopback. The production frontend is served as static assets rather than through a Vite development server. These constraints reduce exposure; they do not erase the audit findings.

## Release gate

The original published head `718b6561018646cbf1a33ce61923da3b2b405a1b` passed [release CI run 38759806470](https://github.com/revanthjoshua/DATALYZE/actions/runs/38759806470). That earlier run predates these dependency updates. Application release `c959a021e65b0f076692ba14c165a32ef8e2ddbc` passed [all three CI jobs](https://github.com/revanthjoshua/DATALYZE/actions/runs/39003978728) on **17 October 2026**: **167 backend tests**, **8 frontend login/session tests**, the standard production build and production-dependency audit, and fresh/repeated PostgreSQL 18 migration with production readiness. Documentation-only updates after this commit do not change the verified application. Keep the lockfile in the reviewed source and use `npm ci` for repeatable release installation.
