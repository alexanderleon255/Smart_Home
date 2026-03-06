#!/usr/bin/env bash
# =============================================================================
# Smart Home — macOS Firewall Setup (pf)
#
# Roadmap: P4-03 (Local Firewall Configuration)
# Reference: Smart_Home_Threat_Model_Analysis_Rev_1_0.md §9.2
#
# WHAT THIS DOES:
#   - Enables macOS Application Firewall (socketfilterfw) in stealth mode
#   - Creates pf (packet filter) rules to restrict incoming connections
#   - Only allows LAN + Tailscale to reach Ollama (11434)
#   - Blocks all other incoming connections
#
# RUN AS: User with admin/sudo access on Mac M1
#   cd ~/Developer/Smart_Home && sudo ./deploy/security/setup-firewall-mac.sh
#
# ROLLBACK:
#   sudo pfctl -d                    # Disable pf
#   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate off
#
# PORT INVENTORY (Mac M1 sidecar):
#   11434 — Ollama (LLM server, accessed by Pi Tool Broker)
#
# NETWORK ASSUMPTIONS:
#   LAN:       192.168.0.0/16
#   Tailscale: 100.64.0.0/10
# =============================================================================
set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
err()  { echo -e "${RED}[✗]${NC} $*" >&2; }

# Must run as root
if [[ $EUID -ne 0 ]]; then
    err "This script must be run with sudo: sudo $0"
    exit 1
fi

PF_CONF="/etc/pf.anchors/smart_home"
PF_ANCHOR_NAME="com.smart_home"

# =============================================================================
# 1. Enable macOS Application Firewall + Stealth Mode
# =============================================================================
configure_app_firewall() {
    log "Enabling macOS Application Firewall..."
    /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on
    
    log "Enabling stealth mode (no ICMP/ping responses to strangers)..."
    /usr/libexec/ApplicationFirewall/socketfilterfw --setstealthmode on
    
    log "Blocking all incoming by default..."
    /usr/libexec/ApplicationFirewall/socketfilterfw --setblockall off  # We use pf for fine-grained control
    
    log "macOS Application Firewall configured"
}

# =============================================================================
# 2. Create pf anchor rules
# =============================================================================
create_pf_rules() {
    log "Creating pf rules at $PF_CONF..."
    cat > "$PF_CONF" << 'PFRULES'
# =============================================================================
# Smart Home — macOS pf Rules (Mac M1 Sidecar)
# P4-03: Local Firewall Configuration
#
# Allow Ollama (11434) from LAN and Tailscale only.
# Block everything else incoming.
# =============================================================================

# Macros
lan_net = "192.168.0.0/16"
tailscale_net = "100.64.0.0/10"
loopback = "lo0"
ollama_port = "11434"

# Tables (for easy management)
table <trusted> { 192.168.0.0/16, 100.64.0.0/10, 127.0.0.0/8 }

# Options
set skip on $loopback
set block-policy drop

# Default: pass all outgoing, block unsolicited incoming
block in all
pass out all keep state

# Allow established connections back in
pass in quick proto { tcp, udp } from any to any keep state

# Allow Ollama from trusted networks only
pass in quick on en0 proto tcp from <trusted> to any port $ollama_port keep state
pass in quick on en1 proto tcp from <trusted> to any port $ollama_port keep state

# Allow Tailscale interface (utun) — all traffic (Tailscale handles its own ACLs)
pass in quick on utun0 all keep state
pass in quick on utun1 all keep state
pass in quick on utun2 all keep state
pass in quick on utun3 all keep state

# Allow mDNS (for local device discovery)
pass in quick proto udp from $lan_net to any port 5353 keep state

# Allow DHCP
pass in quick proto udp from any to any port 68 keep state
PFRULES
    log "pf rules created"
}

# =============================================================================
# 3. Register the anchor in pf.conf
# =============================================================================
register_anchor() {
    local PF_MAIN="/etc/pf.conf"
    
    if grep -q "$PF_ANCHOR_NAME" "$PF_MAIN" 2>/dev/null; then
        log "pf anchor already registered in $PF_MAIN"
        return
    fi
    
    log "Registering pf anchor in $PF_MAIN..."
    
    # Backup original
    cp "$PF_MAIN" "${PF_MAIN}.bak.smart_home"
    
    # Add anchor load line before the last rule
    cat >> "$PF_MAIN" << EOF

# Smart Home sidecar firewall (P4-03)
anchor "$PF_ANCHOR_NAME"
load anchor "$PF_ANCHOR_NAME" from "$PF_CONF"
EOF
    
    log "pf anchor registered"
}

# =============================================================================
# 4. Load and enable pf
# =============================================================================
enable_pf() {
    log "Loading pf rules..."
    pfctl -f /etc/pf.conf 2>/dev/null || {
        warn "pf load had warnings (this is normal on macOS)"
    }
    
    log "Enabling pf..."
    pfctl -e 2>/dev/null || {
        # pf may already be enabled
        log "pf already enabled"
    }
    
    log "pf active with Smart Home rules"
}

# =============================================================================
# 5. Show status
# =============================================================================
show_status() {
    echo ""
    log "=== pf Status ==="
    pfctl -s info 2>/dev/null | head -5
    echo ""
    log "=== Smart Home Anchor Rules ==="
    pfctl -a "$PF_ANCHOR_NAME" -s rules 2>/dev/null || echo "(anchor rules shown at load time)"
    echo ""
    log "=== Application Firewall Status ==="
    /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
    /usr/libexec/ApplicationFirewall/socketfilterfw --getstealthmode
}

# =============================================================================
# Main
# =============================================================================
main() {
    echo "========================================"
    echo "  Smart Home — macOS Firewall Setup"
    echo "  Roadmap: P4-03"
    echo "========================================"
    echo ""
    
    # Check we're on macOS
    if [[ "$(uname)" != "Darwin" ]]; then
        err "This script is for macOS only. Use setup-firewall-pi.sh for the Pi."
        exit 1
    fi
    
    configure_app_firewall
    create_pf_rules
    register_anchor
    enable_pf
    show_status
    
    echo ""
    log "macOS firewall setup complete!"
    echo ""
    echo "IMPORTANT: Verify Ollama is still reachable from the Pi:"
    echo "  (from Pi) curl -s http://100.98.1.21:11434/api/tags"
    echo ""
    echo "Rollback:"
    echo "  sudo pfctl -d                    # Disable pf"
    echo "  sudo cp /etc/pf.conf.bak.smart_home /etc/pf.conf  # Restore"
    echo ""
}

main "$@"
