#!/bin/bash
#
# Connectivity Test for ComfyuME
# Validates network paths between all services, containers, and external domain
#
# Usage: ./scripts/test-connectivity.sh
#

set -e

# Source shared helpers
source "$(dirname "$0")/test-helpers.sh"

# Load environment
if ! load_env; then
    exit 1
fi

QM_PORT="${QUEUE_MANAGER_PORT:-3000}"

echo "════════════════════════════════════════════════════════════"
echo "  ComfyuME Connectivity Test"
echo "════════════════════════════════════════════════════════════"
echo ""

# ==========================================================================
# 1. Redis Connectivity
# ==========================================================================
section_header "1" "Redis Connectivity"

# Redis from host (via docker compose)
if docker compose exec -T redis redis-cli --no-auth-warning -a "$REDIS_PASSWORD" ping 2>/dev/null | grep -q "PONG"; then
    pass_test "Redis from host (docker compose exec)"
else
    fail_test "Redis from host" "Cannot reach Redis via docker compose exec"
fi

# Redis from host via TCP (localhost binding)
REDIS_BIND="${REDIS_BIND_IP:-127.0.0.1}"
if command -v redis-cli &>/dev/null; then
    if redis-cli -h "$REDIS_BIND" -p 6379 -a "$REDIS_PASSWORD" --no-auth-warning ping 2>/dev/null | grep -q "PONG"; then
        pass_test "Redis from host TCP (${REDIS_BIND}:6379)"
    else
        warn "Redis from host TCP (${REDIS_BIND}:6379)" "May not be exposed to host"
    fi
else
    info "redis-cli not installed on host — skipping host TCP test"
fi

# Redis from queue-manager container
QM_REDIS_TEST=$(docker compose exec -T queue-manager python3 -c "
import redis, os
r = redis.Redis(
    host=os.environ.get('REDIS_HOST', 'redis'),
    port=int(os.environ.get('REDIS_PORT', 6379)),
    password=os.environ.get('REDIS_PASSWORD', ''),
    socket_timeout=5
)
print('PONG' if r.ping() else 'FAIL')
" 2>/dev/null || echo "ERROR")

if echo "$QM_REDIS_TEST" | grep -q "PONG"; then
    pass_test "Redis from queue-manager container"
else
    fail_test "Redis from queue-manager container" "QM cannot reach Redis"
fi

# ==========================================================================
# 2. Queue Manager Connectivity
# ==========================================================================
section_header "2" "Queue Manager Connectivity"

# QM from host
if check_http "http://localhost:${QM_PORT}/health" "200"; then
    pass_test "Queue Manager from host (localhost:${QM_PORT})"
else
    fail_test "Queue Manager from host" "Got HTTP ${CHECK_HTTP_CODE}"
fi

# QM from user001 frontend container (via Docker network)
if container_running "comfy-user001"; then
    QM_FROM_USER=$(docker compose exec -T user001 curl -s -o /dev/null -w "%{http_code}" --max-time 5 \
        "http://queue-manager:3000/health" 2>/dev/null || echo "000")
    if [ "$QM_FROM_USER" = "200" ]; then
        pass_test "Queue Manager from user001 container (Docker network)"
    else
        fail_test "Queue Manager from user001" "Got HTTP ${QM_FROM_USER}"
    fi
else
    info "user001 container not running — skipping container-to-QM test"
fi

# QM from admin container
if container_running "comfy-admin"; then
    QM_FROM_ADMIN=$(docker compose exec -T admin curl -s -o /dev/null -w "%{http_code}" --max-time 5 \
        "http://queue-manager:3000/health" 2>/dev/null || echo "000")
    if [ "$QM_FROM_ADMIN" = "200" ]; then
        pass_test "Queue Manager from admin container"
    else
        fail_test "Queue Manager from admin" "Got HTTP ${QM_FROM_ADMIN}"
    fi
else
    info "admin container not running — skipping admin-to-QM test"
fi

# ==========================================================================
# 3. Nginx Reverse Proxy Paths
# ==========================================================================
section_header "3" "Nginx Reverse Proxy Paths"

# Test from localhost (bypasses DNS)
# Admin route
ADMIN_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 -k "https://localhost/admin" 2>/dev/null \
    || curl -s -o /dev/null -w "%{http_code}" --max-time 10 "http://localhost/admin" 2>/dev/null \
    || echo "000")
if [ "$ADMIN_CODE" = "200" ] || [ "$ADMIN_CODE" = "401" ] || [ "$ADMIN_CODE" = "301" ]; then
    pass_test "Nginx → admin (HTTP ${ADMIN_CODE})"
else
    fail_test "Nginx → admin" "Got HTTP ${ADMIN_CODE}"
fi

# API route
API_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 -k "https://localhost/api/queue/status" 2>/dev/null \
    || curl -s -o /dev/null -w "%{http_code}" --max-time 10 "http://localhost/api/queue/status" 2>/dev/null \
    || echo "000")
if [ "$API_CODE" = "200" ]; then
    pass_test "Nginx → API (HTTP ${API_CODE})"
else
    fail_test "Nginx → API" "Got HTTP ${API_CODE}"
fi

# Health endpoint
HEALTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 -k "https://localhost/health" 2>/dev/null \
    || curl -s -o /dev/null -w "%{http_code}" --max-time 10 "http://localhost/health" 2>/dev/null \
    || echo "000")
if [ "$HEALTH_CODE" = "200" ]; then
    pass_test "Nginx → health (HTTP ${HEALTH_CODE})"
else
    warn "Nginx → health" "Got HTTP ${HEALTH_CODE}"
fi

# User routes — test user001 and user020 (first and last)
for user_num in 1 20; do
    USER_ID=$(printf "user%03d" "$user_num")
    USER_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 -k "https://localhost/${USER_ID}/" 2>/dev/null \
        || curl -s -o /dev/null -w "%{http_code}" --max-time 10 "http://localhost/${USER_ID}/" 2>/dev/null \
        || echo "000")
    if [ "$USER_CODE" = "200" ] || [ "$USER_CODE" = "401" ] || [ "$USER_CODE" = "301" ]; then
        pass_test "Nginx → /${USER_ID}/ (HTTP ${USER_CODE})"
    else
        warn "Nginx → /${USER_ID}/" "Got HTTP ${USER_CODE}"
    fi
done

# ==========================================================================
# 4. External Domain & HTTPS
# ==========================================================================
section_header "4" "External Domain & HTTPS"

DOMAIN_VAL="${DOMAIN:-}"
if [ -n "$DOMAIN_VAL" ] && [ "$DOMAIN_VAL" != "workshop.example.com" ]; then
    # DNS resolution
    if command -v dig &>/dev/null; then
        RESOLVED_IP=$(dig +short "$DOMAIN_VAL" 2>/dev/null | head -1)
        if [ -n "$RESOLVED_IP" ]; then
            pass_test "DNS resolves: ${DOMAIN_VAL} → ${RESOLVED_IP}"
        else
            fail_test "DNS resolution failed for ${DOMAIN_VAL}"
        fi
    elif command -v host &>/dev/null; then
        if host "$DOMAIN_VAL" >/dev/null 2>&1; then
            pass_test "DNS resolves: ${DOMAIN_VAL}"
        else
            fail_test "DNS resolution failed for ${DOMAIN_VAL}"
        fi
    else
        info "No DNS tools (dig/host) — skipping DNS check"
    fi

    # HTTPS reachability
    HTTPS_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 -k "https://${DOMAIN_VAL}/" 2>/dev/null || echo "000")
    if [ "$HTTPS_CODE" != "000" ]; then
        pass_test "HTTPS reachable: https://${DOMAIN_VAL}/ (HTTP ${HTTPS_CODE})"
    else
        fail_test "HTTPS unreachable: https://${DOMAIN_VAL}/"
    fi

    # SSL certificate validation
    if command -v openssl &>/dev/null; then
        # Certificate chain
        CERT_OUTPUT=$(echo | openssl s_client -servername "$DOMAIN_VAL" -connect "${DOMAIN_VAL}:443" 2>/dev/null)
        CERT_VERIFY=$(echo "$CERT_OUTPUT" | grep "Verify return code" | head -1)

        if echo "$CERT_VERIFY" | grep -q "0 (ok)"; then
            pass_test "SSL certificate chain valid"
        elif [ -n "$CERT_VERIFY" ]; then
            warn "SSL certificate chain" "$(echo "$CERT_VERIFY" | sed 's/.*Verify return code: //')"
        else
            warn "Could not verify SSL certificate chain"
        fi

        # Certificate expiry
        CERT_EXPIRY=$(echo "$CERT_OUTPUT" | openssl x509 -noout -enddate 2>/dev/null | sed 's/notAfter=//')
        if [ -n "$CERT_EXPIRY" ]; then
            EXPIRY_EPOCH=$(date -d "$CERT_EXPIRY" +%s 2>/dev/null || echo "0")
            NOW_EPOCH=$(date +%s)
            if [ "$EXPIRY_EPOCH" -gt 0 ]; then
                DAYS_LEFT=$(( (EXPIRY_EPOCH - NOW_EPOCH) / 86400 ))
                if [ "$DAYS_LEFT" -gt 30 ]; then
                    pass_test "SSL cert expires in ${DAYS_LEFT} days (${CERT_EXPIRY})"
                elif [ "$DAYS_LEFT" -gt 0 ]; then
                    warn "SSL cert expires in ${DAYS_LEFT} days" "${CERT_EXPIRY}"
                else
                    fail_test "SSL cert expired" "${CERT_EXPIRY}"
                fi
            fi
        fi

        # Certificate CN/SAN matches domain
        CERT_SUBJECT=$(echo "$CERT_OUTPUT" | openssl x509 -noout -subject 2>/dev/null | sed 's/.*CN *= *//')
        CERT_SAN=$(echo "$CERT_OUTPUT" | openssl x509 -noout -ext subjectAltName 2>/dev/null || echo "")
        if echo "$CERT_SUBJECT $CERT_SAN" | grep -qi "$DOMAIN_VAL"; then
            pass_test "SSL cert matches domain (CN/SAN includes ${DOMAIN_VAL})"
        else
            warn "SSL cert may not match domain" "CN=${CERT_SUBJECT}"
        fi
    else
        info "openssl not available — skipping SSL validation"
    fi
else
    info "DOMAIN not set or is example — skipping external checks"
fi

# ==========================================================================
# 5. Docker Network
# ==========================================================================
section_header "5" "Docker Network"

# Check comfy-network exists
NETWORK_EXISTS=$(docker network ls --format '{{.Name}}' 2>/dev/null | grep -c "comfy-network" || echo "0")
if [ "$NETWORK_EXISTS" -gt 0 ]; then
    pass_test "Docker network 'comfy-network' exists"

    # Count containers on the network
    NETWORK_CONTAINERS=$(docker network inspect comfy-network --format '{{range .Containers}}{{.Name}} {{end}}' 2>/dev/null | wc -w || echo "0")
    if [ "$NETWORK_CONTAINERS" -gt 0 ]; then
        pass_test "Containers on comfy-network: ${NETWORK_CONTAINERS}"
    else
        warn "No containers on comfy-network"
    fi
else
    fail_test "Docker network 'comfy-network' not found" "Run: docker compose up -d"
fi

# Check for containers NOT on the network (potential isolation issues)
ALL_COMFY=$(docker ps --format '{{.Names}}' 2>/dev/null | grep "^comfy-" | wc -l || echo "0")
if [ "$ALL_COMFY" -gt 0 ] && [ "$NETWORK_CONTAINERS" -gt 0 ]; then
    if [ "$ALL_COMFY" -le "$NETWORK_CONTAINERS" ]; then
        pass_test "All comfy containers on shared network"
    else
        warn "Some comfy containers may not be on comfy-network (${ALL_COMFY} running, ${NETWORK_CONTAINERS} on network)"
    fi
fi

# ==========================================================================
# Summary
# ==========================================================================
print_summary "Connectivity Test"

if [ "$TESTS_FAILED" -eq 0 ]; then
    exit 0
else
    exit 1
fi
