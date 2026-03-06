#!/usr/bin/env bash
# =============================================================================
# Jarvis Voice Pipeline — End-to-End Test Protocol  (P6-10)
#
# Prerequisites:
#   1. SonoBus running on Pi (systemctl --user status sonobus)
#   2. iPhone SonoBus app connected to same group ("SmartHome")
#   3. PipeWire virtual devices active (jarvis-tts-sink, jarvis-mic-source)
#   4. Tool Broker running (systemctl --user status tool-broker)
#   5. Home Assistant reachable (curl http://localhost:8123/api/ -H "Authorization: ...")
#   6. Ollama running (curl http://localhost:11434/api/tags)
#
# Usage:
#   ./jarvis_audio/scripts/voice_test_protocol.sh [--auto]
#
#   --auto   Run automated checks only (no manual voice tests)
#
# This script runs in two phases:
#   Phase A: Automated infrastructure checks (always runs)
#   Phase B: Manual voice test prompts (requires human + iPhone)
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

PASS=0
FAIL=0
SKIP=0
AUTO_ONLY=false

[[ "${1:-}" == "--auto" ]] && AUTO_ONLY=true

log()     { echo -e "${GREEN}[PASS]${NC} $*"; ((PASS++)); }
fail()    { echo -e "${RED}[FAIL]${NC} $*"; ((FAIL++)); }
skip()    { echo -e "${YELLOW}[SKIP]${NC} $*"; ((SKIP++)); }
header()  { echo -e "\n${BLUE}${BOLD}═══ $* ═══${NC}"; }
prompt()  { echo -e "${BOLD}  → $*${NC}"; }

# =============================================================================
# Phase A: Automated Infrastructure Checks
# =============================================================================
header "Phase A: Infrastructure Checks"

# A1: SonoBus process
echo -n "A1. SonoBus running: "
if pgrep -x sonobus &>/dev/null; then
    log "PID $(pgrep -x sonobus)"
else
    fail "sonobus not running — start with: systemctl --user start sonobus"
fi

# A2: PipeWire virtual devices
echo -n "A2. PipeWire jarvis-tts-sink: "
if pw-cli list-objects | grep -q "jarvis-tts-sink" 2>/dev/null; then
    log "found"
else
    fail "jarvis-tts-sink not found — run: systemctl --user start jarvis-audio-devices"
fi

echo -n "A3. PipeWire jarvis-mic-source: "
if pw-cli list-objects | grep -q "jarvis-mic-source" 2>/dev/null; then
    log "found"
else
    fail "jarvis-mic-source not found"
fi

# A4: SonoBus wiring (JACK connections)
echo -n "A4. SonoBus→PipeWire wiring: "
if pw-jack jack_lsp -c 2>/dev/null | grep -q "SonoBus"; then
    log "SonoBus JACK ports connected"
else
    fail "No SonoBus JACK connections — run: jarvis_audio/scripts/wire_sonobus.sh"
fi

# A5: Tool Broker health
echo -n "A5. Tool Broker health: "
TB_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/v1/health 2>/dev/null || echo "000")
if [[ "$TB_HEALTH" == "200" ]]; then
    log "HTTP 200"
else
    fail "HTTP ${TB_HEALTH} — start with: systemctl --user start tool-broker"
fi

# A6: Home Assistant API
echo -n "A6. Home Assistant API: "
HA_URL="${HA_URL:-http://localhost:8123}"
HA_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${HA_URL}/api/" -H "Authorization: Bearer ${HA_TOKEN:-invalid}" 2>/dev/null || echo "000")
if [[ "$HA_STATUS" == "200" ]]; then
    log "HTTP 200"
else
    fail "HTTP ${HA_STATUS} — check HA_URL and HA_TOKEN"
fi

# A7: Ollama
echo -n "A7. Ollama running: "
OLLAMA_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:11434/api/tags 2>/dev/null || echo "000")
if [[ "$OLLAMA_STATUS" == "200" ]]; then
    log "HTTP 200"
else
    fail "HTTP ${OLLAMA_STATUS} — start with: systemctl --user start ollama"
fi

# A8: whisper.cpp binary
echo -n "A8. whisper.cpp binary: "
WHISPER_BIN="${WHISPER_CPP_PATH:-$HOME/whisper.cpp/build/bin/whisper-cli}"
if [[ -x "$WHISPER_BIN" ]]; then
    log "$WHISPER_BIN"
else
    fail "Not found at $WHISPER_BIN — set WHISPER_CPP_PATH"
fi

# A9: Piper binary
echo -n "A9. Piper TTS binary: "
PIPER_BIN="${PIPER_PATH:-$HOME/.local/piper/piper/piper}"
if [[ -x "$PIPER_BIN" ]]; then
    log "$PIPER_BIN"
else
    fail "Not found at $PIPER_BIN — set PIPER_PATH"
fi

# A10: Jarvis model in Ollama
echo -n "A10. Jarvis model available: "
if curl -s http://localhost:11434/api/tags 2>/dev/null | grep -q '"jarvis"'; then
    log "jarvis model found"
else
    skip "jarvis model not found — create with: ollama create jarvis -f jarvis_audio/Modelfile.jarvis"
fi

# Phase A summary
header "Phase A Summary: ${PASS} pass, ${FAIL} fail, ${SKIP} skip"

if $AUTO_ONLY; then
    echo ""
    echo "Auto-only mode. Skipping manual voice tests."
    echo "Total: ${PASS} pass, ${FAIL} fail, ${SKIP} skip"
    exit $(( FAIL > 0 ? 1 : 0 ))
fi

# =============================================================================
# Phase B: Manual Voice Tests (requires iPhone SonoBus + human)
# =============================================================================
header "Phase B: Manual Voice Tests"
echo ""
echo "These tests require you to speak into iPhone SonoBus."
echo "The Jarvis voice loop should be running:"
echo "  cd ${REPO_DIR} && .venv/bin/python -m jarvis"
echo ""
echo "Press Enter after each test to record the result."
echo ""

run_voice_test() {
    local test_id="$1"
    local description="$2"
    local utterance="$3"
    local expected="$4"
    
    echo -e "${BOLD}Test ${test_id}: ${description}${NC}"
    echo "  Utterance: \"${utterance}\""
    echo "  Expected:  ${expected}"
    echo ""
    prompt "Speak the utterance, observe result, then enter [p]ass / [f]ail / [s]kip:"
    read -r result
    case "${result,,}" in
        p|pass)  log "${test_id}: ${description}" ;;
        f|fail)  fail "${test_id}: ${description}" ;;
        s|skip)  skip "${test_id}: ${description}" ;;
        *)       skip "${test_id}: ${description} (invalid input)" ;;
    esac
    echo ""
}

# B1: Wake word detection
run_voice_test "B1" "Wake Word Detection" \
    "Hey Jarvis" \
    "Wake word triggers listening state (voice_loop transitions from IDLE to LISTENING)"

# B2: Basic light command
run_voice_test "B2" "Basic Light Control" \
    "Hey Jarvis, turn on the living room lights" \
    "STT transcribes → LLM generates ha_service_call → HA executes light.turn_on → TTS confirms"

# B3: Invalid entity handling
run_voice_test "B3" "Invalid Entity Rejection" \
    "Hey Jarvis, turn on the garage door" \
    "LLM responds with text explaining the entity is not found (no tool_call emitted)"

# B4: Brightness / parameterized command
run_voice_test "B4" "Parameterized Command" \
    "Hey Jarvis, set the bedroom lights to 50 percent" \
    "Tool call includes service_data with brightness: 128 (or brightness_pct: 50)"

# B5: Barge-in interruption
run_voice_test "B5" "Barge-In During TTS" \
    "Hey Jarvis, what's the weather — [interrupt during response] — Hey Jarvis, turn off all lights" \
    "TTS stops mid-sentence; new command is processed (barge_in.py triggers)"

# B6: Background noise resilience
run_voice_test "B6" "Background Noise Resilience" \
    "[Play music/TV audio] Hey Jarvis, turn on the kitchen lights" \
    "Wake word still detected; STT transcribes correctly despite noise"

# B7: Multi-turn silence handling
run_voice_test "B7" "Silence Timeout" \
    "Hey Jarvis [wait 10 seconds without speaking]" \
    "Voice loop transitions from LISTENING back to IDLE after silence timeout"

# B8: End-to-end latency
run_voice_test "B8" "Latency Check" \
    "Hey Jarvis, turn on the living room lights [time from end of speech to TTS response]" \
    "Total latency < 5 seconds (STT < 2s, LLM < 2s, TTS start < 1s)"

# =============================================================================
# Final Summary
# =============================================================================
header "Final Summary"
echo ""
echo -e "Infrastructure (Phase A): checked above"
echo -e "Voice Tests (Phase B):    manual results recorded"
echo ""
echo -e "${BOLD}Total: ${PASS} pass, ${FAIL} fail, ${SKIP} skip${NC}"
echo ""

if (( FAIL > 0 )); then
    echo -e "${RED}Some tests FAILED. Review output above.${NC}"
    exit 1
else
    echo -e "${GREEN}All executed tests PASSED.${NC}"
    exit 0
fi
