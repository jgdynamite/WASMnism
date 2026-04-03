#!/usr/bin/env bash
set -euo pipefail

# Run the reproduce pipeline from all 3 k6 runners in parallel.
# Collects results back to local machine.
#
# Usage:
#   ./bench/run-multiregion.sh <platform> <gateway-url> [--ml] [--cold]
#
# Prerequisites:
#   - deploy/runners.env exists (created by deploy/k6-runner-setup.sh provision)
#   - Scripts synced to runners (deploy/k6-runner-setup.sh sync)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
RUNNERS_FILE="${REPO_ROOT}/deploy/runners.env"
PLATFORM="${1:?Usage: $0 <platform> <gateway-url> [--ml] [--cold]}"
GATEWAY_URL="${2:?Usage: $0 <platform> <gateway-url> [--ml] [--cold]}"

EXTRA_FLAGS=""
shift 2
for arg in "$@"; do
    EXTRA_FLAGS="${EXTRA_FLAGS} ${arg}"
done

if [ ! -f "${RUNNERS_FILE}" ]; then
    echo "ERROR: No runners.env found at ${RUNNERS_FILE}"
    echo "Run: ./deploy/k6-runner-setup.sh provision"
    exit 1
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="${REPO_ROOT}/results/${PLATFORM}/multiregion_${TIMESTAMP}"
mkdir -p "${RESULTS_DIR}"

echo "============================================"
echo "  WASMnism Multi-Region Benchmark"
echo "  Platform: ${PLATFORM}"
echo "  Gateway:  ${GATEWAY_URL}"
echo "  Flags:    ${EXTRA_FLAGS}"
echo "  Results:  ${RESULTS_DIR}"
echo "  Date:     $(date)"
echo "============================================"
echo ""

# Read runner labels and IPs into parallel arrays
RUNNER_LABELS=()
RUNNER_IPS=()
while IFS='=' read -r label ip; do
    [ -z "$label" ] && continue
    RUNNER_LABELS+=("$label")
    RUNNER_IPS+=("$ip")
done < "${RUNNERS_FILE}"

echo "Runners:"
for i in "${!RUNNER_LABELS[@]}"; do
    echo "  ${RUNNER_LABELS[$i]}: ${RUNNER_IPS[$i]}"
done
echo ""

region_from_label() { echo "$1" | sed 's/^k6-//'; }

# Launch reproduce.sh on each runner in parallel
PIDS=()
REGIONS=()
for i in "${!RUNNER_LABELS[@]}"; do
    label="${RUNNER_LABELS[$i]}"
    ip="${RUNNER_IPS[$i]}"
    region=$(region_from_label "$label")
    log="${RESULTS_DIR}/${region}.log"
    REGIONS+=("$region")

    echo "=== Launching on ${label} (${ip}, region=${region}) ==="

    ssh -o StrictHostKeyChecking=no "root@${ip}" \
        "cd /opt/bench && ./reproduce.sh ${PLATFORM} ${GATEWAY_URL} --region ${region} ${EXTRA_FLAGS}" \
        > "${log}" 2>&1 &

    PIDS+=($!)
    echo "  PID: $!, log: ${log}"
done

echo ""
echo "=== Waiting for all runners to complete ==="
echo "  (This takes ~60 min with --ml --cold, ~40 min without --cold)"
echo ""

FAILED=0
for i in "${!PIDS[@]}"; do
    pid="${PIDS[$i]}"
    if wait "$pid"; then
        echo "  PID ${pid} (${RUNNER_LABELS[$i]}): SUCCESS"
    else
        echo "  PID ${pid} (${RUNNER_LABELS[$i]}): FAILED (check log)"
        FAILED=$((FAILED + 1))
    fi
done

if [ "$FAILED" -gt 0 ]; then
    echo ""
    echo "WARNING: ${FAILED} runner(s) failed. Check logs in ${RESULTS_DIR}/"
fi

echo ""
echo "=== Collecting results from runners ==="

for i in "${!RUNNER_LABELS[@]}"; do
    label="${RUNNER_LABELS[$i]}"
    ip="${RUNNER_IPS[$i]}"
    region="${REGIONS[$i]}"
    region_dir="${RESULTS_DIR}/${region}"
    mkdir -p "${region_dir}"

    echo "  Collecting from ${label} (${ip})..."

    # Copy the latest 7run directory
    REMOTE_LATEST=$(ssh -o StrictHostKeyChecking=no "root@${ip}" \
        "ls -td /opt/results/${PLATFORM}/7run_* 2>/dev/null | head -1" || true)

    if [ -n "${REMOTE_LATEST}" ]; then
        scp -o StrictHostKeyChecking=no -r "root@${ip}:${REMOTE_LATEST}" "${region_dir}/7run/" 2>/dev/null || true
    fi

    # Copy medians
    scp -o StrictHostKeyChecking=no "root@${ip}:/opt/results/${PLATFORM}/medians_${region}_"*.md "${region_dir}/" 2>/dev/null || true

    # Copy cold start results if they exist
    scp -o StrictHostKeyChecking=no "root@${ip}:/opt/results/${PLATFORM}/cold_start/"*"_${region}.json" "${region_dir}/" 2>/dev/null || true
done

echo ""
echo "============================================"
echo "  Multi-Region Benchmark Complete"
echo "============================================"
echo ""
echo "  Results: ${RESULTS_DIR}/"
echo ""
echo "  Per-region:"
for i in "${!REGIONS[@]}"; do
    echo "    ${REGIONS[$i]}: ${RESULTS_DIR}/${REGIONS[$i]}/"
done
echo ""
echo "  Next steps:"
echo "    1. Review per-region medians in each region dir"
echo "    2. Compare platforms:"
echo "       python3 bench/build-scorecard.py ${RESULTS_DIR}/<region>/7run/ results/<other>/<region>/7run/"
echo ""
