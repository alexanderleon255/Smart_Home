#!/usr/bin/env bash
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

pass() { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}!${NC} $*"; }
fail() { echo -e "${RED}✗${NC} $*"; }
info() { echo -e "${BLUE}ℹ${NC} $*"; }

ALERTS=0
HUB_MEMORY_DIR="${HUB_MEMORY_DIR:-$HOME/hub_memory}"
AUDIT_LOG="${AUDIT_LOG:-$HUB_MEMORY_DIR/audit_log.jsonl}"
TAILSCALE_STATE="${TAILSCALE_STATE:-$HUB_MEMORY_DIR/tailscale_peers.snapshot}"
HA_LOG_PATH="${HA_LOG_PATH:-$PWD/ha_config/home-assistant.log}"

echo "========================================"
echo "  Smart Home Security Monitor"
echo "  Roadmap: P4-05 Logging & Monitoring"
echo "========================================"

mkdir -p "$HUB_MEMORY_DIR"

echo
info "Checking Tool Broker auth failures in audit log"
if [[ -f "$AUDIT_LOG" ]]; then
  FAIL_COUNT=$(tail -n 5000 "$AUDIT_LOG" | awk '/"status_code": (401|403)/ {count++} END {print count+0}')
  if [[ "$FAIL_COUNT" -gt 0 ]]; then
    warn "Detected $FAIL_COUNT recent unauthorized/forbidden requests"
    ALERTS=$((ALERTS + 1))
  else
    pass "No recent unauthorized Tool Broker requests"
  fi

  BROKER_ERRORS=$(tail -n 5000 "$AUDIT_LOG" | awk '/"error": "[^"]+/ {count++} END {print count+0}')
  if [[ "$BROKER_ERRORS" -gt 0 ]]; then
    warn "Detected $BROKER_ERRORS recent Tool Broker error entries"
    ALERTS=$((ALERTS + 1))
  else
    pass "No recent Tool Broker error entries"
  fi
else
  warn "Audit log not found at $AUDIT_LOG"
fi

echo
info "Checking for new Tailscale device joins"
if command -v tailscale >/dev/null 2>&1; then
  CURRENT_PEERS=$(tailscale status --json 2>/dev/null | python3 -c 'import json,sys; data=json.load(sys.stdin); peers=sorted((v.get("HostName") or v.get("DNSName") or k) for k,v in data.get("Peer",{}).items()); print("\n".join(peers))' || true)
  if [[ -n "$CURRENT_PEERS" ]]; then
    if [[ -f "$TAILSCALE_STATE" ]]; then
      NEW_PEERS=$(comm -13 <(sort "$TAILSCALE_STATE") <(printf "%s\n" "$CURRENT_PEERS" | sort) || true)
      if [[ -n "$NEW_PEERS" ]]; then
        warn "New Tailscale peers detected since last run:"
        printf "%s\n" "$NEW_PEERS" | sed 's/^/  - /'
        ALERTS=$((ALERTS + 1))
      else
        pass "No new Tailscale peers detected"
      fi
    else
      info "No prior Tailscale snapshot found — creating baseline"
    fi
    printf "%s\n" "$CURRENT_PEERS" > "$TAILSCALE_STATE"
  else
    warn "Unable to read peer list from tailscale status"
  fi
else
  warn "Tailscale CLI not available on this host"
fi

echo
info "Checking Home Assistant automation errors"
if [[ -f "$HA_LOG_PATH" ]]; then
  AUTO_ERRORS=$(tail -n 5000 "$HA_LOG_PATH" | awk 'BEGIN{IGNORECASE=1} /automation|script/ && /error|exception|failed/ {count++} END {print count+0}')
  if [[ "$AUTO_ERRORS" -gt 0 ]]; then
    warn "Detected $AUTO_ERRORS recent automation/script error log lines"
    ALERTS=$((ALERTS + 1))
  else
    pass "No recent automation/script error lines in HA logs"
  fi
else
  warn "HA log not found at $HA_LOG_PATH"
fi

echo
if [[ "$ALERTS" -gt 0 ]]; then
  fail "Security monitor finished with $ALERTS alert class(es)"
  exit 2
fi

pass "Security monitor finished with no alerts"
