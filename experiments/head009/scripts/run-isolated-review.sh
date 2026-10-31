#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
: "${HEAD009_BROWSER_EXECUTABLE:?Set HEAD009_BROWSER_EXECUTABLE to the unpacked Playwright Chromium headless shell}"
test -x "$HEAD009_BROWSER_EXECUTABLE"
npm run check
npm run validate
npx tsx scripts/validate-organ-data.ts
npx tsx scripts/validate-vdd.ts
npm run build:review
npm run audit:review
printf '\nVerified review HTML: %s\n' "$PWD/out/head009/head009-review.html"
