#!/bin/sh
set -e

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
