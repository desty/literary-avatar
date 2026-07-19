# P0: 논문 재포지셔닝 계획 (branch: p0-repositioning)

> 목표: 경쟁 분석 결과에 따라, 스쿱당한 #1을 격하하고 살아있는 #2를 헤드라인으로.
> 실험(P1, TimeChara 비교) 착수 전에 텍스트부터 정비.

## 배경 (docs/07-competitive-analysis.md 요약)
- **#1 시간축 RAG 필터링** → Living the Novel(2025-12)에 스쿱당함. 격하 필요.
- **#2 명시적 unknown-items list** → 여전히 novel. 헤드라인으로.
- **실험(명시적 열거 > 모호한 지시)** → 역할극 첫 controlled test로 프레이밍.

---

## 작업 단위 (avatar.tex + references.bib)

### T1. references.bib — 필수 인용 5편 추가
- [ ] Living the Novel (arXiv 2512.07474, 2025-12)
- [ ] RoleKE-Bench / S²RD (Zhou et al., EMNLP 2025, arXiv 2409.11726)
- [ ] RoleFact (Sadeq et al., EMNLP Findings 2024, arXiv 2406.17260)
- [ ] Context-faithful Prompting (Zhou et al., arXiv 2303.11315, 2023)
- [ ] FaithfulRAG (arXiv 2506.08938, 2025)

### T2. Title / Abstract 재중심화
- [ ] 헤드라인 = "explicit enumerated negative knowledge boundary"
- [ ] 시간축 RAG는 "결합한다(cf. Living the Novel)" 수준으로 언급
- [ ] 핵심 실험 발견을 "first controlled vague-vs-explicit test in point-in-time RP"로

### T3. Introduction — 기여 재정의
- [ ] 기여 #1(시간축 필터)을 "선행연구와 결합한 구성요소"로 격하
- [ ] 기여 #2(명시적 열거)를 단독 헤드라인으로
- [ ] 기여 #3 = controlled ablation (명시적 vs 모호)
- [ ] dual timeline 언급은 유지하되 "Living the Novel의 diegetic-time과 유사" 명시

### T4. Related Work — 신규 선행연구 차별화
- [ ] Living the Novel: HIGH 위협 → 정면으로 다루고 "우리는 enumeration, 그들은 graph+학습" 차별화
- [ ] RoleKE-Bench: 시대착오 정의 인정, self-doubt와 메커니즘 차이
- [ ] RoleFact: confidence threshold vs 우리 enumeration
- [ ] context-faithfulness 라인: 일반 원리는 선점됐음을 인정, "역할극 controlled test는 처음"

### T5. Method §3.4–3.5 — 강조점 이동
- [ ] §3.4 시간축 RAG: "cf. Living the Novel"로 톤 다운
- [ ] §3.5 unknown-items list: 핵심 메커니즘으로 승격, 상세 기술

### T6. Analysis §5.1 — controlled test 프레이밍
- [ ] "명시적 열거 > 모호한 지시"를 point-in-time RP 첫 controlled 실험으로 명시
- [ ] context-faithfulness(Zhou 2023) 인용하여 일반 원리와 구분

### T7. Conclusion / Future Work 정리
- [ ] 결론을 #2 중심으로
- [ ] Future Work에 "TimeChara head-to-head 비교"를 명시적 다음 단계로

### T8. 빌드 & 검증
- [ ] tectonic 컴파일, 인용 깨짐(`[?]`) 0 확인
- [ ] 페이지 수 확인 (TACL 7-10p)

---

## 브랜치 운영
- `submission/tacl-2026-05` — 제출본, 동결. 절대 커밋 안 함.
- `p0-repositioning` — 이 작업. 완료 후 main 병합 또는 별도 venue용 유지.
- TACL 리뷰 결과에 따라:
  - C-decision(재제출 권유) → p0 + P1(TimeChara 비교) 합쳐 강화본 제출
  - reject → p0 기반으로 workshop/다른 venue

## 다음 (P1, 이 계획 이후)
- TimeChara 데이터(github.com/ahnjaewoo/timechara)에 우리 방법 이식
- Narrative-Experts vs unknown-items 직접 비교
