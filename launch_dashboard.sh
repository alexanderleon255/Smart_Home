#!/usr/bin/env bash
# Launch the Smart Home Dashboard
# Usage: ./launch_dashboard.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "  ╔═══════════════════════════════════════╗"
echo "  ║    Smart Home Dashboard  v2.0         ║"
echo "  ║    Conversation-First Architecture    ║"
echo "  ╚═══════════════════════════════════════╝"
echo ""

# Ensure Dash is installed
if ! python3 -c "import dash" 2>/dev/null; then
    echo "  Installing dash..."
    pip3 install dash >/dev/null 2>&1
fi

cd "$SCRIPT_DIR"
exec python3 -m dashboard
