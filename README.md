# PyFix
### Traceback-Based Bug Classification for Automated Python Repair

A reproducible ML project that generates labelled Python failures, compares five classifiers, and uses the predicted bug category to guide a test-verified repair loop. Includes a FastAPI web workspace, CLI, offline demonstration, optional Gemini patch generation, experiment outputs and automated tests.

**Build status:** Dataset generation, model training and all 11 pytest tests (including FastAPI integration) passed on [GitHub Actions](https://github.com/priyanka1vivek/pyfix/actions/runs/37267046220). Ten additional core checks passed locally. Docker, live Gemini and browser visual checks remain outstanding; see [validation status](docs/VALIDATION.md).

## Quick start — Windows / VS Code

Use Python 3.11 or newer. Open a terminal in this project folder.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pyfix.cli generate
python -m pyfix.cli train
python -m pytest -q
```

On macOS/Linux activate with `source .venv/bin/activate`.

### Run the built-in demonstration

For your own trusted example files only, PowerShell:

```powershell
$env:PYFIX_RUNNER="trusted"
python -m pyfix.cli serve
```

macOS/Linux: `PYFIX_RUNNER=trusted python -m pyfix.cli serve`.

Open **http://localhost:8000**. The numeric-string example loads automatically. Click **Classify & attempt repair**. The offline rule attempts numeric conversion and accepts the patch only if all supplied tests pass. No API key is needed for this demo. Trusted mode executes Python on your machine; only use code and tests you trust.

### Docker execution (default for submitted code)

Install/start Docker Desktop or Docker Engine, then:

```sh
docker build -f Dockerfile.runner -t pyfix-runner:1 .
python -m pyfix.cli serve
```

Ensure `PYFIX_RUNNER` is unset or set to `docker`. Each execution has no network, a read-only root filesystem and code mount, an unprivileged user, dropped capabilities, resource limits and a timeout. This is a local educational prototype, not a hardened multi-tenant service. Docker shares the host kernel; do not expose this app publicly. The trusted runner is not a sandbox. Captured output is capped when read; output files are not quota-limited, so hostile output flooding is outside this prototype's hardening scope.

### Gemini repair

Copy `.env.example` to `.env`. Set `GEMINI_API_KEY` and `GEMINI_MODEL` to a model supported by your Google account. Restart the app and select Gemini. Never commit `.env`. Source code, traceback/test failure output and your behavior contract are sent to Google's API; test failure output may contain portions of tests. Independent tests are never replaced by a generated patch. API costs and availability depend on your account. A live Gemini request requires your own key; the delivered project does not include one.

## What is implemented

- Six mutation labels: type conversion, missing None guard, index boundary, missing mapping key, zero denominator and wrong argument count.
- 36 seed expression families, wrapped in working functions and verified by execution before mutation records are admitted.
- Reproducible generation, clean/broken source provenance, captured tracebacks and deterministic family-separated train/validation/test partitions.
- TF-IDF with Naive Bayes, logistic regression, linear SVM, random forest and AdaBoost.
- Model selection by validation macro F1; accuracy, macro precision/recall/F1, per-class reports and confusion matrices on held-out test families.
- Majority and exception-only baselines. These test whether ML adds information beyond the exception name.
- Training-fitted two-dimensional PCA plot of held-out samples. PCA is descriptive; classifiers use nonnegative sparse TF-IDF, avoiding invalid negative PCA inputs to MultinomialNB.
- Category-guided patching, external pytest verification, bounded retries, repeated-candidate detection, original-source retention on failure and unified diffs.
- Local frontend, REST API, CLI and GitHub Actions workflow.

## Reproduce the experiment

```sh
python -m pyfix.cli generate --variants 12
python -m pyfix.cli train
python -m pytest -q
```

The generator removes duplicate source strings. The final count is therefore below 432 and is recorded in `artifacts/metrics.json`. Four expression families per class train the models; one is validation and one is test. Random renaming does not cross these family boundaries. Vectorizers and PCA fit only on training data. The selected model is not refitted on validation, ensuring the shipped model reproduces the displayed test result. No inference is made from filename or label metadata.

Files in `artifacts/`: `metrics.json`, `comparison.csv`, `classification_report.json`, five confusion matrices, `pca.png`, and a locally generated `model.joblib`. Do not load joblib artifacts from unknown sources. Git ignores the model binary; rerun training after cloning.

## CLI

```sh
pyfix classify traceback.txt
pyfix repair example.py --tests test_example.py --contract "Numeric inputs plus 2" --provider gemini
```

The repair command writes a JSON audit record and returns exit code 1 when review is needed. It does not overwrite your input file. This enables a CI integration, but the repository does not automatically edit or commit arbitrary failing builds. The included workflow verifies this project's own reproducibility and tests.

## Project structure

```text
pyfix/
  dataset.py       mutation recipes, execution and provenance
  runner.py        Docker/trusted execution and timeout handling
  training.py      training, selection, baselines and plots
  repair.py        class-guided proposals and verification loop
  app.py           local REST API
  cli.py           command-line entry point
  static/          HTML, CSS, JavaScript interface
 tests/            behavioral and integration checks
 docs/             methodology, assessment summary and viva guide
 data/             generated labelled examples
 artifacts/        measured results and plots
```

## Limits that matter

This is a controlled synthetic benchmark, not evidence of production repair accuracy. Six families per label are small; variant names are not independent real programs. Exception types strongly reveal some labels. Some distinct root causes have indistinguishable tracebacks. The classifier always chooses from known labels and its scores are not calibrated; unsupported failures require review. The offline patcher supports one narrow numeric conversion demonstration. Gemini proposals can fail or overfit tests. Passing tests does not prove semantic correctness. Test files are fixed outside the patch, but adversarial Python can interfere with a test harness; this system does not claim malicious-candidate-proof verification.

A meaningful extension is a separately curated real-bug dataset and a controlled comparison of class-guided versus unguided repair, with identical models, test suites and budgets. That experiment has not been claimed as completed.

See [methodology](docs/METHODOLOGY.md), [viva guide](docs/VIVA.md), and [assessment wording](docs/ASSESSMENT.md).

## Reference documentation

- https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction
- https://scikit-learn.org/stable/modules/generated/sklearn.naive_bayes.MultinomialNB.html
- https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html
- https://ai.google.dev/api/generate-content
- https://docs.pytest.org/en/stable/

## Dependency-light core verification

The repair API also supports `test_framework="unittest"`. With the ML dependencies installed, run `python -m unittest discover -s tests -p stdlib_checks.py -v`. The browser and CLI use pytest by default. This check does not substitute for HTTP or Docker integration tests.
