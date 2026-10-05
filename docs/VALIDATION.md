# Validation — version 2

Version 1 passed its 11-test GitHub Actions run. Version 2 changes the benchmark, calibration, repair rules and UI substantially; v1 success is not used to claim v2 verification.

## Locally executed

- Program generation and all five model experiments.
- Feature ablations, calibration metrics, prediction reports and bootstrap intervals.
- Paired guided/unguided AST repair experiments.
- All 36 upstream cases across four QuixBugs programs.
- Python compilation and JavaScript syntax checking.

## CI verification

The v2 workflow installs dependencies, regenerates all results, runs core and pytest checks, builds/tests Docker, and runs Playwright against the real API on desktop/mobile. Inspect the latest [Actions run](https://github.com/priyanka1vivek/pyfix/actions) and its `experiment-results` artifact for current status and screenshots. This file will be updated when that run is verified.

Live Gemini calls and a live Gemini repair ablation remain unverified because no API key was supplied. Synthetic test scores do not establish production reliability. QuixBugs is an external challenge benchmark, not a production incident corpus.
