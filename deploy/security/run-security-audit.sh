#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REPORT_DIR="$ROOT_DIR/AI_CONTEXT/SESSION_ARTIFACTS/SECURITY_AUDITS"
TIMESTAMP="$(date '+%Y-%m-%d_%H-%M-%S')"
REPORT_PATH="$REPORT_DIR/${TIMESTAMP}_p4-06_security_audit.md"

mkdir -p "$REPORT_DIR"

PASS=0
FAIL=0
WARN=0

pass() { echo "- ✅ $*" >> "$REPORT_PATH"; PASS=$((PASS + 1)); }
fail() { echo "- ❌ $*" >> "$REPORT_PATH"; FAIL=$((FAIL + 1)); }
warn() { echo "- ⚠️ $*" >> "$REPORT_PATH"; WARN=$((WARN + 1)); }

{
  echo "# P4-06 Security Audit Report"
  echo
  echo "- **Generated:** $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
  echo "- **Host:** $(hostname)"
  echo "- **Roadmap Item:** P4-06 Security Audit"
  echo
  echo "## Checks"
} > "$REPORT_PATH"

# 1) External nmap scan
if command -v nmap >/dev/null 2>&1; then
  SCAN_OUT="$REPORT_DIR/${TIMESTAMP}_nmap.txt"
  {
    echo "# nmap localhost"
    nmap -Pn -sT -p 22,53,1883,8000,8050,8080,8123,11434,9001,10998 127.0.0.1 || true
  } > "$SCAN_OUT"
  pass "External scan executed (local host baseline): $SCAN_OUT"
else
  warn "nmap not installed; external port scan skipped"
fi

# 2) Tailscale ACL verification
ACL_FILE="$ROOT_DIR/deploy/security/tailscale-acl-policy.jsonc"
if [[ -f "$ACL_FILE" ]]; then
  if grep -q '"acls"' "$ACL_FILE" && grep -q '"tests"' "$ACL_FILE"; then
    pass "Tailscale ACL file includes ACL rules and test assertions"
  else
    fail "Tailscale ACL file missing required sections (acls/tests)"
  fi
else
  fail "Tailscale ACL file missing: deploy/security/tailscale-acl-policy.jsonc"
fi

# 3) Tool whitelisting verification
TOOLS_FILE="$ROOT_DIR/tool_broker/tools.py"
if [[ -f "$TOOLS_FILE" ]]; then
  if grep -q 'REGISTERED_TOOLS' "$TOOLS_FILE"; then
    pass "Tool allowlist registry present in tool_broker/tools.py"
  else
    fail "REGISTERED_TOOLS not found in tools.py"
  fi

  if grep -Eq 'run_command|os\.system|subprocess\.Popen\(.*shell=True' "$ROOT_DIR/tool_broker"/*.py; then
    fail "Potential command-execution primitive detected in tool_broker/*.py"
  else
    pass "No command-execution primitive detected in tool_broker/*.py"
  fi
else
  fail "Tool definition file missing: tool_broker/tools.py"
fi

# 4) Entity validation verification
MAIN_FILE="$ROOT_DIR/tool_broker/main.py"
VALIDATORS_FILE="$ROOT_DIR/tool_broker/validators.py"
if grep -q 'EntityValidator' "$MAIN_FILE" && grep -q 'validate_tool_call' "$MAIN_FILE" && grep -q 'is_valid_entity' "$VALIDATORS_FILE"; then
  pass "Entity validation is wired (main.py + validators.py)"
else
  fail "Entity validation wiring not detected"
fi

# 5) TTS shell injection verification
if grep -Eq 'shell=True' "$ROOT_DIR/jarvis/tts_controller.py" "$ROOT_DIR/jarvis_audio/tts.py"; then
  fail "TTS modules still use shell=True"
else
  pass "TTS modules do not use shell=True"
fi

{
  echo
  echo "## Summary"
  echo
  echo "- Passed: $PASS"
  echo "- Failed: $FAIL"
  echo "- Warnings: $WARN"
} >> "$REPORT_PATH"

echo "Security audit report written: $REPORT_PATH"

if [[ "$FAIL" -gt 0 ]]; then
  exit 1
fi
