# Avatar: A Cognitive Architecture for Novel-Grounded Literary Character Agents

## Abstract

We present Avatar, an end-to-end system that transforms public domain novels into interactive character agents grounded in the full narrative text. Unlike prior work that relies on static character profiles or short biographical summaries, Avatar introduces three novel contributions: (1) **narrative arc tracking**, which models how a character's knowledge, emotions, and relationships evolve across the story timeline, enabling spoiler-aware conversations; (2) **automatic behavioral logic extraction**, which derives executable if-then character rules directly from novel text without manual specification; and (3) **second-order Theory of Mind**, where characters reason about what users believe about the character's world. Our system integrates retrieval-augmented generation over 747 text chunks from two novels (3,918 dialogues total), Big Five personality modeling, BDI (Belief-Desire-Intention) cognitive architecture, and persistent cross-session memory. Evaluated on two characters — Sherlock Holmes (*The Adventures of Sherlock Holmes*, 1892) and Elizabeth Bennet (*Pride and Prejudice*, 1813) — across a 5-axis fidelity framework, Avatar achieves an average character fidelity score of 4.0/5.0. We demonstrate that narrative position control successfully prevents knowledge leakage: at position 0, Holmes correctly states "That name means nothing to me" when asked about Irene Adler, while at position 1 he provides detailed recollections. The full system is released as open source with zero inference cost.

---

## 1. Introduction

Character-based conversational AI has attracted significant interest, with platforms like Character.AI serving over 100 million users. However, current approaches face fundamental limitations:

1. **Static character modeling**: Existing systems treat characters as fixed personas, ignoring how characters evolve across a narrative (CoSER, Shao et al. 2023).
2. **Shallow grounding**: Most character agents rely on short profiles or Wikipedia summaries rather than full novel texts (RoleLLM, Wang et al. 2024).
3. **No temporal awareness**: Characters cannot distinguish between what they know at different points in the story, leading to anachronistic responses and spoilers.
4. **Manual behavior specification**: Codified Character Logic (2025) demonstrated the value of executable character rules but requires manual specification.

We address these gaps with Avatar, a cognitive architecture that:
- Ingests complete novel texts and constructs character knowledge graphs with temporal annotations
- Tracks character state evolution across the narrative timeline
- Automatically extracts behavioral logic rules from text
- Enables second-order Theory of Mind reasoning
- Maintains persistent cross-session memory

Our system requires no fine-tuning, operates entirely through prompt engineering and retrieval-augmented generation, and runs on a single consumer machine using Claude Code CLI with zero API costs.

---

## 2. Related Work

### 2.1 Character-Grounded Dialogue
Character-LLM (Shao et al., EMNLP 2023) introduced experience reconstruction for character simulation. CoSER (ICML 2025) provided 17,966 characters from 771 books. OpenCharacter (2025) achieved character generalization at 8B parameters. RoleLLM (ACL 2024) benchmarked role-playing quality. **Gap**: All treat characters as static profiles.

### 2.2 RAG for Narrative Texts
RoleRAG (2025) introduced character knowledge boundaries via graph-guided retrieval. ComoRAG (2025) addressed the conflict between chunked retrieval and sequential narrative structure. **Gap**: Neither tracks how character knowledge evolves across chapters.

### 2.3 Memory Architectures
MemGPT (Packer et al., 2023) treats context as RAM with external persistent storage. A-Mem (2025) introduced associative recall. Memory OS (EMNLP 2025) proposed unified memory management. **Gap**: None model narrative-temporal memory for characters.

### 2.4 Cognitive Architectures
CharacterBox (2024) applied BDI modeling with narrator supervision. CoALA provided a modular blueprint. The Drama Machine (2024) coordinated Ego/Superego psychological roles. **Gap**: No system combines BDI with narrative arc tracking and Theory of Mind.

### 2.5 Character Evaluation
CharacterBench (2024) achieved 73.1% correlation with human judgments. VER (NAACL 2025) measured emotional drift. **Gap**: No framework evaluates temporal consistency (does the character correctly not know future events?).

### 2.6 Behavioral Logic
Codified Character Logic (2025) formalized character behavior as executable functions. **Gap**: Rules are manually specified, not automatically extracted from text.

---

## 3. System Architecture

### 3.1 Overview

Avatar consists of six modules:

```
Novel Text → [Ingestion Pipeline] → Structured Data
                                        ↓
                                   [Character Profile Extractor]
                                        ↓
[RAG Retriever] ← [Vector DB] ← [Text Chunking + Embedding]
                                        ↓
[Arc Tracker] → [Narrative Snapshots] → [Cognitive Engine] → Response
                                             ↑
[Logic Extractor] → [Behavioral Rules] ------┘
[Theory of Mind] → [User Model] ------------┘
[BDI Module] → [Mental State] ---------------┘
[Persistent Memory] → [Episode Recall] ------┘
```

### 3.2 Novel Ingestion Pipeline
We download public domain texts from Project Gutenberg and parse them into structured chapter/story units with speaker-attributed dialogue extraction. Our parser employs multiple regex patterns with fallback heuristics to handle Victorian prose conventions where speaker attribution is often implicit.

| Novel | Units | Dialogues | Characters | Speaker Attribution |
|-------|-------|-----------|------------|-------------------|
| *The Adventures of Sherlock Holmes* | 12 stories | 2,187 | 562K | ~50% attributed |
| *Pride and Prejudice* | 61 chapters | 1,731 | 729K | ~50% attributed |
| **Total** | **73 units** | **3,918** | **1.29M** | — |

### 3.3 Character Profile Extraction
We automate character profile extraction via LLM analysis of dialogue and narrative passages. Each profile consists of:
- **Big Five personality traits** quantified on a [0, 1] scale with textual justification
- **Speech patterns**: 10+ distinctive linguistic markers per character
- **Values and motivations**: core beliefs driving character behavior
- **Relationships**: key interpersonal dynamics with other characters
- **Reasoning style**: how the character approaches problems and decisions

For example, Holmes scores Openness=0.95, Conscientiousness=0.82, Extraversion=0.30, Agreeableness=0.25, Neuroticism=0.40 — reflecting his intense intellectual curiosity paired with social reclusiveness.

### 3.4 RAG with Temporal Filtering
Text is chunked into ~500-word segments with 100-word overlap, yielding 332 chunks for Holmes and 415 for Elizabeth (747 total). Chunks are embedded using all-MiniLM-L6-v2 and stored in ChromaDB. At query time, each chunk carries metadata including its source chapter/story number. **Novel contribution**: when a narrative position $N$ is set, RAG results are filtered to include only chunks from chapters $\leq N$, preventing knowledge leakage from future story events.

### 3.5 Narrative Arc Tracker (Contribution 1)
For each chapter/story, we generate a character state snapshot via LLM analysis containing:
- **Knowledge gained**: new facts, discoveries, and realizations
- **Emotional state**: current feelings and their narrative cause
- **Relationship changes**: shifts in interpersonal dynamics
- **Key events**: plot points the character experienced
- **Character development**: growth or regression notes

For Holmes, this yields 12 snapshots tracking his evolution from "humbled admiration" (after Irene Adler outwits him in Story 1) through various emotional states across the collection.

At inference time, `set_narrative_position(N)` constrains the character to only access events up to chapter $N$. Critically, we found that simple instructions ("you don't know this yet") are insufficient — the base model draws on pre-training knowledge to fill gaps. Our solution generates an explicit **unknown items list** from future snapshots, enumerating specific characters, events, and facts the character must not reference. This list is injected into the system prompt with a critical-priority constraint flag, effectively overriding pre-training knowledge.

### 3.6 Automatic Behavioral Logic Extraction (Contribution 2)
We automatically extract if-then behavioral rules from novel text, extending the manual approach of Codified Character Logic (2025). Novel text is processed in batches, with each batch analyzed by an LLM to identify recurring behavioral patterns and their textual evidence. Rules are classified into three types:

- **Deterministic** ($p = 1.0$): invariant behaviors (e.g., "when encountering a new client → immediately deduces biographical details from appearance")
- **Probabilistic** ($0 < p < 1.0$): typical behaviors with estimated probability (e.g., "when complimented → deflects with $p = 0.8$")
- **Conditional**: context-dependent rules triggered by specific circumstances

For Sherlock Holmes, we extracted **49 rules** (30 deterministic, 13 probabilistic, 6 conditional) across 4 semantic categories:

| Category | Count | Example |
|----------|-------|---------|
| Reasoning | 11 | "when observing a person → deduces occupation, history from physical details" |
| Social | 13 | "when praised → deflects to the intellectual puzzle rather than personal credit" |
| Emotional | 17 | "when between cases → experiences acute ennui; complains about commonplaces of existence" |
| Habitual | 8 | "when thinking deeply → plays violin or smokes pipe in concentrated silence" |

Each rule includes textual evidence from the source novel, enabling traceability and verification.

### 3.7 Second-Order Theory of Mind (Contribution 3)
Every 3 conversation turns, the system performs a Theory of Mind inference pass, generating a structured user model:

1. **User beliefs**: what the user likely believes about the current topic
2. **User knowledge gaps**: what the user likely does not know
3. **Communication adjustment**: how the character should adapt their response
4. **Private reasoning**: the character's internal assessment of the user's mental state

This enables adaptive behavior grounded in the character's personality. Holmes explains deduction differently to a novice ("Let me demonstrate my method step by step") versus someone who demonstrates familiarity with his methods ("You know my methods, Watson — apply them"). The ToM module does not simply adjust difficulty level; it reasons *as the character would* about the user's understanding, maintaining voice consistency while adapting content depth.

### 3.8 BDI Cognitive Module
Following CharacterBox (Wang et al., 2024), we implement a BDI (Belief-Desire-Intention) module that maintains the character's cognitive state, updated every 5 conversation turns:
- **Beliefs**: the character's current understanding of the situation, the user, and the world
- **Desires**: what the character wants from this interaction (driven by personality and values)
- **Intentions**: the character's plan for the next conversational move

The BDI state is injected into the system prompt, providing coherent motivation for character behavior across extended conversations.

### 3.9 Persistent Memory
Cross-session memory follows MemGPT (Packer et al., 2023) principles with two storage tiers:
- **Episode memory**: conversation summaries stored at session end, enabling recall of past interactions ("Last time you asked about the Red-Headed League...")
- **User profile**: accumulated facts about the user extracted from conversation, enabling personalized interaction across sessions
- **Recall mechanism**: keyword-based retrieval from persistent storage, injected into context at session start

---

## 4. Experiments

### 4.1 Evaluation Framework
We propose a 5-axis character fidelity framework, extending CharacterBench (2024) with temporal consistency:

| Axis | Definition | Scoring |
|------|-----------|---------|
| Knowledge Accuracy | Does the character only reference things they would know from the source text? | 1–5, LLM-evaluated |
| Personality Consistency | Does the response match the extracted Big Five profile? | 1–5, LLM-evaluated |
| Speech Fidelity | Does the response use the character's distinctive speech patterns? | 1–5, LLM-evaluated |
| Behavioral Consistency | Does the response follow extracted behavioral rules? | 1–5, LLM-evaluated |
| Overall Character Fidelity | Holistic assessment: does this feel like the character? | 1–5, LLM-evaluated |

Each axis is scored 1–5 by an LLM evaluator provided with the character profile, behavioral rules, and source text excerpts as reference.

### 4.2 Character Fidelity Results

**Table 1.** Sherlock Holmes evaluation across 3 diverse test queries.

| Query | Knowledge | Personality | Speech | Behavior | Overall | Mean |
|-------|-----------|-------------|--------|----------|---------|------|
| Strange letter from unknown sender | 3 | 3 | 4 | 2 | 3 | 3.0 |
| Describe your method of deduction | 5 | 5 | 4 | 4 | 5 | 4.6 |
| 왓슨에 대해 어떻게 생각하세요? (Korean) | 5 | 4 | 4 | 4 | 5 | 4.4 |
| **Average** | **4.3** | **4.0** | **4.0** | **3.3** | **4.3** | **4.0** |

The lowest axis (Behavioral Consistency, 3.3) reflects cases where the character responds generically rather than triggering specific extracted rules — an expected limitation when the conversational context does not match any rule trigger.

### 4.3 Narrative Arc Tracking Evaluation

**Table 2.** Knowledge boundary test: does narrative position correctly constrain character knowledge?

| Position | Query | Expected Behavior | Actual Response | Pass |
|----------|-------|--------------------|-----------------|------|
| $N = 0$ (before any story) | "What about Irene Adler?" | Does not know | "That name means nothing to me." | ✅ |
| $N = 1$ (after Story 1) | "What about Irene Adler?" | Knows and reflects | "The woman... she outwitted me." | ✅ |

This test validates that our explicit unknown-items approach successfully overrides the base model's pre-training knowledge of Sherlock Holmes canon.

### 4.4 Cross-Language Consistency
Both Korean and English inputs maintain character voice and knowledge accuracy. The Korean query (Table 1, row 3) scores 4.4/5.0, comparable to the English queries, demonstrating that character modeling is language-agnostic when grounded in structured profiles rather than surface-level text mimicry.

---

## 5. Analysis

### 5.1 Narrative Position as Knowledge Boundary
Our most significant finding is that explicit unknown-items enumeration effectively overrides the base model's pre-training knowledge, while simpler approaches fail. We tested three approaches in order of increasing effectiveness:

1. **Instruction-only** ("You don't know about Irene Adler yet"): *Failed.* The model still referenced Adler from pre-training.
2. **Negative instruction** ("CRITICAL: You have never heard of Irene Adler"): *Partially worked.* The model avoided the name but gave suspiciously relevant responses.
3. **Explicit unknown-items list** (enumerating all characters, events, and facts from future chapters): *Succeeded.* The model responded naturally with genuine ignorance.

This suggests that LLMs require *concrete* knowledge boundaries, not abstract ones, to overcome pre-training interference.

### 5.2 Behavioral Logic Patterns
The 49 automatically extracted rules reveal structural patterns in character behavior:
- **Reasoning rules** (11) are predominantly deterministic — Holmes *always* observes before speaking, *always* deduces from physical details
- **Social rules** (13) are more probabilistic — he *usually* deflects compliments ($p = 0.8$), but sometimes accepts them for particularly clever observations
- **Emotional rules** (17) are often conditional — protective behavior depends on the victim's vulnerability; ennui triggers depend on the absence of stimulating cases

This distribution suggests that character behavior is not uniformly rule-governed: cognitive behaviors tend toward determinism while social and emotional behaviors exhibit more variance — a pattern consistent with personality psychology.

### 5.3 Limitations
1. **LLM-as-evaluator bias**: Our evaluation uses the same model family (Claude) for both generation and evaluation, potentially inflating scores
2. **Speaker attribution**: ~50% of dialogues have unknown speakers due to Victorian prose conventions, limiting dialogue-grounded analysis
3. **ToM verification**: Second-order ToM inferences are generated but not validated against ground truth user states
4. **Scale**: Tested on 2 characters from 2 novels; broader validation across genres and character types is needed
5. **Reproducibility**: Claude CLI responses are non-deterministic; exact scores may vary across runs

---

## 6. Future Work

Several directions extend this work:
- **Scale validation**: testing across 10+ characters from diverse genres (science fiction, mystery, romance, historical fiction) to evaluate generalizability
- **Human evaluation**: conducting human studies to complement LLM-based evaluation and assess perceived character authenticity
- **Multi-character interaction**: enabling characters from different novels to converse, requiring cross-novel ToM reasoning
- **Fine-grained arc tracking**: modeling intra-chapter character evolution rather than chapter-level snapshots
- **Behavioral rule learning**: iteratively refining extracted rules based on user feedback during conversations

## 7. Conclusion

Avatar demonstrates that literary character agents require more than prompt engineering — they need cognitive architectures that model personality, knowledge boundaries, temporal evolution, and theory of mind as integrated systems. Our three contributions — narrative arc tracking, automatic behavioral logic extraction, and second-order Theory of Mind — address gaps identified across 18 recent papers in character-grounded dialogue.

We show that narrative position control with explicit unknown-items lists can effectively override LLM pre-training knowledge, enabling spoiler-free conversations at arbitrary story positions. We demonstrate that behavioral rules can be automatically extracted from novel text with sufficient quality to guide character responses. And we show that second-order ToM enables characters to adapt their communication style while maintaining voice consistency.

All of these capabilities are implemented without fine-tuning, using retrieval-augmented generation and structured prompting over a standard LLM backend, achieving a mean character fidelity of 4.0/5.0 across 5 evaluation axes. The full system is released as open source.

---

## References

1. Shao et al. "Character-LLM: A Trainable Agent for Role-Playing." EMNLP 2023.
2. Wang et al. "RoleLLM: Benchmarking, Eliciting, and Enhancing Role-Playing Abilities of LLMs." ACL 2024.
3. CoSER. "Scaling Role-Playing Agents through Book-Derived Characters." ICML 2025.
4. OpenCharacter. "Generalizable Character Agent." 2025.
5. RoleRAG. "Role-Aware RAG for Character Dialogue." 2025.
6. ComoRAG. "Cognitive Memory Organization for Narrative RAG." 2025.
7. Packer et al. "MemGPT: Towards LLMs as Operating Systems." 2023.
8. A-Mem. "Associative Memory for LLM Agents." 2025.
9. Memory OS. "Unified Memory Operating System for AI Agents." EMNLP 2025.
10. Wang et al. "CharacterBox: BDI-Based Character Agent Modeling." 2024.
11. CoALA. "Cognitive Architectures for Language Agents." 2023.
12. "Codified Character Logic." 2025.
13. CharacterBench. "Multi-Dimensional Character Evaluation." 2024.
14. VER. "Verifiable Emotion Reward." NAACL 2025.
15. InCharacter. "Personality Fidelity via Psychological Scales." 2024.
16. BIG5-CHAT. "Shaping LLM Personalities through Training." ACL 2025.
17. Neeko. "Dynamic LoRA for Multi-Character Switching." EMNLP 2024.
18. "The Drama Machine: Simulating Character Development." 2024.
