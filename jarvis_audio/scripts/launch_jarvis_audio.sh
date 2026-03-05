#!/usr/bin/env bash
# launch_jarvis_audio.sh - Start Jarvis audio subsystem
#
# This script:
#   1. Verifies PipeWire virtual devices exist
#   2. Launches SonoBus headless with PipeWire JACK shim
#   3. Wires SonoBus <-> PipeWire virtual devices (by port ID)
#   4. Disconnects unwanted WirePlumber auto-links (HDMI)
#
# Architecture:
#   AirPods -> iPhone -> SonoBus App -> Tailscale -> Pi SonoBus
#   Pi SonoBus -> jarvis-mic-source -> whisper.cpp (STT)
#   Piper TTS -> jarvis-tts-sink -> SonoBus -> iPhone -> AirPods
#
# Usage:
#   ./jarvis_audio/scripts/launch_jarvis_audio.sh [group_name]
#
# Environment:
#   SONOBUS_GROUP   - SonoBus group name (default: jarvis-audio)
#   SONOBUS_PORT    - SonoBus server port (default: 10998)
#   SONOBUS_BIN     - Path to sonobus binary
set -euo pipefail

GROUP="${SONOBUS_GROUP:-${1:-jarvis-audio}}"
PORT="${SONOBUS_PORT:-10998}"
USERNAME="${SONOBUS_USERNAME:-jarvis-pi}"
SONOBUS="${SONOBUS_BIN:-/usr/local/bin/sonobus}"

# PipeWire JACK shim - SonoBus dlopen()s libjack at runtime.
# This makes it find PipeWire's JACK library instead of the
# system libjack-jackd2, so audio routes through PipeWire.
PW_JACK_LIB="/usr/lib/aarch64-linux-gnu/pipewire-0.3/jack"

# -- Preflight checks --

if ! command -v pw-link &>/dev/null; then
    echo "ERROR: pw-link not found. Install pipewire-utils."
    exit 1
fi

if ! command -v pactl &>/dev/null; then
    echo "ERROR: pactl not found. Install pulseaudio-utils."
    exit 1
fi

if ! [ -d "$PW_JACK_LIB" ]; then
    echo "ERROR: PipeWire JACK shim not found at: $PW_JACK_LIB"
    echo "   Install: sudo apt-get install -y pipewire-jack"
    exit 1
fi

# Verify virtual devices exist
if ! pactl list sinks short | grep -q "jarvis-tts-sink"; then
    echo "ERROR: jarvis-tts-sink not found."
    echo "   Copy jarvis-virtual-devices.conf to ~/.config/pipewire/pipewire.conf.d/"
    echo "   then: systemctl --user restart pipewire"
    exit 1
fi

if ! pactl list sources short | grep -q "jarvis-mic-source"; then
    echo "ERROR: jarvis-mic-source not found."
    exit 1
fi

echo "OK: PipeWire virtual devices"
echo "   Sink:   jarvis-tts-sink   (TTS -> AirPods)"
echo "   Source: jarvis-mic-source (AirPods mic -> STT)"
echo ""

# -- Launch SonoBus --

if ! [ -x "$SONOBUS" ]; then
    echo "ERROR: SonoBus binary not found at: $SONOBUS"
    echo "   Build it: cd ~/sonobus/linux && ./build.sh && sudo ./install.sh"
    exit 1
fi

echo "Launching SonoBus headless (group: $GROUP, user: $USERNAME)..."
echo "   Clients should connect to this group from iPhone/Mac/iPad SonoBus app."
echo ""

# Launch with PipeWire JACK shim so SonoBus registers as
# PipeWire nodes (alsa_capture.sonobus / alsa_playback.sonobus).
LD_LIBRARY_PATH="$PW_JACK_LIB${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" \
    "$SONOBUS" --headless -g "$GROUP" -n "$USERNAME" &
SONOBUS_PID=$!
echo "   SonoBus pid=$SONOBUS_PID"

# Give SonoBus time to register PipeWire nodes
echo "   Waiting for SonoBus PipeWire nodes..."
for i in $(seq 1 10); do
    sleep 1
    if pw-link -Io 2>/dev/null | grep -q "sonobus"; then
        echo "   OK: SonoBus ports detected after ${i}s"
        break
    fi
    if [ "$i" -eq 10 ]; then
        echo "   WARN: SonoBus ports not detected after 10s - wiring may fail"
    fi
done

# -- Wire PipeWire <-> SonoBus --

echo ""
echo "Wiring audio routes..."

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -x "$SCRIPT_DIR/wire_sonobus.sh" ]; then
    "$SCRIPT_DIR/wire_sonobus.sh"
else
    echo "   wire_sonobus.sh not found - attempting inline wiring..."
    # Fallback: wire by port name (first match)
    pw-link "alsa_playback.sonobus:output_FL" "jarvis-mic-source:input_FL" 2>/dev/null || true
    pw-link "alsa_playback.sonobus:output_FR" "jarvis-mic-source:input_FR" 2>/dev/null || true
    pw-link "jarvis-tts-sink:monitor_FL" "alsa_capture.sonobus:input_FL" 2>/dev/null || true
    pw-link "jarvis-tts-sink:monitor_FR" "alsa_capture.sonobus:input_FR" 2>/dev/null || true
fi

echo ""
echo "=============================================="
echo "  Jarvis Audio Subsystem Running"
echo ""
echo "  SonoBus group: $GROUP"
echo "  SonoBus user:  $USERNAME"
echo "  TTS sink:      jarvis-tts-sink"
echo "  Mic source:    jarvis-mic-source"
echo ""
echo "  Connect your iPhone/Mac/iPad SonoBus app to"
echo "  group '$GROUP' to relay AirPods audio."
echo ""
echo "  Press Ctrl+C to stop."
echo "=============================================="

# Cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down Jarvis audio..."
    kill "$SONOBUS_PID" 2>/dev/null || true
    echo "   Done."
}
trap cleanup EXIT INT TERM

# Keep script alive
wait "$SONOBUS_PID" 2>/dev/null || true
