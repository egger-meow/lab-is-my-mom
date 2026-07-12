# Experiments and results

## Observed result (reported; not reproduced)

The evaluation uses 195 GSAT English vocabulary questions from 2006–2018; two are few-shot demonstrations and the other 193 are test questions (p. 16). The paper reports F-score and NDCG for up to 30 candidates.

ISSR reports F1@3 1.55%, F1@10 2.07%, NDCG@3 3.57%, NDCG@10 6.31%, and NDCG@30 9.82%; the version without self-review reports lower F1@3 (1.04%) and NDCG@3 (3.11%) (Table 2, p. 17).

The paper reports a 98.79% distractor-selection rate at candidate-set size 50, falling to 90.67% at size 300 (Table 5, p. 22). Selecting three distractors per round gives its best reported F1@3/NDCG@3 among the tested batch sizes (Table 7, p. 25).

## Evidence caveat

Absolute retrieval-style scores are low because suitable distractors may be absent from generated candidate pools; the paper explicitly identifies candidate generation as the bottleneck (pp. 17–19).
