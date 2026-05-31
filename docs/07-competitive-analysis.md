# 경쟁 분석 및 향후 계획 (2026-05 기준)

> 외부 선행연구 조사 + 논문 포지셔닝 분석 + 실행 계획

---

## 1. 조사한 내용 (Prior-Art Check)

2024년 TimeChara 이후 ~1.5년간의 연구를 조사하여, 우리 아이디어가 이미 발표됐는지 확인.

### 발견된 주요 선행연구

| 논문 | 발표 | 방법 | 우리와 관계 |
|------|------|------|------------|
| **TimeChara** (Ahn et al.) | ACL Findings 2024 | 추론 분해 (Narrative-Experts), 10,895 인스턴스 벤치마크 | 직접 비교 대상 (baseline) |
| **Living the Novel** (Huang et al.) | arXiv 2025-12 (2512.07474) | Diegetic 지식그래프 + Narrative-Present Gate + 적대적 학습 | **#1 스쿱**, #2는 안 함 |
| **RoleKE-Bench / S²RD** (Zhou et al.) | EMNLP 2025 Main | 시대착오=unknown knowledge error 정의, self-doubt 에이전트 | 인용 필수, 메커니즘 다름 |
| **RoleFact** (Sadeq et al.) | EMNLP Findings 2024 | confidence threshold (0.6) 기반 파라메트릭 지식 게이팅 | 의도 유사, 메커니즘 다름 |
| **RoleRAG** (Wang et al.) | 2025 | 그래프 기반 검색 (coherence용) | 낮은 위협 |
| **Context-faithful Prompting** (Zhou et al.) | arXiv 2023 | 명시적/반사실 프롬프팅 > 일반 지시 | 일반 원리 선점 |
| **FaithfulRAG / ParamMute** | 2025 | 파라메트릭 지식 억제로 context-faithfulness | 메커니즘 친척 |

### TimeChara 재현성
- **공개됨**: github.com/ahnjaewoo/timechara (MIT), HF `ahnpersie/timechara`
- Narrative-Experts 구현 포함 → **head-to-head 비교 가능**
- 600 validation + 10,895 test, 14개 캐릭터 (Harry Potter, LOTR 등)

---

## 2. 분석한 내용 (Novelty 판정)

| 우리 기여 | 판정 | 근거 |
|----------|------|------|
| #1 시간축 RAG 필터링 | ❌ **스쿱당함** | Living the Novel(2025-12)이 diegetic story-time gate로 먼저 발표 |
| #2 명시적 unknown-items list | ✅ **여전히 novel** | 역할극 분야에서 유일하게 비어있는 자리 |
| 실험 (명시적 열거 > 모호한 지시) | ⚠️ **역할극 한정 novel** | 일반 원리는 2023 context-faithfulness가 선점, 단 controlled test는 우리가 처음 |
| dual timeline (reader-character) | ❌ **프레임 겹침** | Living the Novel의 diegetic-time과 동일 개념 |

### 핵심 판정
- **스쿱당하지 않았으나 절반 깎임.**
- 살아있는 유일한 헤드라인: **"명시적 미래-금지 항목 열거"가 복잡한 추론분해/그래프/학습 방법과 맞먹는다.**
- 분야는 이 문제를 공인함 (IJCAI 2025 튜토리얼 존재).

### 현 상태 등급
| 목표 | 가능성 |
|------|--------|
| TACL / ACL main | 거의 0 |
| ACL/EMNLP Findings | TimeChara 직접 비교 없으면 낮음 |
| Workshop (Wordplay 등) | 현실적 |
| arXiv | 충분 |

---

## 3. 앞으로 할 것 (Action Items)

### P0 — 논문 재포지셔닝 (실험 전 필수)
- [ ] 헤드라인을 #2(명시적 열거)로 재중심화
- [ ] #1 시간축 필터링 → "Living the Novel과 결합" 수준으로 격하
- [ ] 필수 인용 추가: Living the Novel, RoleKE-Bench, RoleFact, context-faithfulness(Zhou 2023, FaithfulRAG)
- [ ] "명시적 열거 > 모호한 지시" 발견을 "point-in-time 역할극에서의 첫 controlled test"로 프레이밍

### P1 — TimeChara head-to-head (논문 생사 결정)
- [ ] github.com/ahnjaewoo/timechara 클론, 데이터/코드 확보
- [ ] 우리 unknown-items 방법을 TimeChara 벤치마크에 이식
- [ ] Narrative-Experts vs 우리 방법 직접 비교 (가능하면 RoleFact도)
- [ ] 목표 메시지: "더 단순한 prompt-time 방법으로 비슷하거나 나은 성능"

### P2 — 남은 보강 (여유 시)
- [ ] LitTimeQA 8-config ablation을 103쿼리 전체로 재실행 (현재 21쿼리)
- [ ] Elizabeth 58→45 확장 쿼리 실험 재실행
- [ ] 인간 평가 추가 (LLM-judge 단독 약점 방어)
- [ ] profile leakage 수정 (시점별 프로필 생성)

---

## 4. 결정 포인트

**TimeChara 비교를 할 것인가?**
- YES → Findings 도전 가능한 논문이 됨. 단 그들 데이터(타 소설 캐릭터)에 우리 파이프라인 이식 비용 큼.
- NO → 현 상태로 workshop/arXiv 제출. 빠르지만 임팩트 제한.

현재 TACL 제출본은 이미 제출됨 (리뷰 대기). 위 작업은 리뷰 결과 + 재제출/다른 venue 준비용.
