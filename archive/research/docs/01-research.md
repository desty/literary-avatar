# 연구 조사: 소설 캐릭터 AI 에이전트

> 조사 일자: 2026-05-23

## 1. 개요

퍼블릭 도메인 소설의 캐릭터를 AI 에이전트로 구현하는 프로젝트를 위한 기술 조사.
2024-2026년 최신 논문과 기술을 중심으로, 7개 영역을 조사했다.

---

## 2. 캐릭터 기반 대화 시스템 (Character-Grounded Dialogue)

### Character-LLM (Shao et al., EMNLP 2023)
- **핵심**: Experience Reconstruction — 소설 텍스트에서 캐릭터의 경험, 성격, 감정을 추출하여 LLM을 파인튜닝
- **의의**: "개인 시뮬라크럼" 개념을 제시. 캐릭터의 경험을 재구성하여 에이전트를 만드는 파이프라인의 원형
- 📄 https://arxiv.org/html/2310.10158v2

### RoleLLM (Wang et al., ACL 2024 Findings)
- **핵심**: 역할 수행 벤치마크 + 역할별 프롬프팅/파인튜닝 파이프라인
- **의의**: 역할 수행의 품질을 정량적으로 평가하는 프레임워크 제공
- 📄 https://aclanthology.org/2024.findings-acl.878/

### CoSER (ICML 2025)
- **핵심**: 771권의 책에서 17,966개 캐릭터 데이터 추출. 대화, 내면 사고, 경험 포함
- **의의**: CoSER-70B가 GPT-4o 수준의 역할 수행 달성. 책 기반 캐릭터 데이터의 대규모 벤치마크
- 📄 https://openreview.net/forum?id=BOrR7YqKUt

### OpenCharacter (2025)
- **핵심**: 대규모 합성 페르소나 데이터로 임의의 캐릭터에 일반화. 8B 모델이 GPT-4o를 PersonaGym에서 능가
- **의의**: 파인튜닝 없이 임의의 캐릭터를 구현할 수 있는 가능성
- 📄 https://arxiv.org/html/2501.15427v1

### 프로젝트 적용
CoSER의 책 기반 캐릭터 데이터 추출 방법론 + OpenCharacter의 일반화 접근법을 조합.
소설 원문에서 캐릭터 경험을 재구성하고, 합성 데이터로 보강하는 파이프라인.

---

## 3. 문학 텍스트 RAG (Retrieval-Augmented Generation)

### RoleRAG (2025)
- **핵심**: 엔티티 구분 + 경계 인식 검색기를 구조화된 지식 그래프 위에서 작동
- **의의**: 캐릭터의 지식 범위를 벗어나는 환각을 방지하는 "캐릭터 지식 경계" 개념
- 📄 https://arxiv.org/html/2505.18541v1

### ComoRAG (2025)
- **핵심**: 인지 영감 메모리 구조로 긴 서사 텍스트의 순차적 구조를 존중하는 검색
- **의의**: 전통적 청크 기반 검색이 서사 구조와 충돌하는 문제를 해결
- 📄 https://arxiv.org/pdf/2508.10419

### 프로젝트 적용
RoleRAG의 지식 경계 그래프를 핵심 검색 인프라로 채택.
소설의 캐릭터 관계, 사건, 지식을 구조화된 그래프로 색인하여 대화 중 검색.

---

## 4. 장기 메모리 아키텍처 (Long-Term Memory)

### MemGPT / Letta (Packer et al., 2023)
- **핵심**: 컨텍스트 윈도우를 RAM, 외부 저장소를 디스크로 취급. 자기 편집 메모리
- **의의**: 에이전트가 자신의 메모리를 도구 호출로 관리하는 아키텍처의 표준
- 📄 https://www.leoniemonigatti.com/papers/memgpt.html

### A-Mem (Xu et al., 2025)
- **핵심**: 연상 기억 — 더 인간적인 기억 회상 메커니즘
- **의의**: 기존 검색 기반 기억보다 자연스러운 연상 기반 회상

### Memory OS (EMNLP 2025)
- **핵심**: AI 에이전트를 위한 통합 메모리 운영 체제
- **의의**: 다양한 메모리 유형(에피소드, 의미, 절차적)을 OS 수준에서 통합 관리
- 📄 https://aclanthology.org/2025.emnlp-main.1318.pdf

### Mem0 (2025)
- **핵심**: 프로덕션 수준의 확장 가능한 장기 메모리
- 📄 https://arxiv.org/pdf/2504.19413

### 프로젝트 적용
MemGPT 스타일의 2-tier 메모리 필수:
- **에피소드 메모리**: 사용자와의 대화 이력
- **의미 메모리**: 소설에서 추출한 캐릭터 지식
- **자기 편집**: 세션 간 캐릭터 일관성 유지

---

## 5. 캐릭터 성격 모델링 (Personality Modeling)

### InCharacter (Wang et al., 2024)
- **핵심**: 심리학적 인터뷰 척도(Big Five, MBTI)로 성격 충실도 평가
- **의의**: 캐릭터 성격의 정량적 평가 프레임워크

### BIG5-CHAT (ACL 2025)
- **핵심**: 심리언어학적 방법으로 LLM 성격을 훈련을 통해 형성
- 📄 https://aclanthology.org/2025.acl-long.999.pdf

### CharacterGPT (2025)
- **핵심**: 120문항 BFI 평가를 통한 페르소나 재구성

### 프로젝트 적용
소설 텍스트에서 캐릭터의 Big Five 프로필을 자동 추출.
이를 훈련 신호와 대화 중 일관성 검증 도구로 동시 활용.

---

## 6. 서사 이해 & 인지 아키텍처 (Narrative Understanding & Cognitive Architecture)

### CharacterBox (Wang et al., 2024)
- **핵심**: BDI(Belief-Desire-Intention) 아키텍처 + 벡터 DB 메모리, 내레이터 에이전트 감독
- **의의**: 캐릭터에게 믿음-욕구-의도를 부여하여 행동의 일관성 확보
- 📄 https://arxiv.org/html/2601.10122v1

### The Drama Machine (2024)
- **핵심**: Ego/Superego 심리적 역할의 LLM 에이전트 조율. 상호주관적 대화 + 내면 독백 병렬 처리
- 📄 https://arxiv.org/html/2408.01725v1

### CoALA (Cognitive Architectures for Language Agents)
- **핵심**: 모듈식 메모리, 구조화된 행동 공간, 일반화된 의사결정을 조합하는 청사진
- 📄 https://arxiv.org/abs/2309.02427

### 프로젝트 적용
BDI 모델로 캐릭터의 동기를 모델링. CoALA 청사진을 기반으로 전체 인지 아키텍처 설계.

---

## 7. 평가 메트릭 (Evaluation)

### CharacterBench (2024)
- **핵심**: 인간 판단과 73.1% 스피어만 상관관계. 지식 일관성, 페르소나 충실도, 톤 평가
- 📄 https://www.emergentmind.com/topics/characterbench

### ComperDial (2024)
- **핵심**: 1,485개 대화에 대한 대화 수준 인간 주석 점수
- 📄 https://arxiv.org/pdf/2406.11228

### Verifiable Emotion Reward (VER) (NAACL 2025)
- **핵심**: 긴 상호작용에서 감정 변동을 측정하는 검증 가능한 감정 보상
- 📄 https://aclanthology.org/2025.naacl-long.316.pdf

### 프로젝트 적용
다축 평가:
- 지식 정확성 (캐릭터가 아는 것만 아는가?)
- 성격 일관성 (Big Five 안정성)
- 감정 충실도 (적절한 감정 반응)
- 대화 몰입도

---

## 8. 신기술 & 차별화 기회 (Emerging Techniques)

### Codified Character Logic (2025)
- **핵심**: 캐릭터 행동을 실행 가능한 함수로 형식화. 결정적/확률적 분기 포함
- **의의**: 1B 모델도 큰 모델의 일관성에 근접. 소규모 모델에서도 캐릭터 유지 가능
- 📄 https://arxiv.org/pdf/2505.07705

### Neeko (EMNLP 2024)
- **핵심**: Dynamic LoRA로 효율적 다중 캐릭터 전환
- 📄 https://aclanthology.org/2024.emnlp-main.697.pdf

### Theory of Mind in LLMs (2024-2025)
- **핵심**: LLM의 마음 이론 능력은 아직 제한적. OpenToM 프레임워크 등
- 📄 https://arxiv.org/html/2505.00026v1

---

## 9. 연구 공백 — 논문 기회

현재 연구에서 다루지 않은 영역으로, 본 프로젝트의 차별화 포인트:

| # | 공백 | 설명 | 논문 가능성 |
|---|------|------|-----------|
| 1 | **소설 전체 기반 캐릭터 아크 추적** | 기존 연구는 짧은 프로필/위키만 사용. 책 전체를 기반으로 챕터별 캐릭터 변화를 추적하는 연구 없음 | ⭐⭐⭐ |
| 2 | **캐릭터 진화 모델링** | 서사 타임라인에 따라 성격/지식/관계가 변하는 것을 모델링 | ⭐⭐⭐ |
| 3 | **2차 Theory of Mind** | 캐릭터가 "다른 캐릭터가 뭘 아는지" 추론 (예: 홈즈가 왓슨이 무엇을 모르는지 파악) | ⭐⭐⭐ |
| 4 | **독자 진행도 인식** | 스포일러 방지, 읽은 데까지의 지식으로만 대화 | ⭐⭐ |
| 5 | **텍스트→실행 가능한 캐릭터 로직 자동 추출** | 수동 명세가 아닌, 소설 텍스트에서 자동으로 행동 규칙 추출 | ⭐⭐⭐ |

---

## 10. 참고 자료 모음

### 논문
- [Character-LLM](https://arxiv.org/html/2310.10158v2) - EMNLP 2023
- [RoleLLM](https://aclanthology.org/2024.findings-acl.878/) - ACL 2024
- [CoSER](https://openreview.net/forum?id=BOrR7YqKUt) - ICML 2025
- [OpenCharacter](https://arxiv.org/html/2501.15427v1) - 2025
- [RoleRAG](https://arxiv.org/html/2505.18541v1) - 2025
- [ComoRAG](https://arxiv.org/pdf/2508.10419) - 2025
- [MemGPT](https://www.leoniemonigatti.com/papers/memgpt.html) - 2023
- [Mem0](https://arxiv.org/pdf/2504.19413) - 2025
- [Memory OS](https://aclanthology.org/2025.emnlp-main.1318.pdf) - EMNLP 2025
- [BIG5-CHAT](https://aclanthology.org/2025.acl-long.999.pdf) - ACL 2025
- [CharacterBench](https://www.emergentmind.com/topics/characterbench) - 2024
- [VER](https://aclanthology.org/2025.naacl-long.316.pdf) - NAACL 2025
- [CharacterBox](https://arxiv.org/html/2601.10122v1) - 2024
- [Drama Machine](https://arxiv.org/html/2408.01725v1) - 2024
- [CoALA](https://arxiv.org/abs/2309.02427) - 2023
- [Codified Character Logic](https://arxiv.org/pdf/2505.07705) - 2025
- [Neeko](https://aclanthology.org/2024.emnlp-main.697.pdf) - EMNLP 2024
- [Theory of Mind](https://arxiv.org/html/2505.00026v1) - 2025

### 큐레이션 목록
- [Awesome LLM Role-Playing with Persona](https://github.com/Neph0s/awesome-llm-role-playing-with-persona)
