# Validation status — 5 October 2026

## Executed successfully

- Generated 410 mutations; each original executed successfully and each retained mutant failed.
- Trained all five classifiers and generated held-out metrics, per-class reports, confusion matrices and a PCA plot.
- Ten standard-library behavioral checks passed; output is saved in `artifacts/core-checks.txt`.
- Core repair was exercised against an independent unittest suite, including incorrect and invalid patch rejection, retry stopping and original source retention.
- GitHub Actions successfully installed the package, regenerated the dataset, trained all five models and passed all 11 pytest tests, including FastAPI endpoint integration. [Verified run](https://github.com/priyanka1vivek/pyfix/actions/runs/37267046220), code commit `360c9a87ce49f397816629baec65e60272807300`. One third-party TestClient deprecation warning was reported.
- Python source compiled and frontend JavaScript passed Node's syntax check.

## Not executed in this build environment

- Docker execution: Docker was unavailable.
- Live Gemini generation: no user API key was supplied.
- Browser visual verification: a Playwright package was present, but no browser executable was installed.

These are outstanding checks, not passing checks. Build `Dockerfile.runner` and run the web demo under Docker before treating that path as verified. The first CI run exposed an editable-install package-discovery error; explicit package discovery fixed it, and the next run passed.

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
