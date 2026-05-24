# Avatar — Literary Character AI Agent

A cognitive architecture that transforms public domain novels into interactive character agents. Characters maintain personality, knowledge boundaries, and emotional states grounded in the full narrative text.

> **Paper**: [Avatar: A Cognitive Architecture for Novel-Grounded Literary Character Agents](docs/paper-draft.md)

## Novel Contributions

Three research-grade contributions not found in existing literature:

1. **Narrative Arc Tracking** — Characters evolve across the story timeline. Set `/timeline 0` and Holmes says "Irene Adler? That name means nothing to me." Set `/timeline 1` and he recalls "The woman... she outwitted me."

2. **Automatic Behavioral Logic Extraction** — 49 if-then character rules automatically extracted from novel text (30 deterministic, 13 probabilistic, 6 conditional). No manual specification needed.

3. **Second-Order Theory of Mind** — Characters reason about what users believe, adjusting explanations to the user's knowledge level.

## Quick Start

### Prerequisites

- Python 3.9+
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) installed and authenticated

### Installation

```bash
git clone https://github.com/YOUR_USERNAME/avatar.git
cd avatar
pip install -r requirements.txt
```

### First Run: Download & Process Novels

```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from src.ingestion.downloader import download_text
from src.ingestion.parser import parse_novel, save_parsed_novel
from src.ingestion.profile_extractor import extract_and_save
from src.memory.retriever import build_index

# Sherlock Holmes
path = download_text('sherlock_holmes')
novel = parse_novel('sherlock_holmes', path.read_text(encoding='utf-8'))
save_parsed_novel(novel)
build_index('sherlock_holmes')
extract_and_save('sherlock_holmes')

# Pride and Prejudice
path = download_text('pride_and_prejudice')
novel = parse_novel('pride_and_prejudice', path.read_text(encoding='utf-8'))
save_parsed_novel(novel)
build_index('pride_and_prejudice')
extract_and_save('elizabeth_bennet')
"
```

### Start Conversation

```bash
python3 -m src.main
```

### Run Demo Showcase

```bash
python3 demo.py
```

### Run Web UI (Streamlit)

```bash
streamlit run app.py
```

## Characters

| Character | Novel | Author | Year | Data |
|-----------|-------|--------|------|------|
| **Sherlock Holmes** | The Adventures of Sherlock Holmes | Arthur Conan Doyle | 1892 | 12 stories, 2,187 dialogues |
| **Elizabeth Bennet** | Pride and Prejudice | Jane Austen | 1813 | 61 chapters, 1,731 dialogues |

## CLI Commands

```
/switch    — Switch between characters
/timeline  — Set narrative position (spoiler control)
/memory    — View past session memories
/bdi       — View character's Belief-Desire-Intention state
/reset     — Reset conversation (saves memories)
/quit      — Exit (saves memories)
```

## Architecture

```
Novel Text → Ingestion Pipeline → Structured Data
                                       ↓
                              Character Profile (Big Five, Speech, Values)
                                       ↓
              ┌─────────────────── Cognitive Engine ──────────────────┐
              │                                                       │
    RAG Retriever ──── Arc Tracker ──── Logic Rules ──── ToM Module   │
    (ChromaDB)    (Timeline Filter)  (49 auto rules)  (User Model)    │
              │                                                       │
              │   BDI Module ──── Persistent Memory ──── Conv Memory  │
              └───────────────────────┬──────────────────────────────┘
                                      ↓
                              Character Response
```

## Tech Stack

- **LLM Backend**: Claude Code CLI (`claude -p`) — zero API cost
- **Language**: Python 3.9+
- **Vector DB**: ChromaDB (all-MiniLM-L6-v2)
- **Terminal UI**: Rich
- **Web UI**: Streamlit

## Evaluation

5-axis character fidelity framework (avg 4.0/5.0):

| Axis | Score |
|------|-------|
| Knowledge Accuracy | 4.3/5.0 |
| Personality Consistency | 4.0/5.0 |
| Speech Fidelity | 4.0/5.0 |
| Behavioral Consistency | 3.3/5.0 |
| Overall Character Fidelity | 4.3/5.0 |

## Project Structure

```
avatar/
├── app.py                         # Streamlit web UI
├── demo.py                        # CLI feature demo
├── requirements.txt
├── LICENSE
├── docs/
│   ├── 01-research.md             # 18 papers surveyed
│   ├── 02-novel-candidates.md     # 14 novel candidates
│   ├── 03-architecture.md         # System architecture
│   ├── 04-mvp-plan.md             # MVP plan
│   ├── 05-future-roadmap.md       # Roadmap (Phase 1-4)
│   ├── 06-progress-and-next.md    # Progress tracker
│   └── paper-draft.md             # Paper draft
├── src/
│   ├── main.py                    # CLI entry point
│   ├── ingestion/
│   │   ├── downloader.py          # Gutenberg download
│   │   ├── parser.py              # Novel parsing
│   │   └── profile_extractor.py   # Character profile extraction
│   ├── character/
│   │   ├── engine.py              # Cognitive engine (core)
│   │   ├── profile.py             # Profile loader
│   │   ├── prompt_builder.py      # System prompt builder
│   │   ├── arc_tracker.py         # Narrative arc tracking
│   │   ├── theory_of_mind.py      # 2nd-order ToM
│   │   └── logic_extractor.py     # Behavioral logic extraction
│   ├── memory/
│   │   ├── conversation.py        # Session memory
│   │   ├── persistent.py          # Cross-session memory
│   │   └── retriever.py           # ChromaDB RAG
│   └── evaluation/
│       └── consistency.py         # 5-axis evaluation
└── data/
    ├── raw/                       # Original novel texts
    ├── processed/                 # Parsed JSON
    ├── profiles/                  # Character profiles
    ├── arcs/                      # Arc snapshots
    ├── logic/                     # Behavioral rules
    └── vectordb/                  # ChromaDB storage
```

## References

Key papers referenced (18 total — see [docs/01-research.md](docs/01-research.md)):

- CoSER (ICML 2025) — Book-derived character data
- RoleLLM (ACL 2024) — Role-playing benchmarks
- MemGPT (2023) — Long-term memory architecture
- CharacterBox (2024) — BDI-based character modeling
- Codified Character Logic (2025) — Executable character rules
- CharacterBench (2024) — Character evaluation
- RoleRAG (2025) — Knowledge boundary RAG

## License

[MIT](LICENSE)
