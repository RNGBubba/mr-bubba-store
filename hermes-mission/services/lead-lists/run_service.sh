#!/bin/bash
# Mr Bubba Data Services — Lead List Service Launcher
# Usage: ./run_service.sh [--daemon] [--compile] [--check-inbox]

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_help() {
    echo -e "${BLUE}Mr Bubba Data Services — Lead List Service${NC}"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  --compile     Compile a lead list (interactive prompt)"
    echo "  --inbox       Check AgentMail inbox for inquiries"
    echo "  --invoice     Create a PayPal invoice (interactive prompt)"
    echo "  --daemon      Run inbox monitor daemon"
    echo "  --help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --compile --industry restaurants --location 'Los Angeles, CA'"
    echo "  $0 --invoice --email client@example.com --name 'Acme Corp' --tier standard"
    echo ""
}

compile_leads() {
    echo -e "${GREEN}📋 Lead List Compilation${NC}"
    echo "==========================="
    python3 "$SCRIPT_DIR/lead_compiler.py" "$@"
}

check_inbox() {
    echo -e "${YELLOW}📬 Checking AgentMail Inbox...${NC}"
    python3 "$SCRIPT_DIR/agentmail_responder.py"
}

run_daemon() {
    echo -e "${GREEN}🤖 Starting AgentMail Daemon...${NC}"
    python3 "$SCRIPT_DIR/agentmail_responder.py" --daemon
}

create_invoice() {
    echo -e "${GREEN}💰 Create PayPal Invoice${NC}"
    echo "========================="
    python3 "$SCRIPT_DIR/paypal_invoicer.py" "$@"
}

# Main command router
case "${1:-}" in
    --compile|-c)
        shift
        compile_leads "$@"
        ;;
    --inbox|-i)
        check_inbox
        ;;
    --invoice|-inv)
        shift
        create_invoice "$@"
        ;;
    --daemon|-d)
        run_daemon
        ;;
    --help|-h|"")
        show_help
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        show_help
        exit 1
        ;;
esac
