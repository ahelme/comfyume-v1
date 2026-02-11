#!/bin/bash
# switch-gpu.sh - Switch between inference modes/GPUs
# Usage: ./scripts/switch-gpu.sh [h200-spot|h200-on-demand|b300-spot|b300-on-demand|local]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

show_usage() {
    echo "Usage: $0 [MODE]"
    echo ""
    echo "Modes:"
    echo "  h200-spot       - H200 SPOT (€0.97/hr + VAT) - Workshop, testing"
    echo "  h200-on-demand  - H200 On-Demand (€2.80/hr + VAT) - Demos"
    echo "  b300-spot       - B300 SPOT (€1.61/hr + VAT) - Cheap 4K"
    echo "  b300-on-demand  - B300 On-Demand (€4.63/hr + VAT) - Premium 4K"
    echo "  local           - Local/Redis workers (no serverless)"
    echo "  status          - Show current mode"
    echo ""
    echo "Examples:"
    echo "  $0 h200-spot        # Workshop with 20 users (cheapest)"
    echo "  $0 b300-on-demand   # Boss demo with 4K video (premium)"
    echo "  $0 status           # Check current mode"
    echo ""
    echo "After switching: docker compose restart queue-manager"
}

show_status() {
    echo -e "${BLUE}Current inference configuration:${NC}"
    echo ""

    if [ -f "$PROJECT_DIR/.env" ]; then
        INFERENCE_MODE=$(grep "^INFERENCE_MODE=" "$PROJECT_DIR/.env" | cut -d'=' -f2)
        SERVERLESS_ACTIVE=$(grep "^SERVERLESS_ACTIVE=" "$PROJECT_DIR/.env" | cut -d'=' -f2)

        echo "  INFERENCE_MODE:    $INFERENCE_MODE"
        echo "  SERVERLESS_ACTIVE: $SERVERLESS_ACTIVE"

        if [ "$INFERENCE_MODE" = "serverless" ]; then
            case "$SERVERLESS_ACTIVE" in
                h200-spot)
                    echo -e "  Active GPU:        ${GREEN}H200 SPOT 141GB (€0.97/hr + VAT)${NC}"
                    echo -e "  Best for:          Workshop, testing, cost-sensitive"
                    ;;
                h200-on-demand)
                    echo -e "  Active GPU:        ${CYAN}H200 On-Demand 141GB (€2.80/hr + VAT)${NC}"
                    echo -e "  Best for:          Important demos, guaranteed availability"
                    ;;
                b300-spot)
                    echo -e "  Active GPU:        ${GREEN}B300 SPOT 288GB (€1.61/hr + VAT)${NC}"
                    echo -e "  Best for:          4K experimentation, cheap 4K"
                    ;;
                b300-on-demand)
                    echo -e "  Active GPU:        ${CYAN}B300 On-Demand 288GB (€4.63/hr + VAT)${NC}"
                    echo -e "  Best for:          Boss demo 4K, critical production"
                    ;;
                *)
                    echo -e "  Active GPU:        ${YELLOW}Default endpoint${NC}"
                    ;;
            esac
        else
            echo -e "  Active GPU:        ${YELLOW}Local/Redis workers${NC}"
        fi
    else
        echo "  .env file not found!"
    fi

    echo ""
    echo "Check live status: curl -s https://comfy.ahelme.net/health | jq '.inference_mode, .active_gpu'"
}

switch_mode() {
    MODE=$1

    case $MODE in
        h200-spot)
            echo -e "${GREEN}Switching to H200 SPOT...${NC}"
            sed -i 's/^INFERENCE_MODE=.*/INFERENCE_MODE=serverless/' "$PROJECT_DIR/.env"
            sed -i 's/^SERVERLESS_ACTIVE=.*/SERVERLESS_ACTIVE=h200-spot/' "$PROJECT_DIR/.env"
            echo "  INFERENCE_MODE=serverless"
            echo "  SERVERLESS_ACTIVE=h200-spot"
            echo -e "  GPU: ${GREEN}H200 SXM5 141GB - €0.97/hr + VAT${NC}"
            echo "  Type: SPOT (can be preempted)"
            echo "  Best for: Workshop (20 users), 720p/1080p, testing"
            ;;
        h200-on-demand)
            echo -e "${CYAN}Switching to H200 On-Demand...${NC}"
            sed -i 's/^INFERENCE_MODE=.*/INFERENCE_MODE=serverless/' "$PROJECT_DIR/.env"
            sed -i 's/^SERVERLESS_ACTIVE=.*/SERVERLESS_ACTIVE=h200-on-demand/' "$PROJECT_DIR/.env"
            echo "  INFERENCE_MODE=serverless"
            echo "  SERVERLESS_ACTIVE=h200-on-demand"
            echo -e "  GPU: ${CYAN}H200 SXM5 141GB - €2.80/hr + VAT${NC}"
            echo "  Type: On-Demand (guaranteed)"
            echo "  Best for: Important demos, time-critical work"
            ;;
        b300-spot)
            echo -e "${GREEN}Switching to B300 SPOT...${NC}"
            sed -i 's/^INFERENCE_MODE=.*/INFERENCE_MODE=serverless/' "$PROJECT_DIR/.env"
            sed -i 's/^SERVERLESS_ACTIVE=.*/SERVERLESS_ACTIVE=b300-spot/' "$PROJECT_DIR/.env"
            echo "  INFERENCE_MODE=serverless"
            echo "  SERVERLESS_ACTIVE=b300-spot"
            echo -e "  GPU: ${GREEN}B300 SXM6 288GB - €1.61/hr + VAT${NC}"
            echo "  Type: SPOT (can be preempted)"
            echo "  Best for: 4K experimentation, cheap 4K, long video tests"
            ;;
        b300-on-demand)
            echo -e "${CYAN}Switching to B300 On-Demand...${NC}"
            sed -i 's/^INFERENCE_MODE=.*/INFERENCE_MODE=serverless/' "$PROJECT_DIR/.env"
            sed -i 's/^SERVERLESS_ACTIVE=.*/SERVERLESS_ACTIVE=b300-on-demand/' "$PROJECT_DIR/.env"
            echo "  INFERENCE_MODE=serverless"
            echo "  SERVERLESS_ACTIVE=b300-on-demand"
            echo -e "  GPU: ${CYAN}B300 SXM6 288GB - €4.63/hr + VAT${NC}"
            echo "  Type: On-Demand (guaranteed)"
            echo "  Best for: Boss demo 4K, critical 4K production, native 4K @ 3+ min"
            ;;
        local)
            echo -e "${YELLOW}Switching to local/redis mode...${NC}"
            sed -i 's/^INFERENCE_MODE=.*/INFERENCE_MODE=local/' "$PROJECT_DIR/.env"
            sed -i 's/^SERVERLESS_ACTIVE=.*/SERVERLESS_ACTIVE=default/' "$PROJECT_DIR/.env"
            echo "  INFERENCE_MODE=local"
            echo "  SERVERLESS_ACTIVE=default"
            echo -e "  Mode: ${YELLOW}Workers poll Redis queue${NC}"
            echo "  Best for: Development, testing, dedicated GPU instance"
            ;;
        *)
            echo "Unknown mode: $MODE"
            show_usage
            exit 1
            ;;
    esac

    echo ""
    echo -e "${YELLOW}Restart queue-manager to apply:${NC}"
    echo "  docker compose restart queue-manager"
}

# Main
case "${1:-}" in
    h200-spot|h200-on-demand|b300-spot|b300-on-demand|local)
        switch_mode "$1"
        ;;
    status|"")
        show_status
        ;;
    -h|--help|help)
        show_usage
        ;;
    *)
        echo "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac
