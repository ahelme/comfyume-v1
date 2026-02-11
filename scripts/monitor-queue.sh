#!/bin/bash
# Monitor queue status during load testing (Issue #19)
# Displays real-time queue statistics and container health

QUEUE_MANAGER_URL="${QUEUE_MANAGER_URL:-http://localhost:3000}"
REFRESH_INTERVAL="${REFRESH_INTERVAL:-2}"

# Clear screen and show header
clear
echo "════════════════════════════════════════════════════════════════"
echo "  ComfyUme Queue Monitor (Issue #19)"
echo "  Press Ctrl+C to exit"
echo "════════════════════════════════════════════════════════════════"
echo ""

while true; do
    # Move cursor to top (preserve header)
    tput cup 5 0

    # Get queue status
    QUEUE_STATUS=$(curl -sf "$QUEUE_MANAGER_URL/api/queue/status" || echo "{}")

    # Parse queue statistics
    QUEUE_DEPTH=$(echo "$QUEUE_STATUS" | jq -r '.queue_depth // "N/A"')
    PENDING=$(echo "$QUEUE_STATUS" | jq -r '.pending_jobs // "N/A"')
    RUNNING=$(echo "$QUEUE_STATUS" | jq -r '.running_jobs // "N/A"')
    COMPLETED=$(echo "$QUEUE_STATUS" | jq -r '.completed_jobs // "N/A"')
    FAILED=$(echo "$QUEUE_STATUS" | jq -r '.failed_jobs // "N/A"')

    # Get worker count
    WORKER_COUNT=$(docker ps --filter "name=comfy-worker" --format "{{.Names}}" 2>/dev/null | wc -l)

    # Display statistics
    echo "Queue Statistics (refreshing every ${REFRESH_INTERVAL}s):"
    echo "────────────────────────────────────────────────────────────────"
    printf "  Queue Depth:     %s\n" "$QUEUE_DEPTH"
    printf "  Pending Jobs:    %s\n" "$PENDING"
    printf "  Running Jobs:    %s\n" "$RUNNING"
    printf "  Completed Jobs:  %s\n" "$COMPLETED"
    printf "  Failed Jobs:     %s\n" "$FAILED"
    echo ""
    echo "Workers:"
    echo "────────────────────────────────────────────────────────────────"
    printf "  Active Workers:  %s\n" "$WORKER_COUNT"
    echo ""

    # Show running containers
    echo "Container Status:"
    echo "────────────────────────────────────────────────────────────────"
    docker ps --filter "name=comfy-" --format "table {{.Names}}\t{{.Status}}" 2>/dev/null || echo "  No containers running"
    echo ""
    echo "────────────────────────────────────────────────────────────────"
    echo "Last update: $(date '+%Y-%m-%d %H:%M:%S')"

    # Clear remaining lines
    tput ed

    sleep $REFRESH_INTERVAL
done
