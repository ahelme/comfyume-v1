#!/bin/bash
#
# deploy.sh — Git-based deployment to Verda production server
#
# Usage:
#   ./scripts/deploy.sh              # Full deploy: push + pull + rebuild + recreate
#   ./scripts/deploy.sh --pull-only  # Just pull code (no rebuild/recreate)
#   ./scripts/deploy.sh --rebuild    # Pull + rebuild images (no recreate)
#
# Flow: local git push → server git pull → rebuild images → recreate containers
# NO SCP, NO tarballs. Everything goes through git.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VERDA_HOST="root@65.108.33.101"
REMOTE_DIR="/home/dev/comfyume-v1"

# Parse flags
PULL_ONLY=false
REBUILD_ONLY=false
for arg in "$@"; do
    case "$arg" in
        --pull-only) PULL_ONLY=true ;;
        --rebuild)   REBUILD_ONLY=true ;;
    esac
done

echo "=== ComfyuME Deploy (git-based) ==="
echo "Server: $VERDA_HOST:$REMOTE_DIR"
echo ""

# 1. Check for uncommitted changes
echo "--- Step 1: Check local git status ---"
cd "$PROJECT_DIR"
if [ -n "$(git status --porcelain -- ':!.claude/')" ]; then
    echo "ERROR: Uncommitted changes (excluding .claude/):"
    git status --short -- ':!.claude/'
    echo ""
    echo "Commit your changes first. No deploying uncommitted code."
    exit 1
fi
echo "OK: Working tree clean"

# 2. Push to origin
echo ""
echo "--- Step 2: Push to origin ---"
BRANCH=$(git rev-parse --abbrev-ref HEAD)
git push origin "$BRANCH"
echo "OK: Pushed $BRANCH"

# 3. Pull on server
echo ""
echo "--- Step 3: Pull on server ---"
ssh "$VERDA_HOST" "cd $REMOTE_DIR && git pull origin $BRANCH"
echo "OK: Server updated"

if $PULL_ONLY; then
    echo ""
    echo "=== Done (pull only) ==="
    exit 0
fi

# 4. Rebuild images
echo ""
echo "--- Step 4: Rebuild images ---"

echo "Building frontend image..."
ssh "$VERDA_HOST" "cd $REMOTE_DIR && docker build -t comfyume-frontend:v0.11.0 -f comfyui-frontend/Dockerfile . 2>&1 | tail -3"

echo "Building queue-manager..."
ssh "$VERDA_HOST" "cd $REMOTE_DIR && docker compose build queue-manager 2>&1 | tail -3"

echo "OK: Images rebuilt"

if $REBUILD_ONLY; then
    echo ""
    echo "=== Done (rebuild only) ==="
    exit 0
fi

# 5. Recreate containers
echo ""
echo "--- Step 5: Recreate containers ---"
ssh "$VERDA_HOST" "cd $REMOTE_DIR && docker compose --profile container-nginx up -d 2>&1 | grep -E 'Started|Created|Healthy' | tail -10"
echo "Waiting for health checks..."
sleep 15

# 6. Verify health
echo ""
echo "--- Step 6: Health check ---"
HEALTHY=$(ssh "$VERDA_HOST" "docker ps --format '{{.Names}} {{.Status}}' | grep -c healthy")
TOTAL=$(ssh "$VERDA_HOST" "docker ps --format '{{.Names}}' | grep -c comfy")
echo "Containers: $HEALTHY healthy / $TOTAL total"

if [ "$HEALTHY" -lt 22 ]; then
    echo "WARNING: Expected 22+ healthy containers, got $HEALTHY"
    echo "Check with: ssh $VERDA_HOST 'docker ps --format \"table {{.Names}}\t{{.Status}}\" | grep comfy | sort'"
fi

# 7. Show git status on server
echo ""
echo "--- Verification ---"
LOCAL_SHA=$(git rev-parse --short HEAD)
REMOTE_SHA=$(ssh "$VERDA_HOST" "cd $REMOTE_DIR && git rev-parse --short HEAD")
echo "Local:  $LOCAL_SHA"
echo "Server: $REMOTE_SHA"
if [ "$LOCAL_SHA" = "$REMOTE_SHA" ]; then
    echo "OK: In sync"
else
    echo "WARNING: SHA mismatch!"
fi

echo ""
echo "=== Deploy complete ==="
