#!/bin/bash
# =============================================================================
# cleanup-mello.sh — Remove ComfyuME containers and images from Mello
# =============================================================================
# Mello (comfy.ahelme.net) is no longer the primary app server.
# Production runs on Verda (aiworkshop.art). This script cleans up
# containers and images to prepare Mello for VPS downgrade.
#
# Usage:
#   ./scripts/cleanup-mello.sh              # Dry-run (preview only)
#   ./scripts/cleanup-mello.sh --execute    # Actually remove containers/images
#   ./scripts/cleanup-mello.sh --execute --prune  # Also prune volumes/networks
#
# What remains after cleanup:
#   - Tailscale (100.99.216.71)
#   - Backup scripts (/home/dev/comfymulti-scripts/)
#   - Git repos, SSH, system services
#   - Docker engine (installed but idle)
# =============================================================================

set -euo pipefail

# --- Configuration ---
COMPOSE_PROJECT="comfyume"
CONTAINER_PREFIX="comfy"
IMAGE_PREFIX="comfyume"

# --- Flags ---
EXECUTE=false
PRUNE=false

for arg in "$@"; do
    case "$arg" in
        --execute) EXECUTE=true ;;
        --prune)   PRUNE=true ;;
        --help|-h)
            echo "Usage: $0 [--execute] [--prune]"
            echo ""
            echo "  (no flags)   Dry-run: show what would be removed"
            echo "  --execute    Actually stop and remove containers/images"
            echo "  --prune      Also prune unused Docker volumes and networks"
            exit 0
            ;;
        *)
            echo "Unknown flag: $arg"
            echo "Usage: $0 [--execute] [--prune]"
            exit 1
            ;;
    esac
done

# --- Colors ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()  { echo -e "${BLUE}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
ok()    { echo -e "${GREEN}[OK]${NC} $1"; }
err()   { echo -e "${RED}[ERR]${NC} $1"; }

# --- Header ---
echo ""
echo "============================================="
if $EXECUTE; then
    echo "  ComfyuME Mello Cleanup — EXECUTE MODE"
else
    echo "  ComfyuME Mello Cleanup — DRY RUN"
fi
echo "============================================="
echo ""

# --- Disk space before ---
DISK_BEFORE=$(df -BM / | tail -1 | awk '{print $4}' | tr -d 'M')
info "Disk space available: ${DISK_BEFORE}MB"
echo ""

# --- 1. Find containers ---
echo "--- Containers ---"

RUNNING=$(docker ps --filter "name=${CONTAINER_PREFIX}" --format "{{.Names}}\t{{.Status}}\t{{.Image}}" 2>/dev/null || true)
STOPPED=$(docker ps -a --filter "status=exited" --filter "name=${CONTAINER_PREFIX}" --format "{{.Names}}\t{{.Status}}\t{{.Image}}" 2>/dev/null || true)
ALL_CONTAINERS=$(docker ps -a --filter "name=${CONTAINER_PREFIX}" --format "{{.Names}}" 2>/dev/null || true)

RUNNING_COUNT=$(echo "$RUNNING" | grep -c . 2>/dev/null || echo 0)
TOTAL_COUNT=$(echo "$ALL_CONTAINERS" | grep -c . 2>/dev/null || echo 0)

if [ "$TOTAL_COUNT" -eq 0 ]; then
    ok "No comfy containers found"
else
    info "Found $TOTAL_COUNT container(s) ($RUNNING_COUNT running):"
    echo ""
    if [ -n "$RUNNING" ]; then
        echo "  Running:"
        echo "$RUNNING" | while IFS=$'\t' read -r name status image; do
            echo "    - $name ($image)"
        done
    fi
    if [ -n "$STOPPED" ]; then
        echo "  Stopped:"
        echo "$STOPPED" | while IFS=$'\t' read -r name status image; do
            echo "    - $name"
        done
    fi
fi
echo ""

# --- 2. Find images ---
echo "--- Docker Images ---"

IMAGES=$(docker images --filter "reference=${IMAGE_PREFIX}*" --format "{{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.ID}}" 2>/dev/null || true)
IMAGE_COUNT=$(echo "$IMAGES" | grep -c . 2>/dev/null || echo 0)

if [ "$IMAGE_COUNT" -eq 0 ]; then
    ok "No comfyume images found"
else
    info "Found $IMAGE_COUNT image(s):"
    echo ""
    echo "$IMAGES" | while IFS=$'\t' read -r repo size id; do
        echo "    - $repo ($size)"
    done
fi
echo ""

# --- 3. Find volumes ---
echo "--- Docker Volumes ---"

VOLUMES=$(docker volume ls --filter "name=${COMPOSE_PROJECT}" --format "{{.Name}}" 2>/dev/null || true)
VOLUME_COUNT=$(echo "$VOLUMES" | grep -c . 2>/dev/null || echo 0)

if [ "$VOLUME_COUNT" -eq 0 ]; then
    ok "No comfyume volumes found"
else
    info "Found $VOLUME_COUNT volume(s):"
    echo "$VOLUMES" | while read -r vol; do
        echo "    - $vol"
    done
fi
echo ""

# --- Summary ---
echo "============================================="
echo "  Summary"
echo "============================================="
echo "  Containers to remove: $TOTAL_COUNT"
echo "  Images to remove:     $IMAGE_COUNT"
echo "  Volumes to remove:    $(if $PRUNE; then echo "$VOLUME_COUNT"; else echo "0 (use --prune)"; fi)"
echo "============================================="
echo ""

# --- Dry-run exit ---
if ! $EXECUTE; then
    warn "DRY RUN — no changes made"
    echo "  Run with --execute to perform cleanup"
    echo "  Run with --execute --prune to also remove volumes"
    exit 0
fi

# --- Execute cleanup ---
echo ""
info "Proceeding with cleanup..."
echo ""

# 3a. Stop running containers via compose
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

if [ "$RUNNING_COUNT" -gt 0 ]; then
    info "Stopping containers via docker compose..."
    cd "$PROJECT_DIR"
    docker compose down --remove-orphans 2>/dev/null || true
    ok "Containers stopped"
else
    info "No running containers to stop"
fi

# 3b. Remove any remaining stopped containers
REMAINING=$(docker ps -a --filter "name=${CONTAINER_PREFIX}" --format "{{.Names}}" 2>/dev/null || true)
REMAINING_COUNT=$(echo "$REMAINING" | grep -c . 2>/dev/null || echo 0)

if [ "$REMAINING_COUNT" -gt 0 ]; then
    info "Removing $REMAINING_COUNT remaining container(s)..."
    echo "$REMAINING" | xargs docker rm -f 2>/dev/null || true
    ok "Containers removed"
fi

# 3c. Remove images
if [ "$IMAGE_COUNT" -gt 0 ]; then
    info "Removing $IMAGE_COUNT image(s)..."
    docker images --filter "reference=${IMAGE_PREFIX}*" --format "{{.ID}}" | xargs docker rmi -f 2>/dev/null || true
    ok "Images removed"
fi

# 3d. Prune if requested
if $PRUNE; then
    info "Pruning unused volumes and networks..."
    docker volume prune -f 2>/dev/null || true
    docker network prune -f 2>/dev/null || true
    ok "Pruned unused volumes and networks"
fi

# --- Disk space after ---
echo ""
DISK_AFTER=$(df -BM / | tail -1 | awk '{print $4}' | tr -d 'M')
FREED=$((DISK_AFTER - DISK_BEFORE))

echo "============================================="
echo "  Cleanup Complete"
echo "============================================="
echo "  Disk before:  ${DISK_BEFORE}MB available"
echo "  Disk after:   ${DISK_AFTER}MB available"
echo "  Freed:        ${FREED}MB"
echo ""
echo "  Mello is now ready for VPS downgrade."
echo "  Remaining: Tailscale, backup scripts, SSH, git repos"
echo "============================================="
