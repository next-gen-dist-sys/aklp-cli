# AKLP - AI Kubernetes Learning Platform CLI

자연어로 Kubernetes를 학습하고 관리할 수 있는 AI 기반 CLI 도구입니다. 복잡한 kubectl 명령어를 몰라도 한글로 원하는 작업을 설명하면 AI가 적절한 명령어를 생성하고 실행합니다.

## ✨ 주요 기능

- **🗣️ 자연어 인터페이스**: 한글/영어로 Kubernetes 작업 요청
- **🎯 kubectl 명령 생성**: AI가 자연어를 kubectl 명령어로 변환
- **👤 Human-in-the-Loop**: 실행 전 사용자 확인 및 승인
- **🔧 로컬 실행**: 생성된 kubectl 명령을 로컬에서 직접 실행
- **🔑 BYOK (Bring Your Own Key)**: 자신의 OpenAI API 키 사용
- **⚡ 성능 측정**: LLM 응답 시간 및 전체 실행 시간 표시
- **📜 세션 히스토리**: 대화 내역 자동 저장

## 📋 요구사항

- kubectl 설치 및 클러스터 연결 설정
- AKLP 백엔드 서비스 실행 → [배포 가이드](https://github.com/next-gen-dist-sys/aklp-infra/tree/main/k8s)

## 🚀 설치 방법

### 방법 1: 바이너리 설치 (권장)

설치 스크립트를 사용하면 OS와 아키텍처에 맞는 바이너리를 자동으로 다운로드합니다.

```bash
curl -sSL https://raw.githubusercontent.com/next-gen-dist-sys/aklp-cli/main/install.sh | sh
```

**수동 다운로드:**

[GitHub Releases](https://github.com/next-gen-dist-sys/aklp-cli/releases)에서 플랫폼에 맞는 바이너리를 직접 다운로드할 수 있습니다.

| Platform            | Asset                  |
| ------------------- | ---------------------- |
| Linux x64           | `aklp-linux-x64`       |
| macOS Intel         | `aklp-macos-x64`       |
| macOS Apple Silicon | `aklp-macos-arm64`     |
| Windows x64         | `aklp-windows-x64.exe` |

**삭제:**

```bash
curl -sSL https://raw.githubusercontent.com/next-gen-dist-sys/aklp-cli/main/install.sh | sh -s uninstall
```

### 방법 2: 소스에서 설치 (개발용)

```bash
git clone https://github.com/next-gen-dist-sys/aklp-cli.git
cd aklp-cli
uv sync
uv run aklp
```

## ⚙️ 초기 설정

처음 `aklp`를 실행하면 자동으로 설정 마법사가 시작됩니다:

1. **클러스터 호스트**: AKLP 서비스가 실행 중인 클러스터 IP 또는 호스트명
2. **OpenAI API Key**: AI 기능을 위한 API 키

설정은 `~/.aklp/config.toml`에 안전하게 저장됩니다.

```toml
# ~/.aklp/config.toml 예시
[cluster]
host = "192.168.1.100"

[openai]
api_key = "sk-..."
```

## 💻 사용 방법

### 대화형 모드 (기본)

```bash
aklp
```

### 사용 예시

```bash
❯ 모든 네임스페이스의 파드 목록 보여줘

🤖 Agent 응답
┌──────────────────────────────────────────────────────────────┐
│ 모든 네임스페이스의 파드 목록 조회                              │
├──────────────────────────────────────────────────────────────┤
│ 📋 명령어: kubectl get pods --all-namespaces                  │
│ 💡 이유: 모든 네임스페이스에서 실행 중인 파드 확인               │
└──────────────────────────────────────────────────────────────┘
  LLM 응답 시간: 1.23초

🤔 이 명령어를 실행할까요? (Y/n): y

✅ kubectl 실행 결과
NAMESPACE     NAME                        READY   STATUS    RESTARTS   AGE
default       nginx-6799fc88d8-abc12      1/1     Running   0          2d
kube-system   coredns-5d78c9869d-xyz34    1/1     Running   0          5d
...

작업 완료 (전체 3.45초 / LLM 1.23초)
```

**더 많은 예시:**

```bash
❯ default 네임스페이스에 nginx 디플로이먼트 만들어줘
❯ my-app 서비스 로그 보여줘
❯ 노드 리소스 사용량 확인해줘
❯ configmap 목록 조회하고 상세 내용도 보여줘
```

## ⌨️ 명령어

| 명령어           | 설명               |
| ---------------- | ------------------ |
| `/help`          | 도움말 표시        |
| `/history`       | 세션 히스토리 보기 |
| `/clear`         | 히스토리 초기화    |
| `/exit`, `/quit` | 종료               |
| `Ctrl+D`         | 빠른 종료          |
| `Ctrl+C`         | 현재 작업 취소     |

## 🔄 작업 흐름

```text
1. 자연어 입력 → 2. AI가 kubectl 명령 생성 → 3. 사용자 확인 → 4. 로컬 실행 → 5. 결과 표시
```

## 📁 프로젝트 구조

```text
aklp-cli/
├── src/aklp/
│   ├── cli.py          # 메인 CLI (Typer)
│   ├── config.py       # 설정 관리
│   ├── executor.py     # kubectl 실행기
│   ├── models.py       # Pydantic 모델
│   ├── secrets.py      # 설정 파일 관리
│   ├── history.py      # 세션 히스토리
│   ├── services/       # API 클라이언트
│   └── ui/             # Rich UI
├── install.sh          # 설치 스크립트
└── pyproject.toml
```

## 🛠️ 개발

```bash
# 개발 환경 설정
uv sync

# 실행
uv run aklp

# 린트 & 포맷
uv run ruff check --fix
uv run ruff format
```

## 📄 라이선스

MIT License

## 🤝 기여하기

이슈를 등록하거나 풀 리퀘스트를 보내주세요.
