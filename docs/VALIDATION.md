# Verified version 2 — 5 October 2026

[Successful GitHub Actions run](https://github.com/priyanka1vivek/pyfix/actions/runs/37340223036)

Tested code commit: `5a75be8d724e069f6be8bb127eee3897e86206ed`.

## Passed

- Editable installation on Python 3.11.
- Generation of 321 execution-verified records from 48 authored programs.
- Training/calibration of all five classifiers; feature ablations and report generation.
- Guided/unguided AST repair comparison and all 36 external QuixBugs cases.
- Ten standard-library core behavioral checks.
- All 26 pytest checks, including all six UI repair examples, API integration, rejection/retention behavior and Docker execution.
- Docker image build, unprivileged execution, read-only code mount, no network connection, and verified repair.
- Real Chromium desktop and mobile flows, including a completed repair, model/benchmark tabs, unsupported-error rejection and no horizontal page overflow.
- Desktop and mobile screenshots visually inspected; no overlap or clipping of core controls was observed. The mobile navigation scrolls horizontally by design.

The run retains reports and screenshots in its `experiment-results` artifact for 14 days. The repair-studio screenshot is also committed in `docs/repair-studio.png`. A third-party TestClient deprecation warning was reported; it did not fail the suite.

## Measured repair comparison

Guided: 11/12 programs pass visible tests, 27 candidate attempts. Unguided: 8/12, 48 attempts. Of ten programs with additional withheld inputs, guided passes nine and unguided six. This is the local AST-rule experiment, not a Gemini result. Fixed unguided ordering and the small synthetic test set limit the conclusion.

QuixBugs: four external challenge programs, 36 upstream cases, 29 failing cases; all 29 are sent for review. Unsupported-exception rules explain this result; it is not evidence of production root-cause accuracy.

## Still unverified / out of scope

- Live Gemini calls or a live Gemini guidance ablation: no API key supplied.
- External in-taxonomy production bug classification accuracy.
- Hardened public multi-user execution or a hosted deployment.

The tested code is followed only by documentation/screenshot updates. Synthetic scores and passing tests must not be presented as proofs of correctness or real-world reliability.
