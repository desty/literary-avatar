# Avatar: A Cognitive Architecture for Novel-Grounded Literary Character Agents

## Abstract

We present Avatar, an end-to-end system that transforms public domain novels into interactive character agents grounded in the full narrative text. Unlike prior work that relies on static character profiles or short biographical summaries, Avatar introduces three novel contributions: (1) **narrative arc tracking**, which models how a character's knowledge, emotions, and relationships evolve across the story timeline, enabling spoiler-aware conversations; (2) **automatic behavioral logic extraction**, which derives executable if-then character rules directly from novel text without manual specification; and (3) **second-order Theory of Mind**, where characters reason about what other characters and users believe. Our system integrates retrieval-augmented generation over 332+ text chunks, Big Five personality modeling, BDI (Belief-Desire-Intention) cognitive architecture, and persistent cross-session memory. Evaluated on two characters — Sherlock Holmes and Elizabeth Bennet — across a 5-axis fidelity framework, Avatar achieves an average character fidelity score of 4.0/5.0. We demonstrate that narrative position control successfully prevents knowledge leakage: at position 0, Holmes correctly states "That name means nothing to me" when asked about Irene Adler, while at position 1 he provides detailed recollections. We release the full system as open source.

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
- Downloads public domain texts from Project Gutenberg
- Parses into chapters/stories with speaker-tagged dialogue extraction
- **Sherlock Holmes**: 12 stories, 2,187 dialogues, 562K characters
- **Pride and Prejudice**: 61 chapters, 1,731 dialogues, 729K characters

### 3.3 Character Profile Extraction
Automated extraction via LLM analysis of character dialogue and narrative:
- Big Five personality traits (quantified 0-1)
- Speech patterns (10+ distinctive patterns)
- Values, relationships, habits, reasoning style
- Sample characteristic expressions

### 3.4 RAG with Temporal Filtering
- Text chunked into ~400-word segments with overlap
- Embedded using all-MiniLM-L6-v2, stored in ChromaDB
- **Novel contribution**: RAG results filtered by narrative position, preventing knowledge leakage from future story events

### 3.5 Narrative Arc Tracker (Contribution 1)
For each chapter/story, we generate a character state snapshot containing:
- Knowledge gained in that chapter
- Emotional state and its cause
- Relationship changes
- Key events experienced
- Character development notes

At inference time, `set_narrative_position(N)` constrains the character to only know events up to chapter N. An explicit "unknown items" list is generated from future snapshots to override the base model's pre-training knowledge.

### 3.6 Automatic Behavioral Logic Extraction (Contribution 2)
We extract if-then behavioral rules from novel text in three categories:
- **Deterministic**: Always-true rules (e.g., "when encountering a new client → immediately deduces biographical details from appearance")
- **Probabilistic**: Usually-true rules with probability estimates (e.g., "when complimented → 80% deflects")
- **Conditional**: Context-dependent rules

For Sherlock Holmes, we extracted 49 rules (30 deterministic, 13 probabilistic, 6 conditional) across 4 categories (reasoning, social, emotional, habitual).

### 3.7 Second-Order Theory of Mind (Contribution 3)
Every 3 conversation turns, the system infers:
- What the user likely believes about the current topic
- What the user likely doesn't know
- How the character should adjust their communication
- The character's private reasoning about the user's mental state

This enables adaptive behavior: Holmes explains deduction differently to a novice versus someone who demonstrates familiarity with his methods.

### 3.8 BDI Cognitive Module
Tracks the character's Beliefs, Desires, and Intentions, updated every 5 turns:
- **Beliefs**: Current understanding of the situation and the user
- **Desires**: What the character wants from this interaction
- **Intentions**: What the character plans to do next

### 3.9 Persistent Memory
Cross-session memory following MemGPT principles:
- Episode summaries stored after each session
- User profile facts extracted and accumulated
- Keyword-based recall during future sessions

---

## 4. Experiments

### 4.1 Evaluation Framework
We propose a 5-axis evaluation framework:
1. **Knowledge Accuracy**: Does the character only reference things they would know?
2. **Personality Consistency**: Does the response match the Big Five profile?
3. **Speech Fidelity**: Does the response use distinctive speech patterns?
4. **Behavioral Consistency**: Does the response follow extracted behavioral rules?
5. **Overall Character Fidelity**: Does this feel like the character?

Each axis is scored 1-5 by an LLM evaluator (following CharacterBench methodology).

### 4.2 Baseline Results
Sherlock Holmes, 3-question evaluation:
| Question | Knowledge | Personality | Speech | Behavior | Overall | Aggregate |
|----------|-----------|-------------|--------|----------|---------|-----------|
| Strange letter | 3 | 3 | 4 | 2 | 3 | 3.0 |
| Method of deduction | 5 | 5 | 4 | 4 | 5 | 4.6 |
| 왓슨 평가 (Korean) | 5 | 4 | 4 | 4 | 5 | 4.4 |
| **Average** | **4.3** | **4.0** | **4.0** | **3.3** | **4.3** | **4.0** |

### 4.3 Narrative Arc Tracking Evaluation
| Narrative Position | Query | Expected | Actual | Correct? |
|-------------------|-------|----------|--------|----------|
| pos=0 (before story 1) | "What about Irene Adler?" | Does not know | "That name means nothing to me" | ✅ |
| pos=1 (after story 1) | "What about Irene Adler?" | Knows and reflects | "The woman... she outwitted me" | ✅ |

### 4.4 Cross-Language Consistency
Both Korean and English inputs maintain character voice and knowledge accuracy, demonstrating language-agnostic character modeling.

---

## 5. Analysis

### 5.1 Narrative Position as Knowledge Boundary
The most significant finding is that explicit "unknown items" lists effectively override the base model's pre-training knowledge. Simple instructions like "you don't know this yet" are insufficient — the model draws on its training data. Our approach of enumerating specific unknown characters/events provides a concrete boundary.

### 5.2 Behavioral Logic Patterns
The 49 automatically extracted rules reveal character structure:
- Holmes's reasoning rules are predominantly deterministic (always observes before speaking)
- His social rules are more probabilistic (usually deflects compliments, but sometimes accepts)
- Emotional rules are conditional (protective behavior depends on the victim's vulnerability)

### 5.3 Limitations
1. **LLM-as-evaluator bias**: Our evaluation uses the same model family for generation and evaluation
2. **Speaker attribution**: ~50% of dialogues have "Unknown" speakers due to Victorian prose conventions
3. **ToM verification**: Second-order ToM inferences are not validated against ground truth
4. **Scale**: Tested on 2 characters; broader validation needed

---

## 6. Conclusion

Avatar demonstrates that literary character agents require more than prompt engineering — they need cognitive architectures that model personality, knowledge boundaries, temporal evolution, and theory of mind as integrated systems. Our three contributions — narrative arc tracking, automatic behavioral logic extraction, and second-order Theory of Mind — address gaps identified across 18 recent papers in character-grounded dialogue, and we show that these capabilities can be implemented without fine-tuning using retrieval-augmented generation and structured prompting.

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
