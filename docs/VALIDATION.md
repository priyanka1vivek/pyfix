# Validation status — 5 October 2026

## Executed successfully

- Generated 410 mutations; each original executed successfully and each retained mutant failed.
- Trained all five classifiers and generated held-out metrics, per-class reports, confusion matrices and a PCA plot.
- Ten standard-library behavioral checks passed; output is saved in `artifacts/core-checks.txt`.
- Core repair was exercised against an independent unittest suite, including incorrect and invalid patch rejection, retry stopping and original source retention.
- Python source compiled and frontend JavaScript passed Node's syntax check.

## Not executed in this build environment

- The full pytest suite and FastAPI HTTP integration: pytest, FastAPI and associated packages were unavailable and package installation failed in the restricted environment.
- Docker execution: Docker was unavailable.
- Live Gemini generation: no user API key was supplied.
- Browser visual verification: a Playwright package was present, but no browser executable was installed.

These are outstanding checks, not passing checks. Install the declared dependencies and run `python -m pytest -q`; build `Dockerfile.runner` and run the web demo under Docker before treating that path as verified. A GitHub Actions workflow is included but has not run because the project has not yet been published to a repository.

## Measured synthetic results

| Model | Validation macro F1 | Test accuracy | Test macro F1 |
|---|---:|---:|---:|
| Naive Bayes | 0.971 | 94.37% | 0.943 |
| Logistic regression (selected) | 1.000 | 100.00% | 1.000 |
| SVM | 1.000 | 100.00% | 1.000 |
| Random forest | 0.387 | 56.34% | 0.504 |
| AdaBoost | 0.225 | 32.39% | 0.222 |
| Exception-only baseline | — | 83.10% | 0.778 |

Train: 271 rows. Validation: 68. Test: 71. The independent recipe count is much smaller than the row count: 24 train, 6 validation and 6 test families. Perfect performance on this easy synthetic split must not be presented as real-world reliability.
