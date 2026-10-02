# Kiro quality-tool adoption requirements

Owner: contracts/programs/KIRO_DEVELOPMENT_ENVIRONMENT.md. Phase: research 3-6 (KDE04-08).
NIZAM-derived from the owner's 2026-09-16 request to run remaining phases and install
high-ranked GitHub projects. Local package installation is authorized for this increment.

1. Preserve existing files, settings, financial policy and application dependencies.
2. Inspect provenance, published package/license and selected source before installation.
   Pin fast-check, axe-core and Stryker in a separate private developer-tool package;
   disable lifecycle scripts and never run bulk upstream setup or global installers.
3. Test bounded synthetic properties including a deliberately false property. Exercise
   existing research validation with generated invalid input without changing its checks.
4. Run mutation testing only on a copied synthetic fixture in an owned temporary tree,
   with finite timeout, concurrency one and explicit files. Never mutate repository files.
5. Run accessibility positive/negative controls in a fresh headless browser, block
   non-loopback requests and websockets, never use personal profiles. Inspect the empty
   built app separately; report genuine violations without suppressing rules.
6. Produce versioned source/installation evidence, rankings, rejection reasons, a 26-section
   blueprint, migration/rollback and actual command receipts. Installation is not Kiro activation.
7. Run focused tests and unchanged repository acceptance. Preserve failures and all
   prior work. No commit, push, host/cloud action, credentials, OAuth or human gate work.
