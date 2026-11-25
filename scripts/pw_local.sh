#!/usr/bin/env bash
# 로컬 브라우저 검사(Playwright, chromium). 깨끗한 환경에서 전체가 약 1분이다.
#   bash scripts/pw_local.sh                     # 전체
#   bash scripts/pw_local.sh tests/pwa.spec.cjs  # 파일 하나
#   bash scripts/pw_local.sh -g "저장"           # 이름에 맞는 테스트만
# - caffeinate: Mac이 도중에 잠들면 실행 시간이 수십 분으로 부풀어 보이고 테스트가 시간 초과로 실패한다.
# - 포트는 worktree마다 다르다(tests/playwright.config.cjs). 다른 세션의 서버를 재사용하지 않는다.
# - 재시도는 끈다(--retries=0). 불안정한 테스트를 숨기지 않기 위해서다. CI는 재시도 1회다.
set -euo pipefail
cd "$(dirname "$0")/.."
[ -d node_modules/@playwright/test ] || npm ci --no-audit --no-fund --prefer-offline
run=(npx playwright test --config=tests/playwright.config.cjs --retries=0 "$@")
if command -v caffeinate >/dev/null 2>&1; then caffeinate -i "${run[@]}"; else "${run[@]}"; fi
