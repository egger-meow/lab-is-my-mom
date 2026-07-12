# Method

## Paper claim

RSVP uses agent responses during pre-training, then fine-tunes on customer intent labels. Its two self-supervised objectives are response retrieval from a candidate batch and response generation that mimics an agent answer; a contrastive loss is added during intent fine-tuning (pp. 1-3).

## Builder interpretation

The approach treats agent replies as lower-cost latent supervision: a useful reply implies that the agent understood the customer's intent, even though the reply is unavailable at live inference time.

## Unresolved question

How robust is the learned association when historical agent responses are incorrect, templated, or policy-driven rather than intent-specific?
