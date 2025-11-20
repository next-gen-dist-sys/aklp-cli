# AKLP - MSA CLI 에이전트

FastAPI 마이크로서비스(LLM, Note, Task)와 연동하여 자연어 입력을 통해 파일 생성과 쉘 명령어 실행을 자동화하는 Python 3.14 기반 대화형 CLI 에이전트입니다.

## ✨ 주요 기능

- **🗣️ 대화형 모드**: Claude Code처럼 계속 대화하며 작업 수행
- **💬 자연어 처리**: 한글/영어로 원하는 작업을 설명하면 AI가 분석
- **👤 Human-in-the-Loop**: 실행 전 사용자 확인 및 승인 과정
- **🎨 모던한 UI**: Rich 라이브러리 기반의 우아하고 세련된 터미널 인터페이스
- **⚡ 비동기 아키텍처**: httpx 기반 빠른 비차단 I/O 처리
- **📜 세션 히스토리**: 대화 내역 자동 저장 및 조회 기능
- **🔒 타입 안전성**: Pydantic V2 기반 완전한 타입 검증

## 📋 요구사항

- Python 3.14 이상
- 실행 중인 3개의 마이크로서비스:
  - **LLM 서비스**: 자연어 분석 엔드포인트 (`POST /analyze`)
  - **Note 서비스**: 파일 생성 엔드포인트 (`POST /notes`)
  - **Task 서비스**: 명령어 실행 엔드포인트 (`POST /tasks/execute`)

## 🚀 설치 방법

### 1. 저장소 클론

```bash
git clone https://github.com/next-gen-dist-sys/aklp-cli.git
cd aklp-cli
```

### 2. 의존성 설치

**uv 사용 (권장):**
```bash
uv pip install -e .
```

**pip 사용:**
```bash
pip install -e .
```

### 3. 환경 설정

```bash
cp .env.example .env
```

`.env` 파일을 열어 서비스 URL을 설정하세요:

```env
LLM_SERVICE_URL=http://localhost:8001
NOTE_SERVICE_URL=http://localhost:8002
TASK_SERVICE_URL=http://localhost:8003
```

## 💻 사용 방법

### 대화형 모드 (기본)

인자 없이 실행하면 대화형 REPL 모드로 시작합니다:

```bash
aklp
```

**실행 화면:**
```
┌──────────────────────────────────────────┐
│      ✨ AKLP Interactive Mode ✨        │
│                                          │
│     자연어로 작업을 요청하세요.           │
│                                          │
│          💡 명령어                       │
│        /help      도움말 보기            │
│        /history   세션 히스토리 보기     │
│        /clear     히스토리 초기화        │
│        /exit      종료                   │
└──────────────────────────────────────────┘
             Ctrl+D로 빠른 종료

❯ 현재 폴더에 README.md 만들고 ls -al 실행해줘
[AI가 분석 중...]

✨ 프로젝트 초기화 ✨
[분석 결과 표시]

🤔 위 작업을 진행하시겠습니까? (y/n): y

✓ 파일 생성 완료: README.md
✓ 명령어 실행 성공

────────────────────────────────────────

❯ /history
[히스토리 테이블 표시]

❯ /exit
👋 Goodbye! 다음에 또 만나요!
```

### 단일 실행 모드

프롬프트와 함께 실행하면 한 번만 실행하고 종료합니다:

```bash
aklp "현재 폴더에 README.md 만들고 ls -al 실행해줘"
```

### 사용 예시

**파일 생성:**
```bash
❯ main.py 파일에 Hello World 함수 만들어줘
```

**프로젝트 초기화:**
```bash
❯ Python 프로젝트 초기 구조 만들고 requirements.txt도 생성해줘
```

**문서 작성:**
```bash
❯ API 문서를 작성하고 마크다운 형식으로 저장해줘
```

## ⌨️ 특수 명령어

대화형 모드에서 사용 가능한 명령어들:

| 명령어 | 설명 |
|--------|------|
| `/help` | 도움말 표시 |
| `/history` | 현재 세션의 대화 히스토리 보기 |
| `/clear` | 히스토리 초기화 |
| `/exit` | REPL 모드 종료 |
| `/quit` | REPL 모드 종료 |
| `Ctrl+D` | 빠른 종료 |
| `Ctrl+C` | 현재 작업 취소 |

## 🔄 작업 흐름

1. **입력**: 자연어로 작업 요청
2. **분석**: AI가 요청을 분석하고 실행 계획 표시
3. **확인**: 사용자가 분석 결과를 검토하고 승인/거부
4. **실행**: 승인 시 파일 생성 → 명령어 실행 순서로 진행
5. **결과**: 실행 결과(STDOUT/STDERR) 표시
6. **히스토리**: 대화 내역 자동 저장

## 📁 프로젝트 구조

```
aklp-cli/
├── pyproject.toml          # 프로젝트 설정 및 의존성
├── .env.example            # 환경 변수 예시
├── .gitignore              # Git 제외 파일
├── README.md               # 프로젝트 문서
└── src/aklp/
    ├── __init__.py         # 패키지 초기화
    ├── __main__.py         # 진입점 (python -m aklp)
    ├── cli.py              # 메인 CLI 로직 (Typer)
    ├── config.py           # 환경 설정 관리
    ├── models.py           # Pydantic 데이터 모델
    ├── history.py          # 세션 히스토리 관리
    ├── services/           # 마이크로서비스 클라이언트
    │   ├── __init__.py
    │   ├── llm.py          # LLM 서비스 클라이언트
    │   ├── note.py         # Note 서비스 클라이언트
    │   └── task.py         # Task 서비스 클라이언트
    └── ui/                 # Rich UI 컴포넌트
        ├── __init__.py
        └── display.py      # 터미널 UI 표시 함수
```

## 💾 히스토리 저장

- 각 세션의 대화 내역이 `~/.aklp_history.json`에 자동 저장됩니다
- 최대 100개의 세션 히스토리를 유지합니다
- 세션 종료 시 자동으로 저장됩니다
- 저장되는 정보:
  - 사용자 프롬프트
  - AI 분석 결과
  - 실행 여부
  - 파일 생성 결과
  - 명령어 실행 결과
  - 오류 메시지

## 🛠️ 개발 가이드

### 개발 모드 실행

```bash
python -m aklp
```

또는 프롬프트와 함께:

```bash
python -m aklp "테스트 작업"
```

### 코드 스타일

프로젝트는 다음 도구들을 사용합니다:
- **ruff**: 린팅 및 포맷팅
- **mypy**: 타입 체크

### 주요 의존성

- `typer[all]` - CLI 프레임워크
- `rich` - 터미널 UI
- `httpx` - 비동기 HTTP 클라이언트
- `pydantic` - 데이터 검증
- `pydantic-settings` - 설정 관리
- `python-dotenv` - 환경 변수 로딩

## 🎨 UI 스타일 가이드

모던하고 우아한 터미널 UI:
- **색상 팔레트**: 부드러운 파스텔 톤 (Blue, Magenta, Cyan)
- **타이포그래피**: 섹션별 명확한 구분, 적절한 여백
- **아이콘**: 직관적인 이모지 사용 (✨, 📋, 📄, ⚡, ✓, ✗)
- **레이아웃**: Panel과 Table 기반 구조화된 정보 표시

## 📄 라이선스

MIT License

## 🤝 기여하기

기여를 환영합니다! 이슈를 등록하거나 풀 리퀘스트를 보내주세요.

## 📞 문의

문제가 발생하거나 질문이 있으시면 GitHub Issues를 이용해주세요.
