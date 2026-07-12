# Experiments and results

## Observed result (reported; not reproduced)

The NIR dataset extends Hippocorpus with five event types for information-recall need detection (pp. 1-2). SEEN with Longformer-large reports F-score 0.6654; removing the event graph lowers it to 0.6334, the largest reported ablation drop (Table 3, p. 8). When detection is correct, support-evidence extraction F-score is 0.8095; when wrong, it is 0.6671 (Table 4, p. 8).

## Evidence caveat

The paper uses gold event graphs. End-to-end extraction quality remains a future requirement.
