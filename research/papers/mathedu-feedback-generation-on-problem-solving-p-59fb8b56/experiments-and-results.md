# Experiments and results

## Observed result (reported; not reproduced)

The dataset has 4,048 authentic student answers, with 3,050 correct and 998 incorrect; three math-education experts annotate errors and feedback, reporting Krippendorff’s alpha 0.7818 (p. 3). The chronological split is 2,836/609/603 (p. 5).

For correctness classification, the single-task LoRA model with rationales reports F-score 95.07%; o1-mini reports 94.66% without rationale. For error identification, the single-task model with rationales reports exact match 23.46% and distance 96.43 (Table 3, p. 6).

Feedback remains difficult: o1-mini reports the highest GPT-4 rating (4.70), but the paper notes verbosity and irrelevant detail; human ratings remain below the ideal 3 across models (pp. 7–8).

## Evidence caveat

These scores are reported model/human evaluations, not a replication. High final-answer classification does not establish reliable feedback for every student process.
