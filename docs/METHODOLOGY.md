# Version 2 methodology

## Research questions
1. Can text classifiers identify six injected mistake categories in unseen small Python programs?
2. Does additional source context improve a fixed classifier over exception-only and traceback-only features?
3. Can calibration and conservative review rules communicate uncertainty?
4. Does predicted-category guidance improve a fixed-budget AST candidate search?

## Data
48 authored programs, eight per category. Four per category train the model; one calibrates, one validates and two test. Actual input values vary; duplicate fixtures are removed. Programs are short and many mutation mechanisms are related. The default 321 records contain only 48 program units, not 321 independent software projects. Clean source and mutation provenance are saved for auditing but not classifier input.

Generation runs both versions. Success of the original and failure of the mutant are required. The same immutable source module belongs to only one partition. Cross-partition checks reject shared program IDs or exact module source. This does not rule out semantic similarity between independently written programs.

## Learning protocol
Training-only TF-IDF unigrams/bigrams, capped at 5,000 features. Equal total sample weight per training program prevents programs with more fixtures dominating. Five classifiers are trained and separately sigmoid-calibrated on calibration programs. Calibration sample weights also balance programs. A FrozenEstimator guarantees the base classifier is not refitted during calibration; overlapping indices in its single calibration split refer only to the calibration set, not base-model training.

Validation macro F1 selects the winner. Ties use fixed classifier insertion order. The winner is not refitted using test or validation. Accuracy, macro precision/recall/F1 and per-class confusion matrices are reported on test. Bootstrap intervals resample whole test programs 1,000 times using seed 42. With only twelve test programs, a degenerate interval such as [1,1] is possible and must not be interpreted as certainty about unseen real software.

The fixed logistic-regression ablation varies only features: exception, traceback, traceback plus broken module code. Calibration quality uses multiclass Brier score and log loss. PCA is exploratory visualization fitted on training only; it is not fed into MultinomialNB, which needs nonnegative inputs.

## Review policy
Choose maximum validation coverage at >=85% empirical accepted accuracy over a fixed score grid; fallback threshold .95. Require at least .08 difference between the leading two scores. A supported-exception whitelist and minimum vocabulary overlap of .15 provide additional rejection rules. These heuristic guard values are engineering choices, not learned unknown-distribution guarantees. The selective test summary measures threshold plus margin on known test classes; live diagnosis also applies exception and overlap guards. Prediction explanations show relative log-likelihood contributions for Naive Bayes or linear score contributions when available, not causal explanations or a decomposition of calibrated probability.

## Repair comparison
Local AST proposals apply a single edit at a time, independently reconstructed from the original source. Six edit families: numeric casts, explicit None defaults, index/loop-bound adjustments, optional mapping lookups, restoration of an existing zero-denominator branch, and signature-related argument changes. Candidate defaults and arguments are hypotheses, not known fixes. Independent tests must validate them.

Guided uses only the predicted family; unguided uses the same families in fixed order. Both have six proposal attempts and the same visible tests. Uncertain guided diagnoses abstain and count as failures. AST candidates do not see clean source or the withheld fixtures. Oracle outputs are computed from clean programs during benchmark construction only. Withheld fixtures assess candidate agreement after visible tests pass. None-only tasks lack a distinct withheld input; report null rather than inventing hidden-test success.

This experiment measures a narrow rule-search system. Fixed unguided ordering affects its outcome. It does not establish a general benefit for language-model repair or superiority over other search strategies. The optional Gemini path uses the same API model and budget, suppressing category guidance in the unguided arm, but a live Gemini experiment remains unexecuted without credentials.

## External evidence
Four QuixBugs algorithms and their upstream test data are pinned to commit 4257f44b0ff1181dedaedee6a447e133219fcebf. They were selected as a scope challenge containing recursion and output-correctness defects. This is a convenience sample, not a random real-world dataset. Most failures are RecursionError or AssertionError and therefore trigger the explicit unsupported-exception rule. High rejection here validates that rule on these tasks, not learned open-set recognition.

## Limitations and reproducibility
Raw Python tracebacks train the model; pytest/unittest reports are a different input format. Built-in example integration tests check a few such failures, not broad format generalization. No external in-taxonomy production bug accuracy is established. Passing tests is evidence of behavior on those cases, not proof of correctness. The proposal provider could overfit visible tests, and executable candidates can interfere with their own process.

The repository includes seeds, generation code, program definitions, reports, plots, provenance, licensed external fixtures and CI. No test metrics are fabricated. Live API costs, Gemini effectiveness, production deployment and safe multi-tenant execution are outside the demonstrated scope.
