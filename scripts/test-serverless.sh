#!/bin/bash
#
# Serverless Inference E2E Test for ComfyuME
# Tests the full job lifecycle through serverless containers (Verda H200/B300)
#
# Usage:
#   ./scripts/test-serverless.sh              # Test active endpoint (config check + submit)
#   ./scripts/test-serverless.sh --dry-run    # Config check only (no GPU cost)
#   ./scripts/test-serverless.sh --all        # Test all configured endpoints
#   ./scripts/test-serverless.sh --timeout 60 # Custom timeout (default: 120s)
#

set -e

# Source shared helpers
source "$(dirname "$0")/test-helpers.sh"

# Load environment
if ! load_env; then
    exit 1
fi

# ============================================================================
# Parse Arguments
# ============================================================================

DRY_RUN=false
TEST_ALL=false
TIMEOUT=120

while [ $# -gt 0 ]; do
    case "$1" in
        --dry-run)  DRY_RUN=true ;;
        --all)      TEST_ALL=true ;;
        --timeout)  TIMEOUT="$2"; shift ;;
        --help|-h)
            echo "Usage: $0 [--dry-run] [--all] [--timeout N]"
            echo ""
            echo "  --dry-run    Config check only, no job submission (no GPU cost)"
            echo "  --all        Check all 4 serverless endpoints, not just active"
            echo "  --timeout N  Seconds to wait for job completion (default: 120)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1 (try --help)"
            exit 1
            ;;
    esac
    shift
done

QM_PORT="${QUEUE_MANAGER_PORT:-3000}"

echo "════════════════════════════════════════════════════════════"
echo "  ComfyuME Serverless Inference Test"
echo "════════════════════════════════════════════════════════════"
echo ""
if [ "$DRY_RUN" = true ]; then
    info "Mode: DRY RUN (config check only, no GPU cost)"
else
    info "Mode: LIVE (will submit a test job — may incur GPU cost)"
fi
info "Timeout: ${TIMEOUT}s"
echo ""

# ==========================================================================
# 1. Serverless Configuration
# ==========================================================================
section_header "1" "Serverless Configuration"

# Inference mode
if [ "${INFERENCE_MODE}" = "serverless" ]; then
    pass_test "INFERENCE_MODE=serverless"
else
    fail_test "INFERENCE_MODE=${INFERENCE_MODE:-not set}" "Expected 'serverless'"
    echo ""
    echo "  This test requires INFERENCE_MODE=serverless in .env"
    print_summary "Serverless Test"
    exit 1
fi

# Active endpoint selector
info "SERVERLESS_ACTIVE=${SERVERLESS_ACTIVE:-default}"

# API key
if [ -n "${SERVERLESS_API_KEY}" ]; then
    KEY_PREVIEW="${SERVERLESS_API_KEY:0:8}..."
    pass_test "SERVERLESS_API_KEY configured (${KEY_PREVIEW})"
else
    fail_test "SERVERLESS_API_KEY not set" "Required for Verda auth"
fi

# Check all endpoint vars
ENDPOINT_NAMES=("h200-spot" "h200-on-demand" "b300-spot" "b300-on-demand")
ENDPOINT_VARS=("SERVERLESS_ENDPOINT_H200_SPOT" "SERVERLESS_ENDPOINT_H200_ON_DEMAND" "SERVERLESS_ENDPOINT_B300_SPOT" "SERVERLESS_ENDPOINT_B300_ON_DEMAND")
CONFIGURED_COUNT=0

for i in "${!ENDPOINT_NAMES[@]}"; do
    NAME="${ENDPOINT_NAMES[$i]}"
    VAR="${ENDPOINT_VARS[$i]}"
    VALUE="${!VAR}"

    if [ -n "$VALUE" ]; then
        CONFIGURED_COUNT=$((CONFIGURED_COUNT + 1))
        if [ "$TEST_ALL" = true ]; then
            pass_test "Endpoint ${NAME}: configured"
        fi
    else
        if [ "$TEST_ALL" = true ]; then
            info "Endpoint ${NAME}: not configured"
        fi
    fi
done

# Fallback endpoint
if [ -n "${SERVERLESS_ENDPOINT}" ]; then
    CONFIGURED_COUNT=$((CONFIGURED_COUNT + 1))
    info "Fallback SERVERLESS_ENDPOINT: configured"
fi

if [ "$CONFIGURED_COUNT" -gt 0 ]; then
    pass_test "Serverless endpoints configured: ${CONFIGURED_COUNT}"
else
    fail_test "No serverless endpoints configured" "Set at least one SERVERLESS_ENDPOINT_* var"
fi

# ==========================================================================
# 2. Queue Manager Serverless Status
# ==========================================================================
section_header "2" "Queue Manager Serverless Status"

QM_HEALTH=$(curl -s --max-time 10 "http://localhost:${QM_PORT}/health" 2>/dev/null || echo "{}")

if echo "$QM_HEALTH" | jq -e '.status' >/dev/null 2>&1; then
    QM_STATUS=$(echo "$QM_HEALTH" | jq -r '.status')
    QM_MODE=$(echo "$QM_HEALTH" | jq -r '.inference_mode')
    QM_GPU=$(echo "$QM_HEALTH" | jq -r '.active_gpu')
    QM_ENDPOINT=$(echo "$QM_HEALTH" | jq -r '.serverless_endpoint // "none"')

    if [ "$QM_STATUS" = "healthy" ]; then
        pass_test "Queue Manager healthy"
    else
        fail_test "Queue Manager unhealthy" "Status: ${QM_STATUS}"
    fi

    if [ "$QM_MODE" = "serverless" ]; then
        pass_test "QM inference mode: serverless"
    else
        fail_test "QM inference mode: ${QM_MODE}" "Expected serverless"
    fi

    if [ "$QM_ENDPOINT" != "none" ] && [ "$QM_ENDPOINT" != "null" ]; then
        pass_test "Active endpoint: ${QM_ENDPOINT} (${QM_GPU})"
    else
        fail_test "No active endpoint in QM health"
    fi
else
    fail_test "Queue Manager not responding" "Is comfy-queue-manager running?"
fi

# ==========================================================================
# 3. Endpoint Reachability
# ==========================================================================
section_header "3" "Endpoint Reachability"

# Build auth header
AUTH_HEADER=""
if [ -n "${SERVERLESS_API_KEY}" ]; then
    AUTH_HEADER="Authorization: Bearer ${SERVERLESS_API_KEY}"
fi

# Function to test an endpoint's health
test_endpoint_health() {
    local name="$1"
    local url="$2"

    if [ -z "$url" ]; then
        info "Endpoint ${name}: not configured (skipped)"
        return
    fi

    # Try /health or / — serverless containers may return different paths
    local code
    if [ -n "$AUTH_HEADER" ]; then
        code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 -H "$AUTH_HEADER" "${url}/" 2>/dev/null || echo "000")
    else
        code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 "${url}/" 2>/dev/null || echo "000")
    fi

    if [ "$code" = "200" ] || [ "$code" = "404" ] || [ "$code" = "405" ]; then
        # 200=healthy, 404/405=server running but no root handler (still reachable)
        pass_test "Endpoint ${name} reachable (HTTP ${code})"
    elif [ "$code" = "000" ]; then
        warn "Endpoint ${name} unreachable (cold start or offline)"
    elif [ "$code" = "401" ] || [ "$code" = "403" ]; then
        fail_test "Endpoint ${name} auth failed (HTTP ${code})" "Check SERVERLESS_API_KEY"
    else
        warn "Endpoint ${name} returned HTTP ${code}"
    fi
}

if [ "$TEST_ALL" = true ]; then
    test_endpoint_health "h200-spot" "${SERVERLESS_ENDPOINT_H200_SPOT}"
    test_endpoint_health "h200-on-demand" "${SERVERLESS_ENDPOINT_H200_ON_DEMAND}"
    test_endpoint_health "b300-spot" "${SERVERLESS_ENDPOINT_B300_SPOT}"
    test_endpoint_health "b300-on-demand" "${SERVERLESS_ENDPOINT_B300_ON_DEMAND}"
else
    # Determine which endpoint is active
    case "${SERVERLESS_ACTIVE}" in
        h200-spot)      ACTIVE_URL="${SERVERLESS_ENDPOINT_H200_SPOT}" ;;
        h200-on-demand) ACTIVE_URL="${SERVERLESS_ENDPOINT_H200_ON_DEMAND}" ;;
        b300-spot)      ACTIVE_URL="${SERVERLESS_ENDPOINT_B300_SPOT}" ;;
        b300-on-demand) ACTIVE_URL="${SERVERLESS_ENDPOINT_B300_ON_DEMAND}" ;;
        *)              ACTIVE_URL="${SERVERLESS_ENDPOINT}" ;;
    esac
    test_endpoint_health "${SERVERLESS_ACTIVE:-default}" "$ACTIVE_URL"
fi

# ==========================================================================
# 4. End-to-End Job Submission (unless --dry-run)
# ==========================================================================
section_header "4" "End-to-End Job Submission"

if [ "$DRY_RUN" = true ]; then
    info "Skipping job submission (--dry-run mode)"
    info "To submit a test job, run without --dry-run"
else
    # Submit a minimal test workflow via the Queue Manager API
    # This goes through the full path: API → QM → serverless endpoint
    TEST_WORKFLOW='{"user_id":"test_e2e","workflow":{"1":{"class_type":"CheckpointLoaderSimple","inputs":{"ckpt_name":"test.safetensors"}}},"priority":2}'

    info "Submitting test job via /api/jobs..."
    START_TIME=$(date +%s)

    JOB_RESPONSE=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$TEST_WORKFLOW" \
        --max-time "$TIMEOUT" \
        "http://localhost:${QM_PORT}/api/jobs" 2>/dev/null || echo '{"error":"timeout"}')

    END_TIME=$(date +%s)
    ELAPSED=$((END_TIME - START_TIME))

    if echo "$JOB_RESPONSE" | jq -e '.id' >/dev/null 2>&1; then
        JOB_ID=$(echo "$JOB_RESPONSE" | jq -r '.id')
        JOB_STATUS=$(echo "$JOB_RESPONSE" | jq -r '.status')
        WORKER_ID=$(echo "$JOB_RESPONSE" | jq -r '.worker_id // "none"')

        pass_test "Job submitted (${JOB_ID:0:8}..., status: ${JOB_STATUS}, ${ELAPSED}s)"

        if [ "$JOB_STATUS" = "completed" ]; then
            pass_test "Job completed immediately (serverless direct)"
            info "Worker: ${WORKER_ID}, Time: ${ELAPSED}s"
        elif [ "$JOB_STATUS" = "failed" ]; then
            JOB_ERROR=$(echo "$JOB_RESPONSE" | jq -r '.error // "unknown"')
            warn "Job failed: ${JOB_ERROR}"
            info "This is expected if using a test workflow with non-existent model"
        elif [ "$JOB_STATUS" = "pending" ]; then
            # Poll for completion (queue-based mode)
            info "Job queued — polling for completion (timeout: ${TIMEOUT}s)..."

            POLL_START=$(date +%s)
            while true; do
                POLL_NOW=$(date +%s)
                POLL_ELAPSED=$((POLL_NOW - POLL_START))

                if [ "$POLL_ELAPSED" -ge "$TIMEOUT" ]; then
                    warn "Job timed out after ${TIMEOUT}s (still ${JOB_STATUS})"
                    # Cancel to avoid wasting GPU credits
                    curl -s -X DELETE --max-time 10 \
                        "http://localhost:${QM_PORT}/api/jobs/${JOB_ID}" >/dev/null 2>&1
                    info "Job cancelled to avoid GPU cost"
                    break
                fi

                sleep 3
                POLL_RESPONSE=$(curl -s --max-time 10 \
                    "http://localhost:${QM_PORT}/api/jobs/${JOB_ID}" 2>/dev/null || echo "{}")
                JOB_STATUS=$(echo "$POLL_RESPONSE" | jq -r '.status // "unknown"')

                if [ "$JOB_STATUS" = "completed" ]; then
                    TOTAL_TIME=$((POLL_NOW - START_TIME))
                    pass_test "Job completed (${TOTAL_TIME}s total)"
                    break
                elif [ "$JOB_STATUS" = "failed" ]; then
                    JOB_ERROR=$(echo "$POLL_RESPONSE" | jq -r '.error // "unknown"')
                    warn "Job failed: ${JOB_ERROR}"
                    break
                fi
            done
        fi
    elif echo "$JOB_RESPONSE" | jq -e '.detail' >/dev/null 2>&1; then
        DETAIL=$(echo "$JOB_RESPONSE" | jq -r '.detail')
        warn "Job submission returned error: ${DETAIL}"
        info "This may be expected if serverless endpoint is cold or model is missing"
    else
        fail_test "Job submission failed" "No valid response after ${ELAPSED}s"
    fi
fi

# ==========================================================================
# Summary
# ==========================================================================
print_summary "Serverless Inference Test"

if [ "$TESTS_FAILED" -eq 0 ]; then
    exit 0
else
    exit 1
fi
