# Demo and viva notes

## Five-minute demo
1. Explain why TypeError alone can mean different things: a wrong operand type, None usage, or the wrong number of arguments.
2. Show `dataset.py`: a working expression, its mutation, the execution checks, and the family split.
3. Open Model evaluation. Explain validation versus test and compare the selected model against the exception-only baseline. Read actual values, not promised accuracy.
4. Open Repair workspace. Run the loaded example. Show the original failure, prediction, diff, and independently verified candidate.
5. Change the behavior contract and tests to require different behavior. Explain that a patch must satisfy tests, not merely stop crashing. Unsupported offline repairs need Gemini or human review.
6. End with the synthetic-data limitation and the need for a real-world benchmark.

## Likely questions
**Where is ML?** The trained text classifier maps a traceback to a known mutation category. Patching is a separate rule/API component.

**Why not just use the exception name?** Some exceptions are already useful, so we measure that baseline. Several categories share TypeError; contextual traceback text may help distinguish them.

**Why these five algorithms?** Naive Bayes is a lightweight text baseline, logistic regression and linear SVM handle sparse text well, and random forest/AdaBoost provide contrasting tree-based approaches. Comparison is empirical, not a guarantee that every algorithm is suited equally well.

**Why not PCA before Naive Bayes?** MultinomialNB needs nonnegative features; centered PCA can produce negatives. PCA is used for exploratory visualization, while the classifiers use TF-IDF.

**Why macro F1?** It balances precision and recall while giving every class equal weight. It complements accuracy.

**Is the model accurate on actual repositories?** That has not been established. The current result is for held-out synthetic families.

**Does a successful test run prove a correct fix?** No. It only demonstrates agreement with the supplied tests. Better test coverage and independent hidden tests reduce overfitting risk.

**What happens without an API key?** Classification and evaluation work; one deliberately narrow offline repair demonstration works. General Gemini proposals require a configured key and model.

**Is this novel?** It is an applied ML project combining synthetic mutation data, comparative classification and verified repair. Do not claim that classifying bugs or verifying repairs is absent from existing research/tools.

**What did you build and understand?** Explain each module, execute it, and change a mutation or a test yourself. If required by your institution, disclose AI assistance. Do not claim unaided authorship or results you have not reproduced.

## Version 2 additions
- Calibration has its own six-program partition; model selection uses a different validation partition. Neither contains test programs.
- Show the feature ablation before claiming source context helps. Extra context can reduce performance; the measured result decides.
- Explain review decisions: unsupported exception, low vocabulary overlap, score threshold or close top-two scores. These are imperfect safeguards.
- The repair benchmark compares hand-written AST rules with and without category guidance, not two trained code-generation systems. Fixed candidate order influences the result.
- Withheld input tests are additional fixtures from the same program; they are not independent real-world code.
- QuixBugs tests scope limits. RecursionError/AssertionError are outside the six supported categories, so rejection is appropriate. It is not an external in-taxonomy accuracy result.
