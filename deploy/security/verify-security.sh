#!/usr/bin/env bash
# =============================================================================
# Smart Home — Security Verification Script
#
# Roadmap: P4-02 (Tailscale ACLs), P4-03 (Local Firewall)
# Reference: Smart_Home_Threat_Model_Analysis_Rev_1_0.md §14
#
# Run from any device on the tailnet to verify security posture.
# Can also run locally on Pi or Mac for self-checks.
#
#   cd ~/Smart_Home && ./deploy/security/verify-security.sh
#
# Flags:
#   --pi-only    Only verify Pi firewall
#   --mac-only   Only verify Mac firewall
#   --tailscale  Only verify Tailscale connectivity
#   (no flags)   Run all checks applicable to current host
# =============================================================================
set -uo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

pass() { echo -e "  ${GREEN}✓${NC} $*"; ((PASS++)); }
fail() { echo -e "  ${RED}✗${NC} $*"; ((FAIL++)); }
warn() { echo -e "  ${YELLOW}!${NC} $*"; ((WARN++)); }
info() { echo -e "  ${BLUE}ℹ${NC} $*"; }
header() { echo -e "\n${BLUE}═══ $* ═══${NC}"; }

# Known IPs
PI_IP="100.83.1.2"
PI_LAN="${PI_LAN:-192.168.1.0}"  # Override with your LAN IP if different
MAC_IP="100.98.1.21"
IPHONE_IP="100.83.74.23"

# Detect current host
HOSTNAME_SHORT="$(hostname -s 2>/dev/null || echo unknown)"
IS_PI=false
IS_MAC=false

if [[ "$(uname -m)" == "aarch64" ]] && [[ -f /etc/debian_version ]]; then
    IS_PI=true
elif [[ "$(uname)" == "Darwin" ]]; then
    IS_MAC=true
fi

# =============================================================================
# Tailscale checks
# =============================================================================
check_tailscale() {
    header "Tailscale Status"

    # Is Tailscale running?
    if command -v tailscale &>/dev/null; then
        pass "Tailscale installed"
    else
        fail "Tailscale not installed"
        return
    fi

    if tailscale status &>/dev/null; then
        pass "Tailscale running"
    else
        fail "Tailscale not running or not authenticated"
        return
    fi

    # Show peer list
    info "Tailscale peers:"
    tailscale status 2>/dev/null | while read -r line; do
        info "  $line"
    done

    # Check MagicDNS
    if tailscale status --json 2>/dev/null | grep -q '"MagicDNSSuffix"'; then
        pass "MagicDNS enabled"
    else
        warn "MagicDNS not detected (optional)"
    fi

    # Check key expiry
    local expiry
    expiry=$(tailscale status --json 2>/dev/null | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    self_key = data.get('Self', {}).get('KeyExpiry', '')
    if self_key:
        print(self_key)
    else:
        print('no-expiry')
except: print('unknown')
" 2>/dev/null || echo "unknown")

    if [[ "$expiry" == "no-expiry" ]]; then
        warn "Key has no expiry set (consider enabling key expiry)"
    elif [[ "$expiry" != "unknown" ]]; then
        info "Key expires: $expiry"
    fi
}

# =============================================================================
# Tailscale connectivity checks
# =============================================================================
check_tailscale_connectivity() {
    header "Tailscale Connectivity (from this device)"

    # Ping Pi
    if timeout 3 tailscale ping "$PI_IP" &>/dev/null 2>&1; then
        pass "Pi ($PI_IP) reachable via Tailscale"
    else
        warn "Pi ($PI_IP) not reachable (may be offline or different IP)"
    fi

    # Ping Mac
    if timeout 3 tailscale ping "$MAC_IP" &>/dev/null 2>&1; then
        pass "Mac ($MAC_IP) reachable via Tailscale"
    else
        warn "Mac ($MAC_IP) not reachable (may be offline or different IP)"
    fi
}

# =============================================================================
# Pi service port checks (from any device)
# =============================================================================
check_pi_services() {
    header "Pi Service Ports ($PI_IP)"

    local -A PORTS=(
        [8123]="Home Assistant"
        [8000]="Tool Broker"
        [8050]="Dashboard"
        [8080]="Pi-hole Admin"
        [53]="Pi-hole DNS"
        [11434]="Ollama"
        [22]="SSH"
    )

    for port in "${!PORTS[@]}"; do
        local svc="${PORTS[$port]}"
        if timeout 3 bash -c "echo >/dev/tcp/$PI_IP/$port" 2>/dev/null; then
            pass "$svc (port $port) — open"
        else
            warn "$svc (port $port) — closed or unreachable"
        fi
    done

    # MQTT should NOT be reachable from non-Pi devices (unless via Tailscale for admin)
    if ! $IS_PI; then
        if timeout 3 bash -c "echo >/dev/tcp/$PI_IP/1883" 2>/dev/null; then
            warn "MQTT (port 1883) — open from this device (may want to restrict)"
        else
            pass "MQTT (port 1883) — not reachable from this device (correct)"
        fi
    fi
}

# =============================================================================
# Mac service port checks (from any device)
# =============================================================================
check_mac_services() {
    header "Mac Sidecar Ports ($MAC_IP)"

    # Ollama should be reachable from Pi (sidecar tier)
    if timeout 3 bash -c "echo >/dev/tcp/$MAC_IP/11434" 2>/dev/null; then
        pass "Ollama sidecar (port 11434) — open"
    else
        warn "Ollama sidecar (port 11434) — closed or unreachable"
    fi

    # SSH
    if timeout 3 bash -c "echo >/dev/tcp/$MAC_IP/22" 2>/dev/null; then
        pass "Mac SSH (port 22) — open"
    else
        info "Mac SSH (port 22) — closed (expected if Remote Login disabled)"
    fi
}

# =============================================================================
# Pi firewall checks (run on Pi only)
# =============================================================================
check_pi_firewall() {
    if ! $IS_PI; then return; fi

    header "Pi Firewall (UFW)"

    if command -v ufw &>/dev/null; then
        pass "UFW installed"
    else
        fail "UFW not installed — run deploy/security/setup-firewall-pi.sh"
        return
    fi

    local status
    status=$(sudo ufw status 2>/dev/null | head -1)
    if echo "$status" | grep -q "Status: active"; then
        pass "UFW is active"
    else
        fail "UFW is not active — run: sudo ufw enable"
        return
    fi

    # Check default policies
    if sudo ufw status verbose 2>/dev/null | grep -q "Default: deny (incoming)"; then
        pass "Default incoming: DENY"
    else
        fail "Default incoming is not DENY"
    fi

    if sudo ufw status verbose 2>/dev/null | grep -q "Default: allow (outgoing)"; then
        pass "Default outgoing: ALLOW"
    else
        warn "Default outgoing is not ALLOW (may break things)"
    fi

    # Count rules
    local rule_count
    rule_count=$(sudo ufw status numbered 2>/dev/null | grep -c "^\[" || echo 0)
    info "UFW has $rule_count rules configured"

    # Check for expected ports
    for port in 22 8000 8050 8123 11434; do
        if sudo ufw status 2>/dev/null | grep -q "$port"; then
            pass "Port $port has a UFW rule"
        else
            warn "Port $port has no UFW rule"
        fi
    done
}

# =============================================================================
# Mac firewall checks (run on Mac only)
# =============================================================================
check_mac_firewall() {
    if ! $IS_MAC; then return; fi

    header "Mac Firewall"

    # Application Firewall
    local fw_state
    fw_state=$(/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate 2>/dev/null || echo "unknown")
    if echo "$fw_state" | grep -qi "enabled"; then
        pass "macOS Application Firewall enabled"
    else
        warn "macOS Application Firewall not enabled — run deploy/security/setup-firewall-mac.sh"
    fi

    # Stealth mode
    local stealth
    stealth=$(/usr/libexec/ApplicationFirewall/socketfilterfw --getstealthmode 2>/dev/null || echo "unknown")
    if echo "$stealth" | grep -qi "enabled"; then
        pass "Stealth mode enabled"
    else
        warn "Stealth mode not enabled"
    fi

    # pf status
    if pfctl -s info &>/dev/null 2>&1; then
        local pf_enabled
        pf_enabled=$(pfctl -s info 2>/dev/null | grep "Status:" | head -1)
        if echo "$pf_enabled" | grep -qi "enabled"; then
            pass "pf (packet filter) enabled"
        else
            warn "pf (packet filter) not enabled"
        fi
    else
        info "pf status check requires sudo"
    fi
}

# =============================================================================
# Security best-practice checks
# =============================================================================
check_best_practices() {
    header "Security Best Practices"

    # Check if Tool Broker has API key configured
    if [[ -n "${TOOL_BROKER_API_KEY:-}" ]]; then
        pass "TOOL_BROKER_API_KEY is set"
    else
        warn "TOOL_BROKER_API_KEY not set in environment (authentication may be disabled)"
    fi

    # Check if HA token is configured (not logging the value)
    if [[ -n "${HA_TOKEN:-}" ]]; then
        pass "HA_TOKEN is set"
    else
        warn "HA_TOKEN not set in environment"
    fi

    # Check for plaintext credentials in repo
    if $IS_PI || $IS_MAC; then
        local script_dir
        script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        local repo_dir
        repo_dir="$(dirname "$(dirname "$script_dir")")"

        if [[ -d "$repo_dir" ]]; then
            local cred_matches
            cred_matches=$(grep -rn "password.*=.*['\"]" "$repo_dir"/*.py "$repo_dir"/**/*.py 2>/dev/null | grep -v "test_" | grep -v "__pycache__" | wc -l || echo 0)
            if [[ "$cred_matches" -gt 0 ]]; then
                warn "Found $cred_matches potential hardcoded password(s) in source files"
            else
                pass "No hardcoded passwords detected in source files"
            fi
        fi
    fi
}

# =============================================================================
# Summary
# =============================================================================
print_summary() {
    header "SUMMARY"
    echo -e "  ${GREEN}Passed:${NC}  $PASS"
    echo -e "  ${RED}Failed:${NC}  $FAIL"
    echo -e "  ${YELLOW}Warnings:${NC} $WARN"
    echo ""

    if [[ $FAIL -gt 0 ]]; then
        echo -e "  ${RED}ACTION REQUIRED: $FAIL check(s) failed. See above.${NC}"
    elif [[ $WARN -gt 0 ]]; then
        echo -e "  ${YELLOW}ATTENTION: $WARN warning(s). Review recommended.${NC}"
    else
        echo -e "  ${GREEN}All checks passed!${NC}"
    fi
    echo ""
}

# =============================================================================
# Main
# =============================================================================
main() {
    echo "========================================"
    echo "  Smart Home — Security Verification"
    echo "  Roadmap: P4-02, P4-03"
    echo "========================================"
    echo "Host: $HOSTNAME_SHORT (Pi=$IS_PI, Mac=$IS_MAC)"
    echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"

    case "${1:-all}" in
        --pi-only)
            check_pi_firewall
            check_pi_services
            ;;
        --mac-only)
            check_mac_firewall
            check_mac_services
            ;;
        --tailscale)
            check_tailscale
            check_tailscale_connectivity
            ;;
        all|*)
            check_tailscale
            check_tailscale_connectivity
            check_pi_services
            check_mac_services
            check_pi_firewall
            check_mac_firewall
            check_best_practices
            ;;
    esac

    print_summary
}

main "$@"
