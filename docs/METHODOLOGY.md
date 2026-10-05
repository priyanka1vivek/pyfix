# Experimental design

## Research question
Can TF-IDF features from a runtime traceback predict an injected bug category more accurately than an exception-name baseline on held-out mutation families?

The label is the known injected mutation, not a universal diagnosis of the root cause. Source lines embedded in a traceback are legitimate input features; full source and clean source are stored for provenance but excluded from classifier training.

## Dataset
Six classes have six expression recipes each. A recipe has a clean expression, a broken expression and an input. Both versions are executed; clean versions must exit successfully and broken versions must fail. Variable names, function names and blank-line offsets vary. These are small generated programs, not a large diverse software corpus. Their effective diversity is 36 families, regardless of row count.

Families 0–3 are training, 4 validation and 5 test for each class. Exact duplicate normalized tracebacks across splits are rejected. This prevents near-identical renamings of one recipe from appearing on both sides of evaluation, but does not remove all synthetic-template similarity or guarantee semantic independence. A stronger future study should use grouped cross-validation across many more independently authored programs and an external real-bug test set.

## Features and comparison
TF-IDF unigram/bigram features fit only on training. Five classifiers use the same input representation. Validation macro F1 determines the winner with deterministic insertion-order tie-breaking. Held-out test results are reported for all five models, but never used to choose the winner. Accuracy measures overall correctness; macro precision, recall and F1 weight each category equally. Confusion matrices reveal class-specific errors.

The majority baseline always predicts the most common training class. The exception-only baseline predicts the most frequent training label for the observed exception. This is a stronger check than chance because KeyError, IndexError and ZeroDivisionError are already highly informative. Multiple classes can produce TypeError.

PCA fits training TF-IDF converted to a bounded dense array (maximum 4,000 features) and projects test samples into two dimensions. It is visualization only. PCA introduces signed components and is not appropriate as direct input to MultinomialNB. Overlap in a 2D plot does not establish inseparability in the original feature space.

## Repair experiment
Execution with an independent pytest suite produces the failure. Classification selects category-specific instructions. The proposal provider creates a full candidate module, which is parsed and executed against the unchanged test file. Success requires pytest exit code zero; no tests collected is not success. Failed candidates can be retried up to the limit, with repeat detection. Failure returns the original source and an attempt history. The local offline rule only supports numeric-string addition and must not be presented as a general repair model.

Pytest failure output differs from the raw Python stderr used for training. This domain shift is explicitly a limitation; the integration tests establish the built-in example, not performance across all pytest failures. A future corpus should capture both formats and evaluate them separately.

There is no completed statistical evidence that category guidance improves Gemini repair rates. Demonstrating that requires a paired ablation: same bugs, same API model, same budgets, guided versus unguided proposals, and a held-out test suite unavailable to the proposer. Report test-pass rate, regressions, attempts, latency and API cost. Five or six real examples are a demonstration, not a robust generalization study.

## Security and operational scope
The server binds loopback and checks Host/Origin. Submitted source and tests are executable code. Docker is the default, trusted subprocess is explicitly opt-in, and secrets are not injected into child executions. Restricted containers reduce risk but are not an exhaustive sandbox. This is not a production multi-user API. No arbitrary repository checkout, automatic pull request or deployment is performed by the repair engine.
