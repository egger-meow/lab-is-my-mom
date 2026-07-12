# Experiments and results

## Observed result (reported; not reproduced)

For resource-rich language pairs, the method reports improvements over LLaMA-3-8B in every Table-2 cell; for example Zh→En COMET/ROUGE-L rises from 79.65/47.85 to 79.90/50.67 (Table 2, p. 3). For low-resource tests, the paper reports gains for Heb→En and Swh→En but lower En→Swh scores (Table 3, p. 3).

For Zh→En, the 8B ParaAlign model reports COMET 79.90 and ROUGE-L 50.67, compared with 79.11/47.29 for ordinary fine-tuning and 80.24/50.32 for few-shot LLaMA-3-70B (Table 5, p. 4).

The data-size analysis reports that 500 paraphrased pairs underperform ordinary training on ROUGE-L, while 1,000 pairs (about 5% of the original set) reach 51.22% and stabilize thereafter (p. 4).

## Evidence caveat

The results are reported using COMET and ROUGE-L. They support the stated benchmark comparisons, not a general guarantee of idiomatic translation or semantic preservation.
