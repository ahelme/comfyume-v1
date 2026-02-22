#!/bin/sh
set -e

# Cookie-based auth persistence (#45)
# If AUTH_COOKIE_SECRET is set, enable cookie bypass for Basic Auth
AUTH_SECRET="${AUTH_COOKIE_SECRET:-}"
if [ -n "$AUTH_SECRET" ]; then
    echo "Cookie auth enabled (24h session persistence)"
    cat > /etc/nginx/conf.d/auth-cookie-map.conf <<EOF
# Cookie-based auth persistence (#45)
# Valid session cookie bypasses HTTP Basic Auth
map \$cookie_comfyume_session \$auth_bypass {
    "${AUTH_SECRET}" "off";
    default "ComfyuME Workshop";
}
EOF
    cat > /etc/nginx/conf.d/auth-cookie-header.conf <<EOF
# Set session cookie after successful auth (#45)
# HttpOnly: no JS access · Secure: HTTPS only · SameSite=Strict: no CSRF
add_header Set-Cookie "comfyume_session=${AUTH_SECRET}; Path=/; Max-Age=86400; HttpOnly; Secure; SameSite=Strict" always;
EOF
else
    echo "Cookie auth disabled (set AUTH_COOKIE_SECRET to enable)"
    cat > /etc/nginx/conf.d/auth-cookie-map.conf <<EOF
# Cookie auth not configured — standard Basic Auth only
map \$x_unused_cookie_auth \$auth_bypass {
    default "ComfyuME Workshop";
}
EOF
    cat > /etc/nginx/conf.d/auth-cookie-header.conf <<EOF
# Cookie auth not configured — no Set-Cookie header
EOF
fi

# Generate user frontend routing configuration
echo "Generating nginx configuration for ${NUM_USERS:-20} users..."

# No upstream blocks needed — using dynamic resolution with resolver
# This prevents nginx from crashing at startup if user containers aren't
# ready yet. DNS resolution happens at request time instead.
cat > /etc/nginx/conf.d/user-upstreams.conf <<EOF
# Dynamic resolution — no upstream blocks needed
# User containers are resolved at request time via Docker DNS (127.0.0.11)
EOF

# Create URL-encoding preserving maps for userdata API (Issue #54)
# The $request_uri variable contains the raw, un-decoded URI
cat > /etc/nginx/conf.d/user-maps.conf <<EOF
# Maps to preserve URL encoding for ComfyUI userdata API
# Issue #54: POST to /userdata returns 405 through nginx without this
# See: https://github.com/comfyanonymous/ComfyUI/pull/6376
EOF

# Create location blocks for user routing
cat > /etc/nginx/conf.d/user-locations.conf <<EOF
# User frontend locations (generated at runtime)
# Using resolver + variables for dynamic DNS resolution
EOF

# Generate configuration for each user
for i in $(seq 1 ${NUM_USERS:-20}); do
    USER_ID=$(printf "user%03d" $i)

    # Add map for URL encoding preservation
    cat >> /etc/nginx/conf.d/user-maps.conf <<EOF
map \$request_uri \$${USER_ID}_raw_path { ~^/${USER_ID}(/[^\?]*) \$1; default /; }
EOF

    # Add location using resolver + variable for dynamic DNS resolution
    # The set $backend trick makes nginx resolve at request time, not startup
    cat >> /etc/nginx/conf.d/user-locations.conf <<EOF

location /${USER_ID}/ {
    resolver 127.0.0.11 valid=30s;
    set \$backend_${USER_ID} ${USER_ID};
    proxy_pass http://\$backend_${USER_ID}:8188\$${USER_ID}_raw_path\$is_args\$args;
    proxy_http_version 1.1;
    proxy_set_header Upgrade \$http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;

    # WebSocket support
    proxy_read_timeout 86400;
    proxy_send_timeout 86400;
}

# Static workflow serving
location /${USER_ID}/user_workflows/ {
    alias /var/www/workflows/;
    add_header Content-Type application/json;
    add_header Cache-Control "no-cache, must-revalidate";
}
EOF
done

echo "Nginx configuration generated successfully"

# Execute the original nginx entrypoint
exec "$@"
