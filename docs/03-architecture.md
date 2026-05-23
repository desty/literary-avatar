# 아키텍처 설계: Character Avatar Agent

> 작성일: 2026-05-23

## 1. 시스템 개요

```
┌─────────────────────────────────────────────────────────────────┐
│                    Character Avatar System                       │
│                                                                   │
│  ┌──────────────┐    ┌──────────────────┐    ┌───────────────┐  │
│  │  Novel        │    │  Character        │    │  Conversation  │  │
│  │  Ingestion    │───▶│  Cognitive        │───▶│  Interface     │  │
│  │  Pipeline     │    │  Engine           │    │  (CLI/Web)     │  │
│  └──────────────┘    └──────────────────┘    └───────────────┘  │
│         │                     │                       │          │
│         ▼                     ▼                       ▼          │
│  ┌──────────────┐    ┌──────────────────┐    ┌───────────────┐  │
│  │  Character    │    │  Memory           │    │  Evaluation    │  │
│  │  Knowledge    │    │  System           │    │  Framework     │  │
│  │  Graph        │    │  (Episodic+       │    │                │  │
│  │              │    │   Semantic)        │    │                │  │
│  └──────────────┘    └──────────────────┘    └───────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 2. 기술 스택

| 레이어 | 기술 | 이유 |
|--------|------|------|
| **LLM 백엔드** | Claude Code CLI (`claude -p`) | API 키 불필요, 로컬 CLI 활용 |
| **언어** | Python 3.11+ | 에코시스템, 라이브러리 풍부 |
| **벡터 DB** | ChromaDB (로컬) | 설치 간단, 임베딩 저장 |
| **텍스트 파싱** | BeautifulSoup + 커스텀 파서 | Gutenberg 텍스트 파싱 |
| **임베딩** | sentence-transformers | 로컬 임베딩 생성 |
| **지식 그래프** | NetworkX + JSON | 경량, 빠른 프로토타이핑 |
| **UI** | CLI (1차) → Streamlit (2차) | 점진적 확장 |

### Claude CLI 활용 방식

```python
import subprocess
import json

def ask_claude(prompt: str, system: str = "") -> str:
    """Claude Code CLI를 LLM 백엔드로 사용"""
    cmd = ["claude", "-p", prompt]
    if system:
        cmd.extend(["--system", system])
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=120
    )
    return result.stdout.strip()
```

> **장점**: API 키/과금 없이 Claude 활용 가능
> **제약**: 속도가 API 직접 호출보다 느릴 수 있음, 동시 호출 제한

---

## 3. 모듈 상세 설계

### 3.1 Novel Ingestion Pipeline

소설 원문을 구조화된 데이터로 변환하는 파이프라인.

```
[Gutenberg 원문 다운로드]
    │
    ▼
[텍스트 전처리] ─── 머리말/꼬리말 제거, 챕터 분리
    │
    ▼
[챕터별 분석] ─── Claude를 사용하여 각 챕터에서 추출:
    │              ├── 등장인물
    │              ├── 사건/장면
    │              ├── 대화 (발화자 태깅)
    │              ├── 캐릭터별 지식 상태 변화
    │              └── 감정 상태 변화
    │
    ▼
[Character Knowledge Graph 구축]
    │
    ▼
[Character Profile 생성] ─── 성격, 말투, 가치관, 관계
```

#### 데이터 구조

```python
@dataclass
class Chapter:
    number: int
    title: str
    text: str
    scenes: list[Scene]

@dataclass
class Scene:
    chapter: int
    summary: str
    characters_present: list[str]
    dialogues: list[Dialogue]
    events: list[Event]
    knowledge_updates: dict[str, list[str]]  # character -> new knowledge

@dataclass
class Dialogue:
    speaker: str
    text: str
    tone: str
    context: str

@dataclass
class CharacterProfile:
    name: str
    big_five: dict[str, float]  # openness, conscientiousness, etc.
    speech_patterns: list[str]
    values: list[str]
    relationships: dict[str, str]  # character -> relationship type
    knowledge_at_chapter: dict[int, list[str]]
    emotional_arc: list[dict]
```

### 3.2 Character Cognitive Engine

캐릭터의 "두뇌" 역할. 대화 시 캐릭터답게 응답하는 핵심 모듈.

```
┌─────────────────────────────────────────┐
│         Character Cognitive Engine        │
│                                           │
│  ┌─────────────┐    ┌─────────────────┐  │
│  │ Personality  │    │ Knowledge       │  │
│  │ Model        │    │ Boundary        │  │
│  │ (Big Five)   │    │ Manager         │  │
│  └──────┬──────┘    └────────┬────────┘  │
│         │                     │           │
│         ▼                     ▼           │
│  ┌──────────────────────────────────────┐ │
│  │        Response Generator            │ │
│  │  ┌──────┐  ┌──────┐  ┌──────────┐   │ │
│  │  │ BDI  │  │ Tone │  │ Knowledge │   │ │
│  │  │Module│  │Filter│  │ Check     │   │ │
│  │  └──────┘  └──────┘  └──────────┘   │ │
│  └──────────────────────────────────────┘ │
│         │                                 │
│         ▼                                 │
│  ┌─────────────┐    ┌─────────────────┐  │
│  │ Consistency │    │ Emotional       │  │
│  │ Validator   │    │ State Tracker   │  │
│  └─────────────┘    └─────────────────┘  │
└─────────────────────────────────────────┘
```

#### 응답 생성 플로우

1. **사용자 입력 수신**
2. **의도 분석** — 사용자가 무엇을 원하는가?
3. **지식 경계 확인** — 이 캐릭터가 알 수 있는 정보인가?
4. **관련 컨텍스트 검색** (RAG) — 소설에서 관련 장면/대화 검색
5. **BDI 추론** — 캐릭터의 현재 믿음/욕구/의도에 기반한 반응 결정
6. **응답 생성** — 캐릭터의 말투, 성격, 감정 상태를 반영
7. **일관성 검증** — 이전 대화와 모순되지 않는지 확인
8. **메모리 업데이트** — 새로운 대화 내용을 에피소드 메모리에 저장

#### 시스템 프롬프트 구조

```python
SYSTEM_PROMPT_TEMPLATE = """
You are {character_name} from "{novel_title}" by {author}.

## Your Identity
{character_profile}

## Your Personality (Big Five)
{big_five_description}

## Your Speech Patterns
{speech_patterns}

## Your Current Knowledge
You know only what {character_name} would know:
{knowledge_boundary}

## Your Relationships
{relationships}

## Your Current Emotional State
{emotional_state}

## Behavioral Rules
{behavioral_rules}

## Relevant Context from the Novel
{rag_context}

## Conversation History
{conversation_history}

## Instructions
- Respond as {character_name} would, maintaining consistent personality
- Use {character_name}'s distinctive speech patterns and vocabulary
- Do not break character or acknowledge being an AI
- If asked about something {character_name} wouldn't know, respond as the character would to unfamiliar topics
- Show {character_name}'s reasoning process when appropriate
"""
```

### 3.3 Memory System

MemGPT 영감의 2-tier 메모리 시스템.

```
┌─────────────────────────────────┐
│          Memory System           │
│                                   │
│  ┌─────────────────────────────┐ │
│  │     Working Memory          │ │
│  │  (Current conversation      │ │
│  │   context window)           │ │
│  └──────────┬──────────────────┘ │
│             │                     │
│  ┌──────────▼──────────────────┐ │
│  │     Episodic Memory         │ │
│  │  (Past conversations,       │ │
│  │   user interactions)        │ │
│  │  Storage: ChromaDB          │ │
│  └──────────┬──────────────────┘ │
│             │                     │
│  ┌──────────▼──────────────────┐ │
│  │     Semantic Memory         │ │
│  │  (Character knowledge,      │ │
│  │   novel facts, profiles)    │ │
│  │  Storage: JSON + ChromaDB   │ │
│  └─────────────────────────────┘ │
└─────────────────────────────────┘
```

### 3.4 Evaluation Framework

```python
class CharacterEvaluator:
    """다축 캐릭터 충실도 평가"""
    
    def evaluate_knowledge_accuracy(self, response, character) -> float:
        """캐릭터가 아는 것만 알고 있는가?"""
        
    def evaluate_personality_consistency(self, responses, big_five) -> float:
        """Big Five 성격 특성이 일관적인가?"""
        
    def evaluate_speech_fidelity(self, response, speech_patterns) -> float:
        """캐릭터의 말투를 유지하는가?"""
        
    def evaluate_emotional_coherence(self, response, emotional_context) -> float:
        """감정 반응이 상황에 적절한가?"""
```

---

## 4. 핵심 차별화 요소

### 4.1 챕터별 캐릭터 아크 추적 (Novel Contribution)

기존 연구는 캐릭터를 정적 프로필로 취급. 본 시스템은 소설의 타임라인에 따라 캐릭터가 진화:

```python
# 사용자가 "소설 3장까지 읽었어"라고 하면
agent.set_narrative_position(chapter=3)

# 에이전트는 3장까지의 지식/감정 상태만으로 대화
# → 스포일러 방지 + 캐릭터 진화 모델링
```

### 4.2 2차 Theory of Mind (Novel Contribution)

홈즈가 대화 중 "왓슨이라면 이렇게 생각했겠지"라고 추론하는 능력:

```python
class TheoryOfMind:
    def infer_other_character_belief(self, character, other_character, topic):
        """캐릭터가 다른 캐릭터의 믿음을 추론"""
    
    def infer_user_knowledge(self, conversation_history):
        """사용자가 소설에 대해 얼마나 아는지 추론"""
```

### 4.3 자동 캐릭터 로직 추출 (Novel Contribution)

소설 텍스트에서 캐릭터의 행동 규칙을 자동으로 추출하여 코드화:

```python
# 소설에서 자동 추출된 홈즈의 행동 규칙 예시
holmes_rules = {
    "when_presented_with_mystery": "ask_for_details_systematically",
    "when_complimented": "deflect_with_dry_humor",
    "when_bored": "express_restlessness_or_seek_stimulation",
    "when_watson_is_wrong": "correct_gently_but_show_reasoning",
}
```
