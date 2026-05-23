# 진행 상황 & 다음 단계

> 최종 업데이트: 2026-05-23

---

## Phase 1 (MVP) — 완료

### 구현 완료 항목

| # | 항목 | 상태 | 상세 |
|---|------|------|------|
| 1 | 프로젝트 구조 설정 | ✅ 완료 | `src/`, `data/`, `docs/`, `tests/` 디렉토리 + requirements.txt |
| 2 | 소설 텍스트 수집 | ✅ 완료 | Gutenberg에서 "The Adventures of Sherlock Holmes" 다운로드 (562K chars) |
| 3 | 텍스트 파싱 | ✅ 완료 | 12개 단편 분리, 2,187개 대화 추출, 발화자 태깅 (Holmes: ~560회 식별) |
| 4 | 캐릭터 프로필 추출 | ✅ 완료 | Claude CLI로 Big Five, 말투 패턴 10개, 가치관 8개, 관계 5개 자동 추출 |
| 5 | RAG 시스템 | ✅ 완료 | ChromaDB + all-MiniLM-L6-v2, 332개 청크 색인, 의미 검색 작동 |
| 6 | 캐릭터 엔진 | ✅ 완료 | 프로필 + RAG + 대화 메모리를 조합한 응답 생성 (Claude CLI 백엔드) |
| 7 | CLI 인터페이스 | ✅ 완료 | Rich 기반 터미널 UI, /reset, /quit 명령어 |

### 파일 구조

```
_avatar/
├── README.md
├── requirements.txt
├── docs/
│   ├── 01-research.md             # 18개 논문 조사
│   ├── 02-novel-candidates.md     # 14개 소설 후보
│   ├── 03-architecture.md         # 시스템 아키텍처
│   ├── 04-mvp-plan.md             # MVP 계획
│   ├── 05-future-roadmap.md       # 전체 로드맵
│   └── 06-progress-and-next.md    # 이 문서
├── src/
│   ├── main.py                    # CLI 진입점
│   ├── ingestion/
│   │   ├── downloader.py          # Gutenberg 다운로드
│   │   ├── parser.py              # 스토리/대화 파싱
│   │   └── profile_extractor.py   # Claude로 프로필 추출
│   ├── character/
│   │   ├── profile.py             # 프로필 로딩
│   │   ├── engine.py              # 인지 엔진 (핵심)
│   │   └── prompt_builder.py      # 시스템 프롬프트 구성
│   ├── memory/
│   │   ├── conversation.py        # 대화 히스토리
│   │   └── retriever.py           # ChromaDB RAG
│   └── evaluation/                # (아직 비어있음)
└── data/
    ├── raw/sherlock_holmes.txt     # 원본 텍스트
    ├── processed/sherlock_holmes.json  # 파싱 결과
    ├── profiles/sherlock_holmes.json   # 캐릭터 프로필
    └── vectordb/                  # ChromaDB 벡터 저장소
```

### 검증 결과 (5턴 테스트)

| 테스트 | 입력 | 결과 |
|--------|------|------|
| RAG 정확성 | "오렌지 씨앗 편지" | "Five Orange Pips" 사건 정확 회상 |
| 대화 메모리 | "K.K.K." (이어서) | 이전 턴 맥락 유지, 연속 추론 |
| 언어 전환 | 영어로 추리법 질문 | 영어로 캐릭터 유지 응답 |
| 감정 표현 | 왓슨 평가 요청 | 칭찬+비판+애정이 자연스럽게 혼합 |
| 깊은 질문 | "외로움을 느끼나요?" | 부정하면서도 행간에 고독 드러남 |

### 기술 스택

- Python 3.9 + Claude Code CLI (`claude -p`)
- ChromaDB (all-MiniLM-L6-v2 임베딩)
- Rich (터미널 UI)

---

## Phase 2 계획 — 심화 + 2번째 캐릭터

### 2.1 Elizabeth Bennet 추가 + 시스템 일반화

현재 코드가 Sherlock Holmes에 하드코딩된 부분이 있음.
2번째 캐릭터를 추가하면서 시스템을 일반화.

| 작업 | 설명 | 난이도 |
|------|------|--------|
| Pride and Prejudice 다운로드/파싱 | `downloader.py` 확장, 소설 구조에 맞는 파서 작성 | 중 |
| 엘리자베스 프로필 추출 | `profile_extractor.py`를 범용화 (캐릭터명 파라미터) | 중 |
| 프롬프트 빌더 일반화 | Holmes 하드코딩 제거, 프로필 기반 동적 생성 | 하 |
| 캐릭터 선택 UI | CLI에서 시작 시 캐릭터 선택 메뉴 | 하 |
| 캐릭터별 RAG 컬렉션 | book_id로 이미 분리되어 있으므로 연결만 하면 됨 | 하 |

### 2.2 장기 메모리 (세션 간 지속)

현재는 세션 내 대화만 기억. 세션 종료 후 모든 것이 사라짐.

| 작업 | 설명 | 참고 논문 |
|------|------|----------|
| 에피소드 메모리 | 대화 세션을 JSON으로 저장/로드 | MemGPT |
| 사용자 프로필 메모리 | 대화에서 사용자 정보 추출 및 저장 | Mem0 |
| 메모리 요약 | 오래된 대화를 Claude로 요약하여 압축 | Memory OS |
| 메모리 검색 | 이전 대화에서 관련 에피소드 검색 | A-Mem |

**핵심**: 홈즈가 "지난번에 당신이 말한 그 사건 말이오..." 라고 할 수 있게 됨.

### 2.3 캐릭터 일관성 강화

| 작업 | 설명 | 참고 논문 |
|------|------|----------|
| Big Five 일관성 검증 | 응답에서 Big Five 점수를 재추출하여 프로필과 비교 | InCharacter |
| 지식 경계 강화 | 현대 지식 질문에 캐릭터다운 거부 응답 | RoleRAG |
| 말투 검증기 | 응답이 캐릭터 말투 패턴과 일치하는지 자동 체크 | CharacterBench |

### 2.4 BDI 모듈 (Belief-Desire-Intention)

캐릭터의 내면 상태를 명시적으로 추적.

```python
# 예시: 대화 중 홈즈의 BDI 상태
{
    "beliefs": ["방문객은 위험에 처해 있다", "이 사건은 K.K.K.와 관련이 있다"],
    "desires": ["사건의 진실을 밝히고 싶다", "방문객을 보호하고 싶다"],
    "intentions": ["더 많은 정보를 수집한다", "경찰에 연락을 권한다"]
}
```

- 매 턴마다 BDI 상태를 Claude로 추론/업데이트
- BDI를 프롬프트에 포함하여 행동 일관성 향상
- 참고: CharacterBox (2024)

---

## Phase 3 계획 — 논문급 기능

> Phase 2 완료 후 착수. 각각이 독립적 기여(contribution)가 될 수 있음.

### 3.1 ⭐ 챕터별 캐릭터 아크 추적

**연구 공백**: 기존 연구는 캐릭터를 정적 프로필로만 취급.

```python
# 사용자가 진행도를 설정하면
agent.set_narrative_position(chapter=3)

# 3장까지의 지식/감정/관계만으로 대화
# → "아이린 애들러? 나는 그런 이름을 들어본 적이 없소." (1장 이전)
# → "그 여자... 나를 이긴 유일한 사람이오." (1장 이후)
```

구현 계획:
1. 소설의 각 챕터/스토리별로 캐릭터 상태 스냅샷 생성
2. 지식 그래프에 시간축 추가 (챕터 번호)
3. `narrative_position`에 따라 RAG 검색 범위 제한
4. 스포일러 방지 로직

### 3.2 ⭐ 2차 Theory of Mind

**연구 공백**: 캐릭터가 다른 캐릭터의 믿음을 추론하는 연구 없음.

구현 계획:
1. 캐릭터 간 관계/지식 비대칭 모델링
2. "홈즈가 생각하는 왓슨의 관점" 추론 모듈
3. "홈즈가 추론하는 사용자의 지식 수준" 적응 모듈
4. 평가: ToM 정확도 벤치마크 설계

### 3.3 ⭐ 텍스트→캐릭터 로직 자동 추출

**연구 공백**: 수동 명세가 아닌, 소설에서 자동으로 행동 규칙 추출.

구현 계획:
1. Claude로 소설 텍스트에서 "if-then" 행동 패턴 추출
2. 확정적/확률적 분기를 포함하는 실행 가능한 로직 코드 생성
3. 로직과 실제 응답의 일치도 평가
4. 참고: Codified Character Logic (2025)

### 3.4 다축 평가 프레임워크

1. 지식 정확성 (캐릭터가 아는 것만 아는가?)
2. 성격 일관성 (Big Five 안정성)
3. 감정 충실도 (VER 기반)
4. 말투 충실도
5. 인간 평가 프로토콜

---

## Phase 4 계획 — 발표 & 공개

- 논문 초고 작성 (ACL / EMNLP / NeurIPS Workshop 타겟)
- 오픈소스 GitHub 공개
- Streamlit 데모 제작
- 블로그/발표

---

## 우선순위 권장

Phase 2에서 가장 임팩트 있는 순서:

```
2.1 Elizabeth Bennet 추가   ← 시스템 일반화 검증 (필수)
     ↓
2.2 장기 메모리             ← 사용자 경험 핵심 차별화
     ↓
2.4 BDI 모듈               ← Phase 3의 선행 작업
     ↓
2.3 일관성 강화             ← 평가 기반 마련
```
