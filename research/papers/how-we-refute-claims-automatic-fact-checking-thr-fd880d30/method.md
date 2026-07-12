# Method

## Paper claim

RefuteClaim frames automatic fact-checking as flaw-oriented: retrieve evidence, generate up to four evaluation aspects, identify flaws, then generate a justification (pp. 2–3). The paper groups seven flaws into explicit compatibility flaws, nuanced support/robustness flaws, and more context-heavy assumption/alternative-explanation flaws (p. 1).

The authors construct FlawCheck by extending WatClaimCheck review material and use GPT-3.5-turbo to distill expert review content into aspects and flaw labels (p. 2).

## Builder interpretation

Aspects function as an explicit reasoning agenda between retrieval and explanation. This can make a fact-checking output easier to inspect, but its faithfulness depends on the quality of the silver labels and retrieved evidence.

## Unresolved question

Can the framework distinguish a truly unsupported claim from one where relevant evidence was simply not retrieved?
