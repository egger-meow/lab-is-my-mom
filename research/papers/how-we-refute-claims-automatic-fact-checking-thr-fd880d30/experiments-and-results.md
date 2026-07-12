# Experiments and results

## Observed result (reported; not reproduced)

The experiments use Vicuna-7B-v1.5 with LoRA rank 8. Justifications are scored with ROUGE and BERTScore; Gemini Pro is used for correctness and completeness scoring because the paper states there is no existing metric for those qualities (p. 3).

For false claims, RefuteClaim-7F reports ROUGE-1 0.3266 and ROUGE-L 0.1739, versus 0.3151 and 0.1644 for the baseline. On Gemini-Pro correctness/completeness, it reports 0.5088/0.5381 versus 0.4770/0.5165 (Tables 1–2, p. 4).

The paper reports weaker justification performance for unproven claims and difficulty separating partly-false, false, and unproven classes (pp. 3–4).

## Evidence caveat

These are reported automatic and model-judge scores; they are not a human replication or a proof that generated explanations are faithful to model internals.
