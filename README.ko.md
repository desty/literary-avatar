# Avatar

[English](README.md) | **한국어**

문학 속 인물과 나누는 시점 인식·원문 기반 대화.

Avatar는 합법적으로 이용할 수 있는 소설을 로컬 중심의 캐릭터 챗봇으로
만듭니다. 원문에서 관련 구절을 검색하고, 인물이 이야기의 어느 시점까지
경험했는지 설정하며, 선택적으로 대화 기억을 세션 간에 저장할 수 있습니다.

> **로컬 중심이지만 완전한 로컬은 아닙니다.** 원문 파일, 검색 인덱스, 기억은
> 설정된 데이터 디렉터리에 저장됩니다. 기본 Claude 백엔드는 Claude Code CLI를
> 통해 프롬프트와 선택된 원문 일부를 외부 모델로 전송합니다. 비공개 자료를
> 사용하기 전에 [개인정보 및 데이터 흐름](docs/privacy.md)을 확인하세요.

## 주요 기능

- CLI에서 셜록 홈즈, 엘리자베스 베넷과 대화합니다.
- 검색과 프롬프트 문맥을 특정 단편 또는 장까지로 제한합니다.
- SQLite FTS5/BM25로 원문 구절을 검색해 답변의 근거로 사용합니다.
- 인물 프로필, 관계, 서사 상태, 행동 지침을 함께 반영합니다.
- 선택적으로 저장되는 평문 대화 기억을 확인하고 삭제합니다.
- 계정 없이 결정론적 mock 백엔드로 전체 연결 구조를 점검합니다.

시점 제어는 스포일러를 줄이는 안전장치이지 수학적으로 보장된 차단 방식은
아닙니다. 모델이 학습 과정에서 얻은 지식을 사용하거나 이후 사건을 추론할 수
있습니다.

## 빠른 시작

### 요구 사항

- Python 3.11–3.13
- 실제 답변 생성 시: 설치 및 인증된 Claude Code CLI (`claude -p`)
- 원문을 처음 내려받을 때 사용할 네트워크 연결

### uv로 설치

```bash
uv sync
uv run avatar-prepare --all
uv run avatar
```

### pip로 설치

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
avatar-prepare --all
avatar
```

`uv.lock`은 개발과 릴리스 검사에 사용하는 재현 가능한 의존성 잠금 파일입니다.
`requirements.txt`는 호환성을 위한 설치 진입점으로 유지됩니다.

### 오프라인 연결 구조 데모

mock 백엔드는 모델을 호출하지 않으며 고정된 응답임을 명시합니다.

```bash
avatar --backend mock
# 또는: AVATAR_GENERATION_BACKEND=mock avatar
```

이 모드는 런타임 연결 구조를 검증하지만, 새로운 프로필·타임라인·행동 자료를
생성하지는 않습니다.

## 기본 캐릭터 준비

저장소에는 작은 프로필, 타임라인, 행동 자료가 포함되어 있습니다. Git에
추적되지 않는 로컬 원문과 검색 인덱스는 다음 명령으로 만듭니다.

```bash
avatar-prepare --all
```

이 명령은 작품을 내려받고 Gutenberg 래퍼를 제거한 뒤, 원문을 파싱하고 로컬
SQLite FTS5 인덱스를 만들며 누락된 분석 자료를 생성합니다. 기존 자료는
`--force-llm`을 지정하지 않는 한 재사용합니다. 외부 모델 호출 없이 다운로드,
파싱, 인덱싱만 하려면 `--skip-llm`을 사용하세요.

## CLI 사용

```bash
avatar
```

```text
/switch       캐릭터 전환
/timeline 3   캐릭터의 지식을 3번째 장/단편까지로 제한
/timeline all 작품 전체에 대한 지식 허용
/memory       최근 로컬 기억 표시
/forget       확인 후 로컬 기억 삭제
/bdi          현재 심리 상태 표시
/reset        대화 초기화
/quit         저장 후 종료
```

## 체크아웃 검증

```bash
python -m unittest discover -s tests -v
python scripts/smoke_check.py
python scripts/check_provenance.py
python -m build
```

원문을 아직 내려받지 않은 체크아웃에서는
`python scripts/smoke_check.py --assets-only`로 저장소에 포함된 자료만 검증할 수
있습니다.

Claude CLI 인증이 되어 있다면 선택적으로 실제 모델 품질 검사도 실행할 수
있습니다.

```bash
python scripts/quality_check.py
```

## 기본 제공 캐릭터

| 캐릭터 | 작품 | 타임라인 단위 | 추적되는 준비 자료 |
| --- | --- | ---: | --- |
| 셜록 홈즈 | *셜록 홈즈의 모험* | 단편 12개 | 프로필, 서사 변화, 행동 규칙 |
| 엘리자베스 베넷 | *오만과 편견* | 61장 | 프로필, 서사 변화, 행동 규칙 |

다운로드한 책과 검색 인덱스는 Git에 포함하지 않습니다. 출처, 관할권,
모델 다운로드, 라이선스에 관한 내용은 [데이터 출처](DATA_SOURCES.md)와
[제3자 고지](THIRD_PARTY_NOTICES.md)를 확인하세요.

## 데이터 위치와 삭제

소스 체크아웃에서는 생성된 상태를 기본적으로 `./data` 아래에 저장합니다.
wheel로 설치하면 기본 자료를 운영체제의 사용자 데이터 디렉터리로 복사합니다.
macOS에서는 `~/Library/Application Support/Avatar`, Linux에서는
`$XDG_DATA_HOME/avatar` 또는 `~/.local/share/avatar`를 사용합니다. 저장 위치를
직접 지정하려면 `AVATAR_DATA_DIR`을 설정하세요.

```text
data/raw/        다운로드한 원문
data/processed/ 파싱된 원문
data/vectordb/  로컬 SQLite 전문 검색 인덱스
data/memory/    평문 대화, 요약, 추론된 사용자 정보
```

위 네 디렉터리는 모두 Git에서 제외됩니다. `/forget`은 현재 캐릭터와 사용자의
기억을 삭제합니다. 설정된 데이터 디렉터리를 제거하면 로컬에서 생성된 모든
데이터가 삭제됩니다. 생성 백엔드에 전송될 수 있는 정보는
[개인정보 및 데이터 흐름](docs/privacy.md)을 확인하세요.

## 아키텍처와 확장

```text
원문 -> 파서 -> 타임라인이 표시된 단위 -> SQLite FTS5 인덱스
              -> 준비된 프로필 / 서사 변화 / 행동 자료

메시지 -> 범위 제한 검색 -> 프롬프트 -> GenerationBackend -> 답변
```

현재 `GenerationBackend`에는 Claude CLI 구현과 결정론적 mock 구현이 있습니다.
`src/characters.py`의 레지스트리가 기본 제공 작품 정보의 단일 기준입니다.
자세한 내용은 [아키텍처](docs/architecture.md)와
[캐릭터 빌더](docs/character-builder.md)를 확인하세요.

현재 지원하는 제품 인터페이스는 CLI입니다. 이 저장소에 프로토타입 웹 UI를
포함하는 대신, 실제 서비스용 웹 클라이언트와 API를 별도로 개발할 예정입니다.

과거 연구 기록, 평가, 논문 초안은 `archive/research/`에 보관합니다. 이 자료들은
현재 제품 성능에 대한 주장으로 간주하지 않습니다.

## 기여와 보안

[기여 안내](CONTRIBUTING.md), [보안 정책](SECURITY.md),
[행동 강령](CODE_OF_CONDUCT.md)을 읽어주세요. 비공개 원문, 인증 정보, 대화 기억,
패치되지 않은 취약점의 세부 내용은 공개 이슈에 올리지 마세요. 관리자는 버전
태그를 만들기 전에 [공개 릴리스 체크리스트](docs/release-checklist.md)를 완료해야
합니다.

## 라이선스

코드와 문서는 MIT 라이선스로 배포합니다. 준비된 생성 데이터는 기여자가 권리를
보유한 범위에서 CC0-1.0으로 제공합니다. 원작, 인용문, 제3자 패키지, 모델,
서비스, 상표에는 각각의 권리와 이용 조건이 적용됩니다. 이 저장소는 REUSE 3.3
규격을 준수합니다. 자세한 내용은 `REUSE.toml`과 `LICENSES/`를 확인하세요.

---

이 번역과 영문 README의 내용이 다른 경우 [영문 README](README.md)를 기준으로
합니다.
