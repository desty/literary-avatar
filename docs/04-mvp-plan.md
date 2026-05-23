# MVP 계획: Sherlock Holmes Character Agent

> 작성일: 2026-05-23

## 1. MVP 범위 정의

### 목표
**셜록 홈즈와 대화할 수 있는 CLI 기반 에이전트** — 소설 원문을 기반으로, 홈즈의 성격/말투/지식을 유지하며 사용자와 자연스럽게 대화.

### MVP에 포함 (In Scope) — 전체 완료 (2026-05-23)
- ✅ 소설 텍스트 다운로드 및 파싱 — 12 stories, 2,187 dialogues 추출
- ✅ 캐릭터 프로필 자동 추출 — Big Five, 말투 10개, 가치관 8개, 관계 5개
- ✅ RAG 기반 대화 — ChromaDB 332 chunks, 의미 검색 작동 확인
- ✅ CLI 대화 인터페이스 — Rich UI, /reset, /quit
- ✅ 기본 대화 메모리 (세션 내) — 최근 20턴 유지
- ✅ 5턴 대화 테스트 통과 — 한국어/영어, RAG 정확성, 캐릭터 일관성

### MVP에서 제외 (Out of Scope → Phase 2+)
- ❌ Elizabeth Bennet (2번째 캐릭터)
- ❌ 장기 메모리 (세션 간 지속)
- ❌ 챕터별 캐릭터 아크 추적
- ❌ 2차 Theory of Mind
- ❌ 평가 프레임워크 자동화
- ❌ Web UI
- ❌ 다중 캐릭터 대화

---

## 2. 파일 구조

```
_avatar/
├── README.md
├── requirements.txt
├── docs/
│   ├── 01-research.md
│   ├── 02-novel-candidates.md
│   ├── 03-architecture.md
│   ├── 04-mvp-plan.md
│   └── 05-future-roadmap.md
├── src/
│   ├── __init__.py
│   ├── main.py                 # CLI 진입점 + 대화 루프
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── downloader.py       # Gutenberg 텍스트 다운로드
│   │   ├── parser.py           # 텍스트 → 챕터/장면/대화 파싱
│   │   └── profile_extractor.py # 캐릭터 프로필 자동 추출
│   ├── character/
│   │   ├── __init__.py
│   │   ├── profile.py          # 캐릭터 프로필 데이터 클래스
│   │   ├── engine.py           # 인지 엔진 (응답 생성)
│   │   └── prompt_builder.py   # 시스템 프롬프트 구성
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── conversation.py     # 대화 히스토리 관리
│   │   └── retriever.py        # RAG 검색 (ChromaDB)
│   └── evaluation/
│       ├── __init__.py
│       └── consistency.py      # 기본 일관성 체크
├── data/
│   ├── raw/                    # 원본 소설 텍스트
│   ├── processed/              # 파싱된 구조화 데이터
│   └── profiles/               # 추출된 캐릭터 프로필
└── tests/
    └── ...
```

---

## 3. 구현 단계

### Step 1: 소설 텍스트 수집 & 파싱
**예상 작업**: 2-3시간

```python
# downloader.py
- Project Gutenberg에서 셜록 홈즈 텍스트 다운로드
- "The Adventures of Sherlock Holmes" (12개 단편)

# parser.py  
- Gutenberg 머리말/꼬리말 제거
- 12개 단편을 개별 스토리로 분리
- 각 스토리에서 대화 추출 (발화자 태깅)
- 장면 분리 및 요약
```

### Step 2: 캐릭터 프로필 추출
**예상 작업**: 2-3시간

```python
# profile_extractor.py
- Claude CLI를 사용하여 소설 텍스트 분석
- 추출 항목:
  - Big Five 성격 특성 (0-1 스케일)
  - 특징적 말투/표현 패턴
  - 가치관 및 세계관
  - 왓슨, 모리아티 등과의 관계
  - 추론 방법론 (연역법 등)
  - 습관 및 특이사항 (바이올린, 코카인, 권태 등)
```

### Step 3: RAG 시스템 구축
**예상 작업**: 2-3시간

```python
# retriever.py
- 소설 텍스트를 청크로 분할
- sentence-transformers로 임베딩 생성
- ChromaDB에 저장
- 사용자 질문 → 관련 소설 장면 검색
```

### Step 4: 캐릭터 엔진 & 프롬프트
**예상 작업**: 3-4시간

```python
# engine.py
- 시스템 프롬프트 구성 (캐릭터 프로필 + RAG 컨텍스트)
- Claude CLI 호출로 응답 생성
- 대화 히스토리 관리

# prompt_builder.py
- 캐릭터 프로필을 시스템 프롬프트로 변환
- RAG 검색 결과를 컨텍스트에 삽입
- 대화 히스토리 포맷팅
```

### Step 5: CLI 인터페이스
**예상 작업**: 1-2시간

```python
# main.py
- 대화 루프 (input → process → output)
- 캐릭터 선택 (향후 확장)
- 세션 관리
- 깔끔한 터미널 출력
```

### Step 6: 기본 평가 & 테스트
**예상 작업**: 2시간

```python
# consistency.py
- 캐릭터가 자기 이름을 정확히 아는지
- 소설에 없는 사실을 만들어내지 않는지
- 말투가 일관적인지 (간단한 체크)
```

---

## 4. 의존성

```txt
# requirements.txt
chromadb>=0.4.0
sentence-transformers>=2.0.0
requests>=2.28.0
rich>=13.0.0          # 터미널 UI
```

> **Note**: Claude는 `claude -p` CLI로 호출하므로 anthropic SDK 불필요.

---

## 5. 성공 기준

MVP가 성공적이라고 판단하는 기준:

1. **캐릭터 인식**: 홈즈가 자신을 홈즈로 인식하고, 왓슨/221B 등을 정확히 언급
2. **말투 유지**: "Elementary, my dear Watson" 스타일의 논리적이고 건조한 화법
3. **지식 경계**: 소설에 없는 현대 지식에 대해 캐릭터답게 반응 (모른다고 하거나 추론)
4. **RAG 작동**: 소설의 구체적 사건/인물에 대한 질문에 원문 기반 답변
5. **대화 유지**: 최소 10턴 이상의 자연스러운 대화
6. **몰입감**: 사용자가 "홈즈와 대화하고 있다"는 느낌을 받음
