# Experiments and results

## Observed result (reported; not reproduced)

The test split contains 300/10/46 gold pairs for training, validation, and test; silver and platinum pairs are training-only. The paper uses Vicuna-7B-v1.5 for student questions and GPT-3.5 for reference questions (p. 3).

On its multiple-candidate/multiple-reference protocol, E-QGen reports ROUGE-1/ROUGE-2/ROUGE-L/BERTScore of 0.2667/0.0866/0.2160/0.8642, above its GPT-4 comparison on the three ROUGE metrics (0.2505/0.0658/0.1967/0.8615) (Table 1, p. 3).

Removing silver or platinum fine-tuning data reduces all reported metrics; removing platinum data has the larger reported drop in ROUGE-L (0.1779 versus 0.1905 without silver data) (Table 2, p. 3).

## Evidence caveat

The metrics assess textual similarity and BERTScore against held-out student questions. They do not directly establish that teachers save preparation time or that students learn more.
