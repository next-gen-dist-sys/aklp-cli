# AKLP CLI 릴리즈 가이드

이 문서는 AKLP CLI의 자동화된 릴리즈 프로세스를 설명합니다.

## 릴리즈 흐름

```text
1. PR 생성 (제목: "feat: 새 기능")
       ↓
2. PR 제목 검사 자동 실행
       ↓
3. 리뷰 완료 후 Squash and merge
       ↓
4. release-please가 Release PR 자동 생성
       ↓
5. Release PR 머지
       ↓
6. 태그 생성 + 바이너리 빌드 + GitHub Release 생성
```

## GitHub 저장소 설정 (필수)

### 1. Pull Request 설정

**Settings → General → Pull Requests:**

```text
☑ Allow squash merging
  ☑ Default to pull request title   ← 중요!

☐ Allow merge commits              ← 비활성화 권장
☐ Allow rebase merging             ← 비활성화 권장
```

### 2. Branch Protection (선택)

**Settings → Branches → Add rule:**

```text
Branch name pattern: main

☑ Require a pull request before merging
  ☑ Require approvals (1)
☑ Require status checks to pass before merging
  ☑ Require branches to be up to date before merging
  Status checks:
    - Validate PR Title
☑ Do not allow bypassing the above settings
```

### 3. Actions 권한

**Settings → Actions → General:**

```text
Workflow permissions:
  ☑ Read and write permissions
  ☑ Allow GitHub Actions to create and approve pull requests
```

## Conventional Commits 규칙

PR 제목은 다음 형식을 따라야 합니다:

```text
<type>: <description>

# 또는 scope 포함
<type>(<scope>): <description>
```

### Type 종류

| Type       | 설명             | 릴리즈        |
| ---------- | ---------------- | ------------- |
| `feat`     | 새로운 기능      | Minor (1.X.0) |
| `fix`      | 버그 수정        | Patch (1.0.X) |
| `docs`     | 문서 변경        | 릴리즈 안 함  |
| `style`    | 코드 스타일 변경 | 릴리즈 안 함  |
| `refactor` | 리팩토링         | 릴리즈 안 함  |
| `perf`     | 성능 개선        | Patch         |
| `test`     | 테스트 추가/수정 | 릴리즈 안 함  |
| `build`    | 빌드 설정 변경   | 릴리즈 안 함  |
| `ci`       | CI 설정 변경     | 릴리즈 안 함  |
| `chore`    | 기타 변경        | 릴리즈 안 함  |
| `revert`   | 커밋 되돌리기    | Patch         |

### Breaking Change

호환성이 깨지는 변경은 `!`를 추가:

```text
feat!: API 응답 형식 변경

# 또는 본문에 BREAKING CHANGE 포함
feat: API 응답 형식 변경

BREAKING CHANGE: response.data가 response.result로 변경됨
```

→ Major 버전 증가 (X.0.0)

### 예시

```text
feat: kubectl 실행 기능 추가
fix: KUBECONFIG 경로 인식 오류 수정
docs: README 설치 가이드 업데이트
feat(cli): 대화형 모드 개선
fix(executor): 타임아웃 처리 버그 수정
```

## 릴리즈 프로세스 상세

### 자동 Release PR

`feat:` 또는 `fix:` 커밋이 main에 머지되면, release-please가 자동으로 Release PR을 생성합니다:

```text
chore(main): release 1.2.0

## [1.2.0](link) (2025-01-15)

### Features
* kubectl 실행 기능 추가 (#42)

### Bug Fixes
* KUBECONFIG 경로 인식 오류 수정 (#41)
```

### Release PR 머지

Release PR을 머지하면:

1. `v1.2.0` 태그 자동 생성
2. `build.yml` 워크플로우 트리거
3. Linux/macOS/Windows 바이너리 빌드
4. GitHub Release에 바이너리 업로드

### 빌드 플랫폼

| Platform    | Runner         | Asset Name             |
| ----------- | -------------- | ---------------------- |
| Linux x64   | ubuntu-latest  | `aklp-linux-x64`       |
| macOS x64   | macos-15       | `aklp-macos-x64`       |
| macOS ARM64 | macos-latest   | `aklp-macos-arm64`     |
| Windows x64 | windows-latest | `aklp-windows-x64.exe` |

## 수동 릴리즈 (비상 시)

자동 릴리즈가 실패한 경우:

```bash
# 1. 버전 태그 생성
git tag v1.2.0
git push origin v1.2.0

# 2. 또는 GitHub Actions 수동 실행
# Actions → Build Binaries → Run workflow
```

## 설치 스크립트 테스트

```bash
# 로컬 테스트
./install.sh install

# 특정 버전 설치
AKLP_VERSION=v1.0.0 ./install.sh install

# 제거
./install.sh uninstall
```

## 트러블슈팅

### PR 제목 검사 실패

```text
❌ PR Title Check failed
```

→ PR 제목이 Conventional Commits 형식을 따르는지 확인

### Release PR이 생성되지 않음

- `docs:`, `chore:` 등 릴리즈 안 하는 타입만 있으면 Release PR 생성 안 됨
- `feat:` 또는 `fix:` 커밋이 필요

### 바이너리 빌드 실패

1. Actions 탭에서 실패 로그 확인
2. PyInstaller 호환성 문제일 수 있음
3. 의존성 버전 확인

## 파일 구조

```text
.github/
├── workflows/
│   ├── pr-title.yml         # PR 제목 검사
│   ├── release-please.yml   # Release PR 자동 생성
│   └── build.yml            # 바이너리 빌드
├── release-please-config.json
└── .release-please-manifest.json
```
