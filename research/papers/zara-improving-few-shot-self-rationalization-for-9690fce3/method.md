# Method

## Paper claim

ZARA improves small-model self-rationalization through self-training. It maps an input, generated rationale, and predicted answer to an NLI premise/hypothesis pair; an ensemble of off-the-shelf NLI models selects plausible rationale-answer pairs for pseudo-label augmentation (pp. 2, 5).

## Builder interpretation

The approach uses plausibility as a selection signal, not proof of truth. It is an efficient filter for small models but inherits NLI-mapping errors.

## Unresolved question

Can a common mapping schema evaluate explanation plausibility across tasks without manual task-specific design?
