# 소설 후보: 퍼블릭 도메인 캐릭터

> 조사 일자: 2026-05-23

## 선정 기준

1. **퍼블릭 도메인** — 미국: 1928년 이전 출판 / 국제: 저자 사망 70년 이상
2. **풍부한 캐릭터** — 뚜렷한 성격, 말투, 세계관
3. **문화적 인지도** — 대중이 대화하고 싶어할 만한 유명 캐릭터
4. **대화 풍부** — 원문에 캐릭터의 목소리를 보여주는 대화가 충분
5. **캐릭터 복잡성** — 도덕적 양면성, 성장 아크, 흥미로운 관점
6. **디지털 접근성** — Project Gutenberg 등에서 전문 이용 가능

---

## 선정된 캐릭터 (★ = 1차 구현 대상)

### Victorian / Gothic

| 소설 | 저자 | 연도 | 캐릭터 | 특징 | 소스 |
|------|------|------|--------|------|------|
| ★ **The Adventures of Sherlock Holmes** | Arthur Conan Doyle | 1892 | Sherlock Holmes | 초논리적 추론, 건조한 위트, 괴짜 습관. 대화 밀도 최고 | [Gutenberg #1661](https://www.gutenberg.org/ebooks/1661) |
| **Dracula** | Bram Stoker | 1897 | Count Dracula | 격식체, 위협적, 유혹적 화법. 서간체 형식 | [Gutenberg #345](https://www.gutenberg.org/ebooks/345) |
| **Frankenstein** | Mary Shelley | 1818 | The Creature | 거부와 정체성에 대한 철학적 독백. AI와 테마적 공명 | [Gutenberg #84](https://www.gutenberg.org/ebooks/84) |
| ★ **Pride and Prejudice** | Jane Austen | 1813 | Elizabeth Bennet | 날카로운 위트, 사회 관찰, 아이러니. 대화가 거의 시나리오 수준 | [Gutenberg #1342](https://www.gutenberg.org/ebooks/1342) |

### Adventure / Satire

| 소설 | 저자 | 연도 | 캐릭터 | 특징 | 소스 |
|------|------|------|--------|------|------|
| **Huckleberry Finn** | Mark Twain | 1884 | Huck Finn | 독특한 구어체, 양심 vs 사회의 도덕적 고뇌 | [Gutenberg #76](https://www.gutenberg.org/ebooks/76) |
| **Don Quixote** | Cervantes | 1605 | Don Quixote | 이상주의 vs 현실, 자신만의 서사를 구축하는 캐릭터 | [Gutenberg #996](https://www.gutenberg.org/ebooks/996) |
| **Alice in Wonderland** | Lewis Carroll | 1865 | Alice / Mad Hatter | 논리 비틀기, 언어유희, 부조리 철학 | [Gutenberg #11](https://www.gutenberg.org/ebooks/11) |

### Russian Classics

| 소설 | 저자 | 연도 | 캐릭터 | 특징 | 소스 |
|------|------|------|--------|------|------|
| **Crime and Punishment** | Dostoevsky | 1866 | Raskolnikov | 강렬한 심리적 내면, 도덕적 고뇌, 철학적 논쟁 | [Gutenberg #2554](https://www.gutenberg.org/ebooks/2554) |
| **The Brothers Karamazov** | Dostoevsky | 1880 | Ivan Karamazov | "대심문관" — 문학 최고의 철학적 목소리 | [Gutenberg #28054](https://www.gutenberg.org/ebooks/28054) |

### French / Other European

| 소설 | 저자 | 연도 | 캐릭터 | 특징 | 소스 |
|------|------|------|--------|------|------|
| **Monte Cristo** | Alexandre Dumas | 1844 | Edmond Dantès | 자기 재창조, 전략적, 도덕적 복잡성. 다중 정체성 | [Gutenberg #1184](https://www.gutenberg.org/ebooks/1184) |
| **Dr Jekyll & Mr Hyde** | R.L. Stevenson | 1886 | Jekyll/Hyde | 이중 인격 — AI가 페르소나를 전환하기에 적합 | [Gutenberg #43](https://www.gutenberg.org/ebooks/43) |

### East Asian

| 소설 | 저자 | 연도 | 캐릭터 | 특징 | 소스 |
|------|------|------|--------|------|------|
| **서유기** | 오승은 | c.1592 | 손오공 | 트릭스터, 불손함, 강력함, 유머. 동아시아 전역 인지도 | [Internet Archive](https://archive.org/details/journeytothewestwuchengen1592) |
| **겐지 이야기** | 무라사키 시키부 | c.1010 | 히카루 겐지 | 세계 최초의 소설. 세련되고 감정적으로 복잡 | Waley 번역 via Internet Archive |

### Early 20th Century

| 소설 | 저자 | 연도 | 캐릭터 | 특징 | 소스 |
|------|------|------|--------|------|------|
| **The Great Gatsby** | Fitzgerald | 1925 | Jay Gatsby | 신비롭고, 야심적이고, 비극적. 2021 퍼블릭 도메인 | [Gutenberg AU](https://gutenberg.net.au/ebooks02/0200041.txt) |

---

## 1차 구현 대상

### 1순위: Sherlock Holmes
- **이유**: 가장 뚜렷한 목소리, 가장 많은 대화, 논리적 추론 시연 가능
- **데이터**: 56개 단편 + 4개 장편, 모두 퍼블릭 도메인
- **도전**: 추론 과정을 실시간으로 보여주는 것

### 2순위: Elizabeth Bennet
- **이유**: 위트, 넓은 대중 호소력, 대화 중심 텍스트
- **데이터**: Pride and Prejudice 1권
- **도전**: 리젠시 시대 영어의 자연스러운 현대화
