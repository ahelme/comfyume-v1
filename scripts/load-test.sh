#!/bin/bash
# Multi-user load testing script for Issue #19
# Submits jobs from all 20 users to test queue management and isolation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Load configuration from .env
if [ -f "$PROJECT_DIR/.env" ]; then
    source "$PROJECT_DIR/.env"
fi

NUM_USERS="${NUM_USERS:-20}"
JOBS_PER_USER="${JOBS_PER_USER:-5}"
TOTAL_JOBS=$((NUM_USERS * JOBS_PER_USER))
QUEUE_MANAGER_URL="${QUEUE_MANAGER_URL:-http://localhost:3000}"
WORKFLOW_NAME="${TEST_WORKFLOW:-example_workflow.json}"

echo "════════════════════════════════════════════════════════════════"
echo "  ComfyUme Multi-User Load Test (Issue #19)"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Configuration:"
echo "  Users:           $NUM_USERS"
echo "  Jobs per user:   $JOBS_PER_USER"
echo "  Total jobs:      $TOTAL_JOBS"
echo "  Queue Manager:   $QUEUE_MANAGER_URL"
echo "  Test workflow:   $WORKFLOW_NAME"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check if queue-manager is healthy
echo "Checking queue-manager health..."
if ! curl -sf "$QUEUE_MANAGER_URL/health" > /dev/null; then
    echo "❌ ERROR: Queue manager is not healthy at $QUEUE_MANAGER_URL"
    echo "   Start services with: docker compose up -d"
    exit 1
fi
echo "✅ Queue manager is healthy"
echo ""

# Check if workflow exists
WORKFLOW_PATH="$PROJECT_DIR/data/workflows/$WORKFLOW_NAME"
if [ ! -f "$WORKFLOW_PATH" ]; then
    echo "❌ ERROR: Workflow not found: $WORKFLOW_PATH"
    exit 1
fi
echo "✅ Workflow found: $WORKFLOW_NAME"
echo ""

# Function to submit a job
submit_job() {
    local user_id=$1
    local job_num=$2

    # Read workflow JSON
    local workflow=$(cat "$WORKFLOW_PATH")

    # Submit job via queue-manager API
    local response=$(curl -sf -X POST "$QUEUE_MANAGER_URL/api/queue/submit" \
        -H "Content-Type: application/json" \
        -d "{
            \"user_id\": \"$user_id\",
            \"workflow\": $workflow,
            \"priority\": 0
        }")

    if [ $? -eq 0 ]; then
        local job_id=$(echo "$response" | jq -r '.job_id // "unknown"')
        echo "  ✅ [$user_id] Job $job_num submitted (ID: $job_id)"
        return 0
    else
        echo "  ❌ [$user_id] Job $job_num FAILED"
        return 1
    fi
}

# Submit jobs
echo "Starting job submission..."
echo "────────────────────────────────────────────────────────────────"
echo ""

START_TIME=$(date +%s)
SUBMITTED_COUNT=0
FAILED_COUNT=0

for i in $(seq 1 $NUM_USERS); do
    USER_ID=$(printf "user%03d" $i)
    echo "[$USER_ID] Submitting $JOBS_PER_USER jobs..."

    for j in $(seq 1 $JOBS_PER_USER); do
        if submit_job "$USER_ID" "$j"; then
            ((SUBMITTED_COUNT++))
        else
            ((FAILED_COUNT++))
        fi
    done

    echo ""
done

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Summary
echo "════════════════════════════════════════════════════════════════"
echo "  Load Test Summary"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Results:"
echo "  ✅ Submitted:  $SUBMITTED_COUNT / $TOTAL_JOBS jobs"
echo "  ❌ Failed:     $FAILED_COUNT / $TOTAL_JOBS jobs"
echo "  ⏱  Duration:   ${DURATION}s"
echo ""
echo "Next steps:"
echo "  1. Monitor queue: ./scripts/monitor-queue.sh"
echo "  2. Check queue manager logs: docker compose logs -f queue-manager"
echo "  3. View outputs: ls -lh data/outputs/user*/"
echo ""
echo "════════════════════════════════════════════════════════════════"
