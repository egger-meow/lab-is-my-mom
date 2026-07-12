# Method

## Paper claim

ParaAlign Translator first creates source-language paraphrases that better match target-language structure, then LoRA-fine-tunes LLaMA-3-8B on original translation pairs and target-to-paraphrased-source pairs (pp. 1–2). It uses prompts for direct translation, translation fine-tuning, and paraphrasing (Table 1, p. 2).

The paper uses LLaMA-3-8B to generate paraphrased aligned pairs and sets LoRA rank to 128 in the reported experiments (pp. 2–3).

## Builder interpretation

The method moves some cross-lingual structural work into a controlled source-side rewrite, making translation easier for a smaller downstream model.

## Unresolved question

When does paraphrasing preserve meaning versus introduce an error that translation metrics may not expose?
