#!/bin/bash
# Initialize user data directories for all users
# Creates proper directory structure for each user

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
USER_DATA_DIR="$PROJECT_DIR/data/user_data"

# Load NUM_USERS from .env if it exists
if [ -f "$PROJECT_DIR/.env" ]; then
    source "$PROJECT_DIR/.env"
fi
NUM_USERS="${NUM_USERS:-20}"

echo "Initializing user data directories for $NUM_USERS users..."
echo "Base directory: $USER_DATA_DIR"
echo ""

# Create user directories
for i in $(seq 1 $NUM_USERS); do
    USER_ID=$(printf "user%03d" $i)
    USER_DIR="$USER_DATA_DIR/$USER_ID"

    # Create directory structure
    mkdir -p "$USER_DIR/comfyui/custom_nodes"
    mkdir -p "$USER_DIR/default"

    # Copy default custom nodes from frontend
    if [ -d "$PROJECT_DIR/comfyui-frontend/custom_nodes" ]; then
        echo "[$USER_ID] Copying default custom nodes..."
        cp -r "$PROJECT_DIR/comfyui-frontend/custom_nodes/"* "$USER_DIR/comfyui/custom_nodes/" 2>/dev/null || true
    fi

    # Set proper permissions
    chmod -R 755 "$USER_DIR"

    echo "✅ [$USER_ID] Directory initialized"
done

echo ""
echo "✅ All $NUM_USERS user directories initialized!"
echo ""
echo "Directory structure per user:"
echo "  user_data/userXXX/"
echo "  ├── comfyui/"
echo "  │   └── custom_nodes/        # User-specific custom nodes"
echo "  │       ├── default_workflow_loader/"
echo "  │       └── queue_redirect/"
echo "  └── default/                 # User preferences"
echo ""
