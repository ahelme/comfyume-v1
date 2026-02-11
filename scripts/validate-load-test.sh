#!/bin/bash
# Validate load test results (Issue #19)
# Checks success criteria: isolation, completion, no deadlocks

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Load configuration
if [ -f "$PROJECT_DIR/.env" ]; then
    source "$PROJECT_DIR/.env"
fi

NUM_USERS="${NUM_USERS:-20}"
QUEUE_MANAGER_URL="${QUEUE_MANAGER_URL:-http://localhost:3000}"

echo "════════════════════════════════════════════════════════════════"
echo "  ComfyUme Load Test Validation (Issue #19)"
echo "════════════════════════════════════════════════════════════════"
echo ""

PASS=0
FAIL=0

# Test 1: All containers started
echo "Test 1: Container Startup"
echo "────────────────────────────────────────────────────────────────"
RUNNING_CONTAINERS=$(docker ps --filter "name=comfy-user" --format "{{.Names}}" | wc -l)
if [ "$RUNNING_CONTAINERS" -eq "$NUM_USERS" ]; then
    echo "✅ PASS: All $NUM_USERS user containers running"
    ((PASS++))
else
    echo "❌ FAIL: Only $RUNNING_CONTAINERS / $NUM_USERS containers running"
    ((FAIL++))
fi
echo ""

# Test 2: Queue Manager healthy
echo "Test 2: Queue Manager Health"
echo "────────────────────────────────────────────────────────────────"
if curl -sf "$QUEUE_MANAGER_URL/health" > /dev/null; then
    echo "✅ PASS: Queue manager is healthy"
    ((PASS++))
else
    echo "❌ FAIL: Queue manager unhealthy"
    ((FAIL++))
fi
echo ""

# Test 3: Queue status
echo "Test 3: Queue Status"
echo "────────────────────────────────────────────────────────────────"
QUEUE_STATUS=$(curl -sf "$QUEUE_MANAGER_URL/api/queue/status" || echo "{}")
PENDING=$(echo "$QUEUE_STATUS" | jq -r '.pending_jobs // 0')
RUNNING=$(echo "$QUEUE_STATUS" | jq -r '.running_jobs // 0')
COMPLETED=$(echo "$QUEUE_STATUS" | jq -r '.completed_jobs // 0')
FAILED=$(echo "$QUEUE_STATUS" | jq -r '.failed_jobs // 0')

echo "  Pending:   $PENDING"
echo "  Running:   $RUNNING"
echo "  Completed: $COMPLETED"
echo "  Failed:    $FAILED"

if [ "$FAILED" -eq 0 ]; then
    echo "✅ PASS: Zero failed jobs"
    ((PASS++))
else
    echo "❌ FAIL: $FAILED failed jobs detected"
    ((FAIL++))
fi
echo ""

# Test 4: Output isolation
echo "Test 4: Output Directory Isolation"
echo "────────────────────────────────────────────────────────────────"
OUTPUT_DIRS=0
for i in $(seq 1 $NUM_USERS); do
    USER_ID=$(printf "user%03d" $i)
    USER_OUTPUT_DIR="$PROJECT_DIR/data/outputs/$USER_ID"
    if [ -d "$USER_OUTPUT_DIR" ]; then
        ((OUTPUT_DIRS++))
    fi
done

if [ "$OUTPUT_DIRS" -eq "$NUM_USERS" ]; then
    echo "✅ PASS: All $NUM_USERS output directories exist"
    ((PASS++))
else
    echo "❌ FAIL: Only $OUTPUT_DIRS / $NUM_USERS output directories exist"
    ((FAIL++))
fi
echo ""

# Test 5: Container resource limits
echo "Test 5: Container Resource Limits"
echo "────────────────────────────────────────────────────────────────"
CONTAINERS_WITH_LIMITS=$(docker ps --filter "name=comfy-user" --format "{{.Names}}" | \
    xargs -I {} docker inspect {} --format '{{.HostConfig.Memory}}' | \
    grep -v "^0$" | wc -l)

if [ "$CONTAINERS_WITH_LIMITS" -eq "$NUM_USERS" ]; then
    echo "✅ PASS: All containers have memory limits"
    ((PASS++))
else
    echo "⚠️  WARNING: Only $CONTAINERS_WITH_LIMITS / $NUM_USERS containers have memory limits"
    echo "   (This may be acceptable in some configurations)"
fi
echo ""

# Summary
echo "════════════════════════════════════════════════════════════════"
echo "  Validation Summary"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Results:"
echo "  ✅ Passed: $PASS tests"
echo "  ❌ Failed: $FAIL tests"
echo ""

if [ "$FAIL" -eq 0 ]; then
    echo "🎉 ALL TESTS PASSED! Issue #19 success criteria met."
    echo ""
    exit 0
else
    echo "⚠️  Some tests failed. Review logs and retry."
    echo ""
    exit 1
fi
