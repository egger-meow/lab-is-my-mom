# Method

## Paper claim

E-QGen takes a lecture abstract and produces potential student questions so that an instructor can prepare answers or resources ahead of time (p. 1). It has two generators:

1. A student-question generator, LoRA-tuned in a multitask setup.
2. A reference-question generator for broader conceptual questions (p. 3).

The student generator uses actual timestamp-aligned questions (gold), probabilistically aligned questions (silver), and GPT-4-generated questions (platinum). The paper reports 356 gold pairs, 4,434 silver pairs, and 4,829 platinum pairs after transcript segmentation and alignment (p. 2).

## Builder interpretation

The system separates two useful pedagogical functions: mimic likely student confusion and cover general concepts. That separation is more actionable for an instructor than a single generic question list.

## Unresolved question

Does similarity to historical YouTube-comment questions predict usefulness for students in a live, different course?
