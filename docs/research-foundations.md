# Research-informed design

This document records primary research that informs Avatar's current failure
model and engineering choices. It is not a claim that Avatar reproduces these
systems, datasets, or reported results.

## Perspective-bounded memory

[Staying In Character: Perspective-Bounded Memory for Book-Based Role-Playing
Agents](https://arxiv.org/abs/2606.25632) (Tang et al., 2026 preprint) describes
factual overreach caused by memory that is not filtered to a character's
perspective. Avatar applies the narrower engineering invariant that every new
conversation turn and episode carries a story/chapter knowledge boundary.
Bounded recall admits only episodes created at an equal or earlier boundary;
legacy and unrestricted episodes are excluded.

This is not an implementation of the paper's three-layer scene, semantic, and
personality memory or its iterative inference pipeline.

## Persona consistency and priority

[PersonaForge](https://aclanthology.org/2026.findings-acl.386/) (Tong and Zou,
Findings of ACL 2026) evaluates personality drift in long conversations and a
selective dual-process design. Avatar does not reproduce its psychological
architecture. It uses a simpler explicit priority order: knowledge boundary,
then source evidence, then persona style. Long-dialogue personality consistency
has not yet been benchmarked for Avatar.

## Evidence, abstention, and verification

[GaRAGe](https://aclanthology.org/2025.findings-acl.875/) (Sorodoc et al.,
Findings of ACL 2025) evaluates whether RAG answers use relevant passages and
deflect when evidence is insufficient. Avatar therefore preserves an empty
retrieval result instead of presenting the first chunks of a book as if they
were relevant. The `/sources` command exposes the last bounded retrieval trace.

[Generate but Verify](https://aclanthology.org/2025.ijcnlp-long.56/) (Filice et
al., IJCNLP-AACL 2025) motivates an explicit verification and fallback stage.
For bounded conversations, Avatar checks a draft for names first introduced
after the boundary. It attempts one constrained repair and otherwise returns a
deterministic uncertainty response. This guard covers tagged entity names, not
all possible paraphrases or future facts.

## Cross-language retrieval

[XRAG](https://aclanthology.org/2025.findings-emnlp.849/) (Liu et al., Findings
of EMNLP 2025) and [Breaking Language Preference in Multilingual
RAG](https://aclanthology.org/2026.findings-acl.374/) (Huo et al., Findings of
ACL 2026) document failures when query and evidence languages differ. Avatar
keeps its small local lexical index, but when a non-ASCII query has no match it
can ask the configured generation backend for a short query in the source
language and rerun the same boundary-constrained search.

Query rewriting is a retrieval aid, not evidence. The original source excerpts
remain the only retrieved story evidence, and `/sources` shows when rewriting
was used.

## Deliberate non-goals

- No benchmark scores from the cited work are attributed to Avatar.
- No knowledge graph, embedding model, or model fine-tuning is bundled.
- No LLM-as-a-judge result is used as a deterministic CI gate.
- Timeline controls and the entity guard reduce common leaks but are not an
  access-control or formal non-disclosure guarantee.
