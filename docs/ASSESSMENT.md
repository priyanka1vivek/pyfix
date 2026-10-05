# Assessment submission

**Title:** Traceback-Based Bug Classification for Automated Python Repair

**Domain:** Machine Learning

**Abstract:** This project investigates supervised classification of Python failures and the usefulness of predicted bug categories in test-verified repair. A reproducible synthetic corpus is built by injecting six mutation types into 48 task programs and retaining execution-verified failures. Programs are separated into training, calibration, validation and test partitions. Five TF-IDF classifiers are compared using macro F1, accuracy, confusion matrices and program-level bootstrap intervals. Feature ablations compare exception-only, traceback-only and traceback-plus-code inputs. Calibrated scores and review rules handle some uncertain or unsupported inputs. Predicted categories guide AST repair candidates, which must pass unchanged tests before acceptance. A paired fixed-budget experiment compares guided and unguided repair, and an external QuixBugs challenge evaluates scope rejection. A local web interface exposes predictions, feature evidence, patches, test output and experiment results. Generalization to production bugs remains an open limitation.

**Problem statement:** Exception names alone can be insufficient to distinguish programming mistakes. Developers need contextual diagnosis and verification of candidate changes. This project studies whether text classification can add useful structure to a bounded repair search and makes its limitations visible through baselines, ablations and external scope checks. It does not claim that prior repair tools lack diagnosis or test verification.

**Tools:** Python 3.11+, scikit-learn, NumPy, Pandas, Matplotlib, joblib, FastAPI, HTML/CSS/JavaScript, pytest/unittest, AST transforms, subprocess, Docker, optional Gemini REST API, GitHub Actions and Playwright. PCA is for visualization, not Naive Bayes input.

**Applications:** Educational debugging demonstrations and controlled software triage experiments. CLI audit output can support a developer-reviewed CI workflow. Arbitrary repository repair, public execution of untrusted programs and production classification accuracy are not established.
