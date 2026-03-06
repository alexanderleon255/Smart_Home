#!/usr/bin/env bash
# =============================================================================
# Smart Home — Pi 5 Firewall Setup (UFW)
#
# Roadmap: P4-03 (Local Firewall Configuration)
# Reference: Smart_Home_Threat_Model_Analysis_Rev_1_0.md §9.1, §9.4
#
# WHAT THIS DOES:
#   - Installs UFW if not present
#   - Sets default-deny incoming, allow outgoing
#   - Opens ONLY the ports Smart Home services need
#   - Restricts source IPs to LAN (192.168.0.0/16) + Tailscale (100.64.0.0/10)
#   - Preserves Docker's iptables rules (UFW + Docker coexistence)
#   - SSH is rate-limited (brute-force protection)
#
# RUN AS: Regular user with sudo access on Pi 5
#   cd ~/Smart_Home && sudo ./deploy/security/setup-firewall-pi.sh
#
# ROLLBACK:
#   sudo ufw disable
#   sudo ufw reset
#
# PORT INVENTORY (Pi 5):
#   22    — SSH (admin only, rate limited)
#   1883  — MQTT (Mosquitto, Docker internal + localhost)
#   8000  — Tool Broker (FastAPI)
#   8050  — Dashboard (Dash)
#   8123  — Home Assistant (Docker)
#   10998 — SonoBus (UDP, audio bridge)
#   11434 — Ollama (local LLM)
#
# NETWORK ASSUMPTIONS:
#   LAN:       192.168.0.0/16 (covers most home networks)
#   Tailscale: 100.64.0.0/10  (Tailscale CGNAT range)
#   Docker:    172.16.0.0/12  (Docker bridge networks)
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

# =============================================================================
# Network ranges
# =============================================================================
LAN="192.168.0.0/16"
TAILSCALE="100.64.0.0/10"
DOCKER="172.16.0.0/12"

# Allowed source networks for most services
ALLOWED_NETS=("$LAN" "$TAILSCALE")

# =============================================================================
# 1. Install UFW
# =============================================================================
install_ufw() {
    if command -v ufw &>/dev/null; then
        log "UFW already installed"
    else
        log "Installing UFW..."
        apt-get update -qq
        apt-get install -y -qq ufw
        log "UFW installed"
    fi
}

# =============================================================================
# 2. Reset and set defaults
# =============================================================================
configure_defaults() {
    log "Resetting UFW rules..."
    ufw --force reset

    log "Setting default policies: deny incoming, allow outgoing"
    ufw default deny incoming
    ufw default allow outgoing

    # Allow all traffic on loopback
    ufw allow in on lo
}

# =============================================================================
# 3. SSH — rate limited, LAN + Tailscale only
# =============================================================================
configure_ssh() {
    log "Configuring SSH (port 22) — rate limited"
    for net in "${ALLOWED_NETS[@]}"; do
        ufw allow from "$net" to any port 22 proto tcp comment "SSH from $net"
    done
    # Rate limiting as additional protection (applies to all SSH)
    ufw limit 22/tcp comment "SSH brute-force protection"
}

# =============================================================================
# 4. Home Assistant — LAN + Tailscale
# =============================================================================
configure_ha() {
    log "Configuring Home Assistant (port 8123)"
    for net in "${ALLOWED_NETS[@]}"; do
        ufw allow from "$net" to any port 8123 proto tcp comment "HA from $net"
    done
}

# =============================================================================
# 5. Tool Broker — LAN + Tailscale
# =============================================================================
configure_tool_broker() {
    log "Configuring Tool Broker (port 8000)"
    for net in "${ALLOWED_NETS[@]}"; do
        ufw allow from "$net" to any port 8000 proto tcp comment "Tool Broker from $net"
    done
}

# =============================================================================
# 6. Dashboard — LAN + Tailscale
# =============================================================================
configure_dashboard() {
    log "Configuring Dashboard (port 8050)"
    for net in "${ALLOWED_NETS[@]}"; do
        ufw allow from "$net" to any port 8050 proto tcp comment "Dashboard from $net"
    done
}

# =============================================================================
# 7. Ollama — LAN + Tailscale (needed for sidecar routing from Mac)
# =============================================================================
configure_ollama() {
    log "Configuring Ollama (port 11434)"
    for net in "${ALLOWED_NETS[@]}"; do
        ufw allow from "$net" to any port 11434 proto tcp comment "Ollama from $net"
    done
}

# =============================================================================
# 8. MQTT — localhost + Docker internal only
# Mosquitto should NOT be accessible from the broader LAN.
# Only Docker containers (HA) and local processes need it.
# =============================================================================
configure_mqtt() {
    log "Configuring MQTT (port 1883) — localhost + Docker only"
    ufw allow from 127.0.0.0/8 to any port 1883 proto tcp comment "MQTT from localhost"
    ufw allow from "$DOCKER" to any port 1883 proto tcp comment "MQTT from Docker"
    # Also allow from Tailscale for future MQTT clients (sensor satellites)
    ufw allow from "$TAILSCALE" to any port 1883 proto tcp comment "MQTT from Tailscale"
}

# =============================================================================
# 9. SonoBus — UDP for audio bridge (Jarvis voice)
# =============================================================================
configure_sonobus() {
    log "Configuring SonoBus (UDP port 10998)"
    for net in "${ALLOWED_NETS[@]}"; do
        ufw allow from "$net" to any port 10998 proto udp comment "SonoBus from $net"
    done
}

# =============================================================================
# 10. Docker bridge — allow Docker internal networking
# UFW can interfere with Docker's iptables. Allow Docker bridge traffic.
# =============================================================================
configure_docker() {
    log "Configuring Docker bridge network access"
    ufw allow from "$DOCKER" comment "Docker internal networking"
}

# =============================================================================
# 11. Enable UFW
# =============================================================================
enable_ufw() {
    log "Enabling UFW..."
    ufw --force enable
    log "UFW enabled and active"
}

# =============================================================================
# 12. Configure UFW + Docker coexistence
# Docker bypasses UFW by default via iptables DOCKER chain.
# To prevent Docker from exposing ports that UFW should block,
# we configure /etc/ufw/after.rules.
# =============================================================================
configure_docker_ufw_compat() {
    local AFTER_RULES="/etc/ufw/after.rules"

    # Check if we already added the Docker rules
    if grep -q "# BEGIN SMART_HOME DOCKER UFW" "$AFTER_RULES" 2>/dev/null; then
        log "Docker UFW compatibility rules already present"
        return
    fi

    log "Adding Docker UFW compatibility rules to $AFTER_RULES"
    cat >> "$AFTER_RULES" << 'DOCKERRULES'

# BEGIN SMART_HOME DOCKER UFW
# These rules ensure UFW controls Docker's external port exposure.
# Docker containers can still communicate internally, but external
# access to Docker-published ports goes through UFW.
*filter
:ufw-user-forward - [0:0]
:DOCKER-USER - [0:0]
-A DOCKER-USER -j RETURN -s 10.0.0.0/8
-A DOCKER-USER -j RETURN -s 172.16.0.0/12
-A DOCKER-USER -j RETURN -s 192.168.0.0/16
-A DOCKER-USER -j RETURN -s 100.64.0.0/10
-A DOCKER-USER -j ufw-user-forward
COMMIT
# END SMART_HOME DOCKER UFW
DOCKERRULES
    log "Docker UFW compatibility configured"
}

# =============================================================================
# 13. Show status
# =============================================================================
show_status() {
    echo ""
    log "=== UFW Status ==="
    ufw status verbose
    echo ""
    log "=== Rules (numbered) ==="
    ufw status numbered
}

# =============================================================================
# Main
# =============================================================================
main() {
    echo "========================================"
    echo "  Smart Home — Pi 5 Firewall Setup"
    echo "  Roadmap: P4-03"
    echo "========================================"
    echo ""

    install_ufw
    configure_defaults
    configure_ssh
    configure_ha
    configure_tool_broker
    configure_dashboard
    configure_ollama
    configure_mqtt
    configure_sonobus
    configure_docker
    configure_docker_ufw_compat
    enable_ufw
    show_status

    echo ""
    log "Firewall setup complete!"
    echo ""
    echo "IMPORTANT: Verify you can still SSH to this device before closing"
    echo "your current session. If locked out, physical access to the Pi"
    echo "and 'sudo ufw disable' will restore access."
    echo ""
    echo "Rollback: sudo ufw disable && sudo ufw reset"
    echo ""
}

main "$@"
