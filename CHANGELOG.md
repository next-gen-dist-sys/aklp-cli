# Changelog

## [0.2.2](https://github.com/next-gen-dist-sys/aklp-cli/compare/v0.2.1...v0.2.2) (2025-12-17)


### Documentation

* Pylance의 잘못된 경고 회피 ([#12](https://github.com/next-gen-dist-sys/aklp-cli/issues/12)) ([fbc76eb](https://github.com/next-gen-dist-sys/aklp-cli/commit/fbc76eb24c6397a59a33e34b4f38fcca5d8159af))
* README 바이너리 설치 가이드 추가 ([#9](https://github.com/next-gen-dist-sys/aklp-cli/issues/9)) ([202ec4b](https://github.com/next-gen-dist-sys/aklp-cli/commit/202ec4b8770089901a498a8a0263c29c4dde878a))

## [0.2.1](https://github.com/next-gen-dist-sys/aklp-cli/compare/v0.2.0...v0.2.1) (2025-12-16)


### Bug Fixes

* 자동 릴리즈는 release-please.yml에서 처리 ([#7](https://github.com/next-gen-dist-sys/aklp-cli/issues/7)) ([b0c55de](https://github.com/next-gen-dist-sys/aklp-cli/commit/b0c55dec56024077939deaf2d3e1cc65c09c3b4d))

## [0.2.0](https://github.com/next-gen-dist-sys/aklp-cli/compare/v0.1.0...v0.2.0) (2025-12-16)


### Features

* LLM 응답 시간 별도 측정 및 표시 ([#5](https://github.com/next-gen-dist-sys/aklp-cli/issues/5)) ([8c4abe5](https://github.com/next-gen-dist-sys/aklp-cli/commit/8c4abe556ee34e69bdc3a275999ebdb6f9bfe5b3))

## 0.1.0 (2025-12-16)


### ⚠ BREAKING CHANGES

* 빌드 및 배포 자동화 ([#3](https://github.com/next-gen-dist-sys/aklp-cli/issues/3))

### Features

* Add agent service and enhanced UI display ([acdbc75](https://github.com/next-gen-dist-sys/aklp-cli/commit/acdbc7574f9593e512785ac5c844d0cd44151fb8))
* Add file, batch, agent, usage services and bulk operations ([f8b1c93](https://github.com/next-gen-dist-sys/aklp-cli/commit/f8b1c93b6d8c85de46cc5bbce90bcc9ceba13bd4))
* Add first-time OpenAI API key setup ([d3f5114](https://github.com/next-gen-dist-sys/aklp-cli/commit/d3f51142fa1dd3423d0f1cdf36ed6e74f7c57caf))
* config 명령어 추가 (aklp config, cluster, apikey, reset) ([5b6a2d2](https://github.com/next-gen-dist-sys/aklp-cli/commit/5b6a2d244d334904c2eac0c033a96e53cdab3741))
* config.toml에서 host 읽어서 URL 생성 ([e39cc75](https://github.com/next-gen-dist-sys/aklp-cli/commit/e39cc75abd64285be46e1c331aee988c2459d70d))
* ConfigManager에 클러스터 IP 등록 로직 추가 ([31ae293](https://github.com/next-gen-dist-sys/aklp-cli/commit/31ae293b86863981da8819fe6e68ab0927cc5156))
* Integrate aklp-note and aklp-task services with CLI ([ed89e9c](https://github.com/next-gen-dist-sys/aklp-cli/commit/ed89e9c3462598e885bbfcf26cfc8c3640f48e84))
* kubernetes 클라이언트로 클러스터 연결과 시크릿을 관리할 KubernetesManager 구현 ([131be9a](https://github.com/next-gen-dist-sys/aklp-cli/commit/131be9a0f287b9b2a1535abf89f5d127b0b50869))
* Secret 생성 후 자동 재시작 & KUBECONFIG 팁 표시 ([10a659f](https://github.com/next-gen-dist-sys/aklp-cli/commit/10a659f046ed101f3809d182f2ec494598b72cb8))
* Secret 업데이트 후 자동으로 Agent 재시작 ([701a2b9](https://github.com/next-gen-dist-sys/aklp-cli/commit/701a2b9bc69a572317d53acd173c8f4caab6fb17))
* Secret 적용을 위한 aklp-agent 재시작 기능 추가 ([1077bae](https://github.com/next-gen-dist-sys/aklp-cli/commit/1077bae377f12e6cb623dfcd32c65551c8650077))
* setup wizard에 클러스터 등록 -&gt; 연결 테스트 -&gt; 시크릿 등록 -&gt; 키 검증 흐름 추가 ([3253e5e](https://github.com/next-gen-dist-sys/aklp-cli/commit/3253e5eb1c4e1475f728478d68dadcb0ef688db3))
* 빌드 및 배포 자동화 ([#3](https://github.com/next-gen-dist-sys/aklp-cli/issues/3)) ([58cd93e](https://github.com/next-gen-dist-sys/aklp-cli/commit/58cd93eb4d82656896486caa07f6fe29494e6e94))


### Bug Fixes

* prompt argument를 옵션으로 변경하여 서브커맨드 충돌 해결 ([e88ba24](https://github.com/next-gen-dist-sys/aklp-cli/commit/e88ba248dd48ade60c5400f7652d04b9244fd277))


### Documentation

* markdownlint에 맞게 형식 수정 ([a1cb110](https://github.com/next-gen-dist-sys/aklp-cli/commit/a1cb110ada5e6d25ce7888b761be7a6554f128d2))
