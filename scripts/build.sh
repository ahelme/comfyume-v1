#!/bin/bash
set -e

# ComfyUI Workshop Platform - Build Script
# ==========================================

# --- Disk Space Check (fail early if disk critical) ---
if command -v disk-check.sh &> /dev/null; then
    disk-check.sh --block || { echo "❌ ABORTING: Disk space critical. Free space before building."; exit 1; }
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "🔨 Building ComfyUI Workshop Platform..."
echo "=========================================="

# Parse arguments
BUILD_ARGS=""
SERVICE=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-cache) BUILD_ARGS="$BUILD_ARGS --no-cache"; shift ;;
        --pull) BUILD_ARGS="$BUILD_ARGS --pull"; shift ;;
        *) SERVICE="$1"; shift ;;
    esac
done

# Run disk check again right before build (in case something filled up)
if command -v disk-check.sh &> /dev/null; then
    echo "🔍 Final disk check before build..."
    disk-check.sh --block || { echo "❌ ABORTING: Disk space critical."; exit 1; }
fi

if [ -n "$SERVICE" ]; then
    echo "Building: $SERVICE"
    docker compose build $BUILD_ARGS $SERVICE
else
    echo "Building all services..."
    docker compose build $BUILD_ARGS
fi

echo ""
echo "✅ Build complete!"
