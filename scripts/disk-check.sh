#!/bin/bash
# Disk Space Monitor - alerts on volumes over threshold
# Usage: ./disk-check.sh [--warn 70] [--critical 90] [--block]
# --block: exit 1 if any volume exceeds critical threshold (use before large operations)

WARN_THRESHOLD=70
CRITICAL_THRESHOLD=90
BLOCK_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --warn) WARN_THRESHOLD="$2"; shift 2 ;;
        --critical) CRITICAL_THRESHOLD="$2"; shift 2 ;;
        --block) BLOCK_MODE=true; shift ;;
        *) shift ;;
    esac
done

CRITICAL_FOUND=false

echo "=== Disk Space Check (warn: ${WARN_THRESHOLD}%, critical: ${CRITICAL_THRESHOLD}%) ==="

# Get all mounted filesystems, skip tmpfs/devtmpfs/squashfs
df -h | grep -vE '^Filesystem|tmpfs|devtmpfs|squashfs|overlay' | while read -r line; do
    USAGE=$(echo "$line" | awk '{print $5}' | tr -d '%')
    MOUNT=$(echo "$line" | awk '{print $6}')
    SIZE=$(echo "$line" | awk '{print $2}')
    AVAIL=$(echo "$line" | awk '{print $4}')

    # Skip if not a number
    [[ ! "$USAGE" =~ ^[0-9]+$ ]] && continue

    if [ "$USAGE" -ge "$CRITICAL_THRESHOLD" ]; then
        echo "🚨 CRITICAL: $MOUNT at ${USAGE}% (${AVAIL} free of ${SIZE})"
        echo "true" > /tmp/.disk_critical
    elif [ "$USAGE" -ge "$WARN_THRESHOLD" ]; then
        echo "⚠️  WARNING: $MOUNT at ${USAGE}% (${AVAIL} free of ${SIZE})"
    else
        echo "✅ OK: $MOUNT at ${USAGE}% (${AVAIL} free of ${SIZE})"
    fi
done

# Check if critical was found (subshell workaround)
if [ -f /tmp/.disk_critical ]; then
    rm -f /tmp/.disk_critical
    CRITICAL_FOUND=true
fi

if [ "$CRITICAL_FOUND" = true ] && [ "$BLOCK_MODE" = true ]; then
    echo ""
    echo "❌ BLOCKING: Critical disk usage detected. Free space before proceeding."
    exit 1
fi

echo "=== End Disk Check ==="
