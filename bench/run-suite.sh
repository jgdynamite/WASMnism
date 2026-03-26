#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLATFORM="${1:?Usage: $0 <platform-name> <gateway-url> [--cold]}"
GATEWAY_URL="${2:?Usage: $0 <platform-name> <gateway-url> [--cold]}"
COLD="${3:-}"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="${SCRIPT_DIR}/../results/${PLATFORM}/${TIMESTAMP}"
mkdir -p "${RESULTS_DIR}"

echo "============================================"
echo "  WASMnism Benchmark Suite"
echo "  Platform: ${PLATFORM}"
echo "  Gateway:  ${GATEWAY_URL}"
echo "  Results:  ${RESULTS_DIR}"
echo "  Date:     $(date)"
echo "============================================"
echo ""

echo "=== Pre-flight health check ==="
CODE=$(curl -s -o /dev/null -w "%{http_code}" "${GATEWAY_URL}/gateway/health")
if [ "${CODE}" != "200" ]; then
    echo "FAIL: Health check returned ${CODE}"
    exit 1
fi
echo "  OK"
echo ""

echo "=== Warm-up request (triggers ML model load) ==="
curl -sf -X POST "${GATEWAY_URL}/gateway/moderate" \
    -H "Content-Type: application/json" \
    -d '{"labels":["safe","unsafe"],"nonce":"warmup","text":"warm up request"}' \
    -o /dev/null -w "  HTTP %{http_code} in %{time_total}s\n"
sleep 3
echo ""

echo "=== Test 1/5: Warm Light (GET /gateway/health, 10 VUs, 60s) ==="
k6 run \
    --env GATEWAY_URL="${GATEWAY_URL}" \
    --summary-export="${RESULTS_DIR}/warm-light.json" \
    --quiet \
    "${SCRIPT_DIR}/warm-light.js"
echo ""

echo "=== Test 2/5: Warm Heavy (POST /gateway/moderate + ML, 5 VUs, 60s) ==="
k6 run \
    --env GATEWAY_URL="${GATEWAY_URL}" \
    --summary-export="${RESULTS_DIR}/warm-heavy.json" \
    --quiet \
    "${SCRIPT_DIR}/warm-heavy.js"
echo ""

echo "=== Test 3/5: Concurrency Ladder (1→5→10→25→50 VUs, 150s) ==="
k6 run \
    --env GATEWAY_URL="${GATEWAY_URL}" \
    --summary-export="${RESULTS_DIR}/concurrency-ladder.json" \
    --quiet \
    "${SCRIPT_DIR}/concurrency-ladder.js"
echo ""

echo "=== Test 4/5: Consistency (5 VUs, 120s) ==="
k6 run \
    --env GATEWAY_URL="${GATEWAY_URL}" \
    --summary-export="${RESULTS_DIR}/consistency.json" \
    --quiet \
    "${SCRIPT_DIR}/consistency.js"
echo ""

if [ "${COLD}" = "--cold" ]; then
    echo "=== Test 5/5: Cold Start (10 iterations, ~20 min) ==="
    k6 run \
        --env GATEWAY_URL="${GATEWAY_URL}" \
        --summary-export="${RESULTS_DIR}/cold-start.json" \
        "${SCRIPT_DIR}/cold-start.js"
    echo ""
else
    echo "=== Test 5/5: Cold Start — SKIPPED (use --cold to enable) ==="
    echo ""
fi

echo "============================================"
echo "  Suite complete! Results: ${RESULTS_DIR}/"
echo "============================================"
