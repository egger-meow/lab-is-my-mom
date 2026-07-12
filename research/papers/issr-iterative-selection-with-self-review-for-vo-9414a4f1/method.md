# Method

## Paper claim

ISSR generates vocabulary-test distractors in three stages: a candidate generator, an LLM distractor selector, and a distractor validator (pp. 13–16). The candidate generator is CDGP-CSG, a BERT-based model trained for distractor generation; rule filters remove unsuitable candidates (p. 14).

The validator is an LLM self-review step: it turns a target word and one proposed distractor into a binary-choice question. If the distractor can be selected as correct, it is rejected because the item would have multiple valid answers (p. 16).

## Builder interpretation

The key design move is to use an LLM primarily for constrained selection and validation, not unconstrained bulk generation. It treats invalid test items as a quality-control problem.

## Unresolved question

Does an LLM validator reliably catch semantic ambiguity for the students who will actually take the exam?
