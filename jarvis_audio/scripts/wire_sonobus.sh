#!/usr/bin/env bash
# wire_sonobus.sh - Wire SonoBus <-> Jarvis PipeWire devices
#
# Run this after SonoBus is already running and connected to
# a group.  It wires SonoBus PipeWire ports to the Jarvis
# virtual audio devices and disconnects unwanted HDMI links.
#
# Port topology (after LD_LIBRARY_PATH pw-jack shim):
#   alsa_playback.sonobus  = network audio FROM remote peers
#     output_FL/FR -> we route to jarvis-mic-source:input_FL/FR
#   alsa_capture.sonobus   = audio TO send to remote peers
#     input_FL/FR  <- we route from jarvis-tts-sink:monitor_FL/FR
#
# Usage:
#   ./jarvis_audio/scripts/wire_sonobus.sh
# Do not use `-e`: many probes intentionally return no-match when ports are absent.
# This script should be best-effort and never fail service startup for optional links.
set -uo pipefail

echo "Discovering SonoBus ports..."
echo ""

# Check SonoBus ports exist
if ! pw-link -Io 2>/dev/null | grep -q "sonobus"; then
    echo "ERROR: No SonoBus ports found in PipeWire."
    echo "   Is SonoBus running with the PipeWire JACK shim?"
    echo "   Launch with: LD_LIBRARY_PATH=/usr/lib/aarch64-linux-gnu/pipewire-0.3/jack sonobus --headless -g jarvis-audio -n jarvis-pi"
    exit 1
fi

echo "-- SonoBus output ports (network -> Pi) --"
pw-link -Io 2>/dev/null | grep sonobus || echo "  (none)"
echo ""
echo "-- SonoBus input ports (Pi -> network) --"
pw-link -Ii 2>/dev/null | grep sonobus || echo "  (none)"
echo ""

WIRED=0
UNWIRED=0

# -- Wire: SonoBus network audio -> jarvis-mic-source (for Whisper STT) --
echo "Routing: SonoBus playback -> jarvis-mic-source (network voice -> STT)..."

# Use port IDs for precision (handles duplicate node names)
PLAY_FL=$(pw-link -Io 2>/dev/null | grep "alsa_playback.sonobus:output_FL" | head -1 | awk '{print $1}')
PLAY_FR=$(pw-link -Io 2>/dev/null | grep "alsa_playback.sonobus:output_FR" | head -1 | awk '{print $1}')
MIC_FL=$(pw-link -Ii 2>/dev/null | grep "jarvis-mic-source:input_FL" | awk '{print $1}')
MIC_FR=$(pw-link -Ii 2>/dev/null | grep "jarvis-mic-source:input_FR" | awk '{print $1}')

if [ -n "$PLAY_FL" ] && [ -n "$MIC_FL" ]; then
    pw-link "$PLAY_FL" "$MIC_FL" 2>/dev/null && { echo "   OK: sonobus:output_FL -> mic-source:input_FL"; WIRED=$((WIRED+1)); } || echo "   (already linked)"
fi
if [ -n "$PLAY_FR" ] && [ -n "$MIC_FR" ]; then
    pw-link "$PLAY_FR" "$MIC_FR" 2>/dev/null && { echo "   OK: sonobus:output_FR -> mic-source:input_FR"; WIRED=$((WIRED+1)); } || echo "   (already linked)"
fi

echo ""

# -- Wire: jarvis-tts-sink -> SonoBus capture (TTS -> AirPods) --
echo "Routing: jarvis-tts-sink -> SonoBus capture (TTS -> network)..."

TTS_MON_FL=$(pw-link -Io 2>/dev/null | grep "jarvis-tts-sink:monitor_FL" | awk '{print $1}')
TTS_MON_FR=$(pw-link -Io 2>/dev/null | grep "jarvis-tts-sink:monitor_FR" | awk '{print $1}')
CAP_FL=$(pw-link -Ii 2>/dev/null | grep "alsa_capture.sonobus:input_FL" | head -1 | awk '{print $1}')
CAP_FR=$(pw-link -Ii 2>/dev/null | grep "alsa_capture.sonobus:input_FR" | head -1 | awk '{print $1}')

if [ -n "$TTS_MON_FL" ] && [ -n "$CAP_FL" ]; then
    pw-link "$TTS_MON_FL" "$CAP_FL" 2>/dev/null && { echo "   OK: tts-sink:monitor_FL -> sonobus:input_FL"; WIRED=$((WIRED+1)); } || echo "   (already linked)"
fi
if [ -n "$TTS_MON_FR" ] && [ -n "$CAP_FR" ]; then
    pw-link "$TTS_MON_FR" "$CAP_FR" 2>/dev/null && { echo "   OK: tts-sink:monitor_FR -> sonobus:input_FR"; WIRED=$((WIRED+1)); } || echo "   (already linked)"
fi

echo ""

# -- Disconnect unwanted HDMI <-> SonoBus auto-links --
echo "Cleaning up unwanted HDMI links..."

# Get HDMI port IDs
HDMI_MON_FL=$(pw-link -Io 2>/dev/null | grep "hdmi.*monitor_FL" | head -1 | awk '{print $1}')
HDMI_MON_FR=$(pw-link -Io 2>/dev/null | grep "hdmi.*monitor_FR" | head -1 | awk '{print $1}')
HDMI_PLAY_FL=$(pw-link -Ii 2>/dev/null | grep "hdmi.*playback_FL" | head -1 | awk '{print $1}')
HDMI_PLAY_FR=$(pw-link -Ii 2>/dev/null | grep "hdmi.*playback_FR" | head -1 | awk '{print $1}')

# Disconnect HDMI monitor -> all SonoBus capture inputs
for cap_id in $(pw-link -Ii 2>/dev/null | grep "alsa_capture.sonobus:input_F" | awk '{print $1}'); do
    if [ -n "$HDMI_MON_FL" ]; then
        pw-link -d "$HDMI_MON_FL" "$cap_id" 2>/dev/null && { echo "   Removed: HDMI monitor -> sonobus capture ($cap_id)"; UNWIRED=$((UNWIRED+1)); } || true
    fi
    if [ -n "$HDMI_MON_FR" ]; then
        pw-link -d "$HDMI_MON_FR" "$cap_id" 2>/dev/null && { echo "   Removed: HDMI monitor -> sonobus capture ($cap_id)"; UNWIRED=$((UNWIRED+1)); } || true
    fi
done

# Disconnect all SonoBus playback outputs -> HDMI playback
for play_id in $(pw-link -Io 2>/dev/null | grep "alsa_playback.sonobus:output_F" | awk '{print $1}'); do
    if [ -n "$HDMI_PLAY_FL" ]; then
        pw-link -d "$play_id" "$HDMI_PLAY_FL" 2>/dev/null && { echo "   Removed: sonobus playback ($play_id) -> HDMI"; UNWIRED=$((UNWIRED+1)); } || true
    fi
    if [ -n "$HDMI_PLAY_FR" ]; then
        pw-link -d "$play_id" "$HDMI_PLAY_FR" 2>/dev/null && { echo "   Removed: sonobus playback ($play_id) -> HDMI"; UNWIRED=$((UNWIRED+1)); } || true
    fi
done

echo ""

# -- Summary --
echo "Wiring complete: $WIRED links added, $UNWIRED HDMI links removed"
echo ""
echo "-- Active links --"
pw-link -l 2>/dev/null | grep -v midi | grep -v bluez | grep -iE "jarvis|sonobus" || echo "  (none)"
