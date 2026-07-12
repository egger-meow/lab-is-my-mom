# Method

## Paper claim

SEEN compares a pre-retold and post-retold life narrative to identify consistent, inconsistent, additional, forgotten, or unforgotten events. It constructs a coreference-aware event graph, encodes it with graph attention, fuses it with a Longformer textual encoder, and selects related nodes as support evidence (pp. 1-5).

## Builder interpretation

The graph is both a performance feature and an explanation interface: selected nodes can remind a user why the system thinks a memory is confused or incomplete.

## Unresolved question

Can the approach work without the gold event graph used in the current experiments?
