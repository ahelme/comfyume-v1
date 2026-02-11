#!/bin/bash
#
# Integration Test Suite for ComfyuME Multi-User Platform
# Tests all components for the serverless architecture
#
# Usage: ./scripts/test.sh
#
# Architecture: Verda CPU app server + DataCrunch serverless inference
# No local GPU workers — inference via direct HTTP to serverless endpoints
#

set -e

# Source shared helpers
source "$(dirname "$0")/test-helpers.sh"

# Load environment
if ! load_env; then
    exit 1
fi

echo "════════════════════════════════════════════════════════════"
echo "  ComfyuME Integration Tests"
echo "════════════════════════════════════════════════════════════"
echo ""
info "Domain: ${DOMAIN:-not set}"
info "Inference mode: ${INFERENCE_MODE:-local}"
echo ""

# ==========================================================================
# 1. Docker Services
# ==========================================================================
section_header "1" "Docker Services"

# Core services (always required)
CORE_SERVICES=("comfy-redis" "comfy-queue-manager" "comfy-admin")

for service in "${CORE_SERVICES[@]}"; do
    if container_running "$service"; then
        pass_test "Service $service is running"
    else
        fail_test "Service $service is NOT running" "Start with: docker compose up -d"
    fi
done

# Nginx: detect host vs container mode
if [ "${USE_HOST_NGINX:-true}" = "true" ]; then
    if systemctl is-active --quiet nginx 2>/dev/null; then
        pass_test "Host nginx is running"
    else
        fail_test "Host nginx is NOT running" "Start with: sudo systemctl start nginx"
    fi
else
    if container_running "comfy-nginx"; then
        pass_test "Container nginx is running"
    else
        fail_test "Container nginx is NOT running"
    fi
fi

# Frontend container count
FRONTEND_COUNT=$(count_containers "comfy-user")
EXPECTED_USERS="${NUM_USERS:-20}"
if [ "$FRONTEND_COUNT" -ge "$EXPECTED_USERS" ]; then
    pass_test "Frontend containers: ${FRONTEND_COUNT}/${EXPECTED_USERS} running"
elif [ "$FRONTEND_COUNT" -gt 0 ]; then
    warn "Frontend containers: ${FRONTEND_COUNT}/${EXPECTED_USERS} running (some missing)"
else
    fail_test "No frontend containers running" "Run: docker compose up -d"
fi

# ==========================================================================
# 2. Service Health Endpoints
# ==========================================================================
section_header "2" "Service Health"

# Redis health
if docker compose exec -T redis redis-cli --no-auth-warning -a "$REDIS_PASSWORD" ping 2>/dev/null | grep -q "PONG"; then
    pass_test "Redis health check (PONG)"
else
    fail_test "Redis health check" "Redis not responding"
fi

# Queue Manager health — parse JSON fields
QM_PORT="${QUEUE_MANAGER_PORT:-3000}"
QM_HEALTH_JSON=$(curl -s --max-time 10 "http://localhost:${QM_PORT}/health" 2>/dev/null || echo "{}")

if echo "$QM_HEALTH_JSON" | jq -e '.status' >/dev/null 2>&1; then
    QM_STATUS=$(echo "$QM_HEALTH_JSON" | jq -r '.status')
    QM_INFERENCE=$(echo "$QM_HEALTH_JSON" | jq -r '.inference_mode')
    QM_REDIS=$(echo "$QM_HEALTH_JSON" | jq -r '.redis_connected')
    QM_GPU=$(echo "$QM_HEALTH_JSON" | jq -r '.active_gpu')

    if [ "$QM_STATUS" = "healthy" ]; then
        pass_test "Queue Manager health (status: healthy)"
    else
        fail_test "Queue Manager health" "Status: $QM_STATUS"
    fi

    if [ "$QM_REDIS" = "true" ]; then
        pass_test "Queue Manager → Redis connected"
    else
        fail_test "Queue Manager → Redis disconnected"
    fi

    info "Inference mode: ${QM_INFERENCE}, Active GPU: ${QM_GPU}"
else
    fail_test "Queue Manager health endpoint" "No valid JSON from /health"
fi

# Admin Dashboard health
ADMIN_PORT_VAL="${ADMIN_PORT:-8080}"
if check_http "http://localhost:${ADMIN_PORT_VAL}/health" "200"; then
    pass_test "Admin Dashboard health (HTTP 200)"
else
    fail_test "Admin Dashboard health" "Got HTTP ${CHECK_HTTP_CODE}"
fi

# Health dashboard (nginx)
if check_http "http://localhost/health" "200"; then
    pass_test "Health dashboard endpoint (/health)"
else
    warn "Health dashboard endpoint" "Got HTTP ${CHECK_HTTP_CODE}"
fi

# ==========================================================================
# 3. Queue Manager API
# ==========================================================================
section_header "3" "Queue Manager API"

# Queue status endpoint
QUEUE_STATUS=$(curl -s --max-time 10 "http://localhost:${QM_PORT}/api/queue/status" 2>/dev/null || echo "{}")
if echo "$QUEUE_STATUS" | jq -e '.mode' >/dev/null 2>&1; then
    pass_test "Queue status endpoint returns valid JSON"
    info "Queue mode: $(echo "$QUEUE_STATUS" | jq -r '.mode')"
    info "Pending: $(echo "$QUEUE_STATUS" | jq -r '.pending_jobs'), Running: $(echo "$QUEUE_STATUS" | jq -r '.running_jobs')"
else
    fail_test "Queue status endpoint" "Invalid JSON response"
fi

# Job submission + cancel (round-trip test)
TEST_JOB='{"user_id":"test_user","workflow":{"test":"workflow"},"priority":2}'
JOB_SUBMIT=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "$TEST_JOB" \
    --max-time 10 \
    "http://localhost:${QM_PORT}/api/jobs" 2>/dev/null || echo "{}")

if echo "$JOB_SUBMIT" | jq -e '.id' >/dev/null 2>&1; then
    JOB_ID=$(echo "$JOB_SUBMIT" | jq -r '.id')
    pass_test "Job submit endpoint (job: ${JOB_ID:0:8}...)"

    # Test GET /api/jobs/{id}
    JOB_GET=$(curl -s --max-time 10 "http://localhost:${QM_PORT}/api/jobs/${JOB_ID}" 2>/dev/null || echo "{}")
    if echo "$JOB_GET" | jq -e '.id' >/dev/null 2>&1; then
        pass_test "Job get endpoint (GET /api/jobs/{id})"
    else
        fail_test "Job get endpoint" "Could not retrieve job ${JOB_ID:0:8}"
    fi

    # Test GET /api/jobs (list)
    JOBS_LIST=$(curl -s --max-time 10 "http://localhost:${QM_PORT}/api/jobs?user_id=test_user" 2>/dev/null || echo "[]")
    if echo "$JOBS_LIST" | jq -e '.[0].id' >/dev/null 2>&1; then
        pass_test "Job list endpoint (GET /api/jobs)"
    else
        warn "Job list endpoint" "No jobs returned for test_user"
    fi

    # Cancel the test job
    CANCEL_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE \
        --max-time 10 \
        "http://localhost:${QM_PORT}/api/jobs/${JOB_ID}" 2>/dev/null || echo "000")
    if [ "$CANCEL_CODE" = "204" ] || [ "$CANCEL_CODE" = "200" ]; then
        pass_test "Job cancel endpoint (DELETE /api/jobs/{id})"
    else
        warn "Job cancel (HTTP ${CANCEL_CODE})" "Job may have already been processed (serverless mode)"
    fi
else
    # In serverless mode, submit may go directly to inference and complete immediately
    if [ "${INFERENCE_MODE}" = "serverless" ]; then
        if echo "$JOB_SUBMIT" | jq -e '.status' >/dev/null 2>&1; then
            pass_test "Job submit endpoint (serverless — completed immediately)"
        else
            fail_test "Job submit endpoint" "Could not create test job"
        fi
    else
        fail_test "Job submit endpoint" "Could not create test job"
    fi
fi

# ==========================================================================
# 4. Redis Queue Operations
# ==========================================================================
section_header "4" "Redis Queue Operations"

REDIS_EXEC="docker compose exec -T redis redis-cli --no-auth-warning -a $REDIS_PASSWORD"

PENDING_COUNT=$($REDIS_EXEC ZCARD queue:pending 2>/dev/null | tr -d '[:space:]' || echo "error")
RUNNING_COUNT=$($REDIS_EXEC ZCARD queue:running 2>/dev/null | tr -d '[:space:]' || echo "error")
COMPLETED_COUNT=$($REDIS_EXEC ZCARD queue:completed 2>/dev/null | tr -d '[:space:]' || echo "error")

if [ "$PENDING_COUNT" != "error" ]; then
    pass_test "Redis queue operations accessible"
    info "Pending: ${PENDING_COUNT}, Running: ${RUNNING_COUNT}, Completed: ${COMPLETED_COUNT}"
else
    fail_test "Redis queue operations" "Could not read queue stats"
fi

# ==========================================================================
# 5. Nginx Routing
# ==========================================================================
section_header "5" "Nginx Routing"

# Determine base URL — use DOMAIN if set and resolvable, otherwise localhost
BASE_URL=""
if [ -n "${DOMAIN}" ] && [ "${DOMAIN}" != "workshop.example.com" ]; then
    # Try HTTPS first
    if check_https "https://${DOMAIN}/health" "200"; then
        BASE_URL="https://${DOMAIN}"
    elif check_http "http://${DOMAIN}/health" "200"; then
        BASE_URL="http://${DOMAIN}"
    fi
fi
if [ -z "$BASE_URL" ]; then
    # Fall back to localhost (try HTTPS then HTTP)
    if check_https "https://localhost/health" "200"; then
        BASE_URL="https://localhost"
    else
        BASE_URL="http://localhost"
    fi
fi
info "Testing routes via: ${BASE_URL}"

# Admin route — may require auth (401 = route exists)
ADMIN_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 -k "${BASE_URL}/admin" 2>/dev/null || echo "000")
if [ "$ADMIN_CODE" = "200" ] || [ "$ADMIN_CODE" = "301" ] || [ "$ADMIN_CODE" = "302" ]; then
    pass_test "Nginx admin route (/admin → HTTP ${ADMIN_CODE})"
elif [ "$ADMIN_CODE" = "401" ]; then
    pass_test "Nginx admin route (/admin → 401, auth required)"
else
    fail_test "Nginx admin route" "Got HTTP ${ADMIN_CODE}"
fi

# API route
API_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 -k "${BASE_URL}/api/queue/status" 2>/dev/null || echo "000")
if [ "$API_CODE" = "200" ]; then
    pass_test "Nginx API route (/api/queue/status)"
else
    fail_test "Nginx API route" "Got HTTP ${API_CODE}"
fi

# User route (user001)
USER_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 -k "${BASE_URL}/user001/" 2>/dev/null || echo "000")
if [ "$USER_CODE" = "200" ] || [ "$USER_CODE" = "301" ] || [ "$USER_CODE" = "302" ]; then
    pass_test "Nginx user route (/user001/ → HTTP ${USER_CODE})"
elif [ "$USER_CODE" = "401" ]; then
    pass_test "Nginx user route (/user001/ → 401, auth required)"
else
    warn "Nginx user route" "Got HTTP ${USER_CODE} (frontends may not be started)"
fi

# ==========================================================================
# 6. Storage & Volumes
# ==========================================================================
section_header "6" "Storage & Volumes"

# Required directories
REQUIRED_DIRS=("data/models/shared" "data/outputs" "data/inputs" "data/workflows")
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$PROJECT_DIR/$dir" ]; then
        pass_test "Directory exists: $dir"
    else
        fail_test "Directory missing: $dir"
    fi
done

# Workflow templates
WORKFLOW_DIR="$PROJECT_DIR/data/workflows"
if [ -d "$WORKFLOW_DIR" ]; then
    WORKFLOW_COUNT=$(find "$WORKFLOW_DIR" -name "*.json" -type f 2>/dev/null | wc -l)
    if [ "$WORKFLOW_COUNT" -gt 0 ]; then
        pass_test "Workflow templates: ${WORKFLOW_COUNT} found"
    else
        warn "No workflow templates in data/workflows/"
    fi
fi

# Model subdirectories
MODEL_SUBDIRS=("checkpoints" "text_encoders" "vae" "loras" "latent_upscale_models")
MODELS_BASE="$PROJECT_DIR/data/models/shared"
MODEL_DIRS_FOUND=0
for subdir in "${MODEL_SUBDIRS[@]}"; do
    if [ -d "$MODELS_BASE/$subdir" ]; then
        MODEL_DIRS_FOUND=$((MODEL_DIRS_FOUND + 1))
    fi
done
if [ "$MODEL_DIRS_FOUND" -eq "${#MODEL_SUBDIRS[@]}" ]; then
    pass_test "Model subdirectories: all ${#MODEL_SUBDIRS[@]} present"
elif [ "$MODEL_DIRS_FOUND" -gt 0 ]; then
    warn "Model subdirectories: ${MODEL_DIRS_FOUND}/${#MODEL_SUBDIRS[@]} present"
else
    warn "No model subdirectories found (expected on inference server, not app server)"
fi

# ==========================================================================
# 7. Serverless Inference
# ==========================================================================
section_header "7" "Serverless Inference"

if [ "${INFERENCE_MODE}" = "serverless" ]; then
    pass_test "INFERENCE_MODE=serverless"

    # Check SERVERLESS_ACTIVE
    if [ -n "${SERVERLESS_ACTIVE}" ] && [ "${SERVERLESS_ACTIVE}" != "default" ]; then
        pass_test "SERVERLESS_ACTIVE=${SERVERLESS_ACTIVE}"
    elif [ -n "${SERVERLESS_ENDPOINT}" ]; then
        pass_test "SERVERLESS_ENDPOINT is set (default mode)"
    else
        fail_test "No serverless endpoint configured" "Set SERVERLESS_ACTIVE or SERVERLESS_ENDPOINT"
    fi

    # Check API key
    if [ -n "${SERVERLESS_API_KEY}" ]; then
        pass_test "SERVERLESS_API_KEY is configured"
    else
        fail_test "SERVERLESS_API_KEY not set" "Required for serverless auth"
    fi

    # Check endpoint reachability via QM health
    if [ -n "$QM_HEALTH_JSON" ]; then
        ENDPOINT_NAME=$(echo "$QM_HEALTH_JSON" | jq -r '.serverless_endpoint // empty')
        if [ -n "$ENDPOINT_NAME" ]; then
            pass_test "Serverless endpoint visible in health: ${ENDPOINT_NAME}"
        else
            warn "Serverless endpoint not reported in QM health"
        fi
    fi
else
    info "Inference mode is '${INFERENCE_MODE:-local}' (not serverless)"
    info "Skipping serverless-specific checks"
    info "Run ./scripts/test-serverless.sh for serverless E2E testing"
fi

# ==========================================================================
# 8. Configuration Validation
# ==========================================================================
section_header "8" "Configuration"

# Core required vars
REQUIRED_VARS=("REDIS_PASSWORD" "DOMAIN" "QUEUE_MODE")
for var in "${REQUIRED_VARS[@]}"; do
    if [ -n "${!var}" ]; then
        pass_test "Env var set: ${var}"
    else
        fail_test "Env var missing: ${var}" "Check .env file"
    fi
done

# Inference mode vars (conditional)
if [ "${INFERENCE_MODE}" = "serverless" ]; then
    SERVERLESS_VARS=("INFERENCE_MODE" "SERVERLESS_API_KEY")
    for var in "${SERVERLESS_VARS[@]}"; do
        if [ -n "${!var}" ]; then
            pass_test "Env var set: ${var}"
        else
            fail_test "Env var missing: ${var}" "Required for serverless mode"
        fi
    done
fi

# Validate queue mode
VALID_MODES=("fifo" "round_robin" "priority")
if [[ " ${VALID_MODES[*]} " =~ " ${QUEUE_MODE} " ]]; then
    pass_test "Queue mode valid: ${QUEUE_MODE}"
else
    fail_test "Queue mode invalid: ${QUEUE_MODE}" "Must be: ${VALID_MODES[*]}"
fi

# ==========================================================================
# 9. Frontend Containers
# ==========================================================================
section_header "9" "Frontend Containers"

# Count running and healthy
RUNNING_FRONTENDS=0
HEALTHY_FRONTENDS=0
UNHEALTHY_LIST=""

for i in $(seq 1 "${NUM_USERS:-20}"); do
    USER_ID=$(printf "user%03d" "$i")
    CONTAINER="comfy-${USER_ID}"

    if container_running "$CONTAINER"; then
        RUNNING_FRONTENDS=$((RUNNING_FRONTENDS + 1))
        if container_healthy "$CONTAINER"; then
            HEALTHY_FRONTENDS=$((HEALTHY_FRONTENDS + 1))
        else
            UNHEALTHY_LIST="${UNHEALTHY_LIST} ${USER_ID}"
        fi
    fi
done

EXPECTED="${NUM_USERS:-20}"
if [ "$RUNNING_FRONTENDS" -eq "$EXPECTED" ]; then
    pass_test "Frontend containers running: ${RUNNING_FRONTENDS}/${EXPECTED}"
elif [ "$RUNNING_FRONTENDS" -gt 0 ]; then
    warn "Frontend containers running: ${RUNNING_FRONTENDS}/${EXPECTED}"
else
    fail_test "No frontend containers running"
fi

if [ "$HEALTHY_FRONTENDS" -eq "$RUNNING_FRONTENDS" ] && [ "$RUNNING_FRONTENDS" -gt 0 ]; then
    pass_test "Frontend containers healthy: ${HEALTHY_FRONTENDS}/${RUNNING_FRONTENDS}"
elif [ "$HEALTHY_FRONTENDS" -gt 0 ]; then
    warn "Frontend containers healthy: ${HEALTHY_FRONTENDS}/${RUNNING_FRONTENDS}"
    if [ -n "$UNHEALTHY_LIST" ]; then
        info "Unhealthy:${UNHEALTHY_LIST}"
    fi
elif [ "$RUNNING_FRONTENDS" -gt 0 ]; then
    warn "No frontend health data (health checks may still be starting)"
fi

# ==========================================================================
# 10. SSL & Domain
# ==========================================================================
section_header "10" "SSL & Domain"

if [ -n "${DOMAIN}" ] && [ "${DOMAIN}" != "workshop.example.com" ]; then
    # HTTPS reachable
    HTTPS_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 -k "https://${DOMAIN}/" 2>/dev/null || echo "000")
    if [ "$HTTPS_CODE" != "000" ]; then
        pass_test "HTTPS reachable: https://${DOMAIN}/ (HTTP ${HTTPS_CODE})"
    else
        fail_test "HTTPS not reachable: https://${DOMAIN}/"
    fi

    # HTTP → HTTPS redirect
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 -L "http://${DOMAIN}/" 2>/dev/null || echo "000")
    REDIRECT_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "http://${DOMAIN}/" 2>/dev/null || echo "000")
    if [ "$REDIRECT_CODE" = "301" ] || [ "$REDIRECT_CODE" = "308" ]; then
        pass_test "HTTP → HTTPS redirect (${REDIRECT_CODE})"
    elif [ "$REDIRECT_CODE" = "200" ]; then
        warn "HTTP returns 200 (no HTTPS redirect)"
    else
        warn "HTTP redirect check" "Got HTTP ${REDIRECT_CODE}"
    fi

    # Certificate expiry (only if openssl available)
    if command -v openssl &>/dev/null; then
        CERT_EXPIRY=$(echo | openssl s_client -servername "${DOMAIN}" -connect "${DOMAIN}:443" 2>/dev/null \
            | openssl x509 -noout -enddate 2>/dev/null \
            | sed 's/notAfter=//')
        if [ -n "$CERT_EXPIRY" ]; then
            EXPIRY_EPOCH=$(date -d "$CERT_EXPIRY" +%s 2>/dev/null || date -j -f "%b %d %T %Y %Z" "$CERT_EXPIRY" +%s 2>/dev/null || echo "0")
            NOW_EPOCH=$(date +%s)
            if [ "$EXPIRY_EPOCH" -gt 0 ]; then
                DAYS_LEFT=$(( (EXPIRY_EPOCH - NOW_EPOCH) / 86400 ))
                if [ "$DAYS_LEFT" -gt 30 ]; then
                    pass_test "SSL certificate valid (${DAYS_LEFT} days remaining)"
                elif [ "$DAYS_LEFT" -gt 0 ]; then
                    warn "SSL certificate expiring soon (${DAYS_LEFT} days remaining)"
                else
                    fail_test "SSL certificate expired" "Expired: ${CERT_EXPIRY}"
                fi
            else
                warn "Could not parse certificate expiry date"
            fi
        else
            warn "Could not retrieve SSL certificate from ${DOMAIN}:443"
        fi
    else
        info "openssl not available — skipping cert expiry check"
    fi
else
    info "DOMAIN not set or is example — skipping SSL/domain checks"
    info "Set DOMAIN in .env to enable these tests"
fi

# ==========================================================================
# Summary
# ==========================================================================
print_summary "Integration Tests"

if [ "$TESTS_FAILED" -eq 0 ]; then
    exit 0
else
    exit 1
fi
