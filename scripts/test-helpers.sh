#!/bin/bash
#
# Shared Test Helper Library for ComfyuME Test Scripts
# Source this file from test scripts: source "$(dirname "$0")/test-helpers.sh"
#

# Prevent double-sourcing
if [ -n "$_TEST_HELPERS_LOADED" ]; then
    return 0
fi
_TEST_HELPERS_LOADED=1

# ============================================================================
# Path Resolution
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[1]:-${BASH_SOURCE[0]}}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# ============================================================================
# Colors
# ============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ============================================================================
# Counters
# ============================================================================

TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0
TESTS_WARNED=0

# ============================================================================
# Output Helpers
# ============================================================================

pass_test() {
    TESTS_PASSED=$((TESTS_PASSED + 1))
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    echo -e "${GREEN}  PASS${NC} - $1"
}

fail_test() {
    TESTS_FAILED=$((TESTS_FAILED + 1))
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    echo -e "${RED}  FAIL${NC} - $1"
    if [ -n "$2" ]; then
        echo -e "${RED}         $2${NC}"
    fi
}

info() {
    echo -e "${BLUE}  info${NC} - $1"
}

warn() {
    TESTS_WARNED=$((TESTS_WARNED + 1))
    echo -e "${YELLOW}  WARN${NC} - $1"
    if [ -n "$2" ]; then
        echo -e "${YELLOW}         $2${NC}"
    fi
}

section_header() {
    local num="$1"
    local title="$2"
    echo ""
    echo -e "${BOLD}${num}. ${title}${NC}"
    echo "────────────────────────────────────────────────────────"
}

print_summary() {
    local script_name="${1:-Test}"
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "  ${script_name} Summary"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo -e "  Total:    ${BLUE}${TESTS_TOTAL}${NC}"
    echo -e "  Passed:   ${GREEN}${TESTS_PASSED}${NC}"
    echo -e "  Failed:   ${RED}${TESTS_FAILED}${NC}"
    echo -e "  Warnings: ${YELLOW}${TESTS_WARNED}${NC}"
    echo ""

    if [ "$TESTS_FAILED" -eq 0 ]; then
        echo -e "${GREEN}  All tests passed.${NC}"
    else
        echo -e "${RED}  ${TESTS_FAILED} test(s) failed.${NC}"
    fi
    echo ""
}

# ============================================================================
# Environment Loading
# ============================================================================

load_env() {
    if [ -f "$PROJECT_DIR/.env" ]; then
        # Export all variables while sourcing
        set -a
        # shellcheck disable=SC1091
        source "$PROJECT_DIR/.env" 2>/dev/null || true
        set +a
        return 0
    else
        echo -e "${RED}  .env file not found at ${PROJECT_DIR}/.env${NC}"
        return 1
    fi
}

# ============================================================================
# HTTP Helpers
# ============================================================================

# check_http URL EXPECTED_CODE [DESCRIPTION]
# Returns 0 if status code matches, 1 otherwise
# Sets CHECK_HTTP_CODE to the actual response code
check_http() {
    local url="$1"
    local expected="$2"
    local desc="${3:-$url}"

    CHECK_HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url" 2>/dev/null || echo "000")

    if [ "$CHECK_HTTP_CODE" = "$expected" ]; then
        return 0
    else
        return 1
    fi
}

# check_https URL EXPECTED_CODE [DESCRIPTION]
# Like check_http but with -k for self-signed certs
check_https() {
    local url="$1"
    local expected="$2"

    CHECK_HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 -k "$url" 2>/dev/null || echo "000")

    if [ "$CHECK_HTTP_CODE" = "$expected" ]; then
        return 0
    else
        return 1
    fi
}

# ============================================================================
# Docker Helpers
# ============================================================================

# Check if a container is running by name
container_running() {
    docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${1}$"
}

# Check if a container is healthy
container_healthy() {
    local health
    health=$(docker inspect --format='{{.State.Health.Status}}' "$1" 2>/dev/null || echo "none")
    [ "$health" = "healthy" ]
}

# Count running containers matching a pattern
count_containers() {
    docker ps --format '{{.Names}}' 2>/dev/null | grep -c "${1}" || echo "0"
}
