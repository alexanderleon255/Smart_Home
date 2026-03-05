#!/bin/bash
# P6-01: SonoBus Audio Bridge Setup (platform-aware)

set -e

echo "=== SonoBus Installation (P6-01) ==="

OS="$(uname -s)"

if [ "$OS" = "Darwin" ]; then
    # -- macOS --
    if ! command -v brew &>/dev/null; then
        echo "Error: Homebrew not installed. Install from https://brew.sh"
        exit 1
    fi
    echo "Installing SonoBus via Homebrew..."
    if brew list --cask sonobus &>/dev/null; then
        echo "OK: SonoBus already installed"
    else
        brew install --cask sonobus
        echo "OK: SonoBus installed"
    fi

elif [ "$OS" = "Linux" ]; then
    # -- Linux (Raspberry Pi / Debian) --
    if command -v sonobus &>/dev/null; then
        echo "OK: SonoBus already installed: $(which sonobus)"
    else
        echo "Building SonoBus from source (ARM64)..."
        SONOBUS_SRC="$HOME/sonobus"
        if [ ! -d "$SONOBUS_SRC" ]; then
            git clone --depth 1 --recurse-submodules \
                https://github.com/sonosaurus/sonobus.git "$SONOBUS_SRC"
        fi
        cd "$SONOBUS_SRC/linux"
        ./deb_get_prereqs.sh
        ./build.sh
        sudo ./install.sh
        echo "OK: SonoBus built and installed"
    fi

    # Install PipeWire JACK shim (required for SonoBus -> PipeWire routing)
    echo "Checking PipeWire packages..."
    PKGS=""
    dpkg -l pipewire-jack 2>/dev/null | grep -q "^ii" || PKGS="$PKGS pipewire-jack"
    dpkg -l pipewire-alsa 2>/dev/null | grep -q "^ii" || PKGS="$PKGS pipewire-alsa"
    dpkg -l pulseaudio-utils 2>/dev/null | grep -q "^ii" || PKGS="$PKGS pulseaudio-utils"

    if [ -n "$PKGS" ]; then
        echo "Installing:$PKGS"
        sudo apt-get install -y $PKGS
    fi
    echo "OK: PipeWire packages (pipewire-jack, pipewire-alsa, pulseaudio-utils)"

    # Verify PipeWire JACK shim exists
    PW_JACK="/usr/lib/aarch64-linux-gnu/pipewire-0.3/jack/libjack.so.0"
    if [ -f "$PW_JACK" ]; then
        echo "OK: PipeWire JACK shim at $PW_JACK"
    else
        echo "WARN: PipeWire JACK shim not found - SonoBus may not route through PipeWire"
    fi

    # Ensure PipeWire virtual devices are configured
    CONF_DIR="$HOME/.config/pipewire/pipewire.conf.d"
    if [ ! -f "$CONF_DIR/jarvis-virtual-devices.conf" ]; then
        echo "WARN: PipeWire virtual devices not configured."
        echo "   Copy from Smart_Home project or restart pipewire after placing config."
    else
        echo "OK: PipeWire virtual devices configured"
    fi
fi

echo ""
echo "=== Post-Installation Steps ==="
echo "1. On iPhone/iPad: Install SonoBus from App Store"
echo "2. On all devices: Ensure Tailscale is running"
echo "3. In SonoBus on all devices:"
echo "   - Use group name: jarvis-audio"
echo "   - Enable 'Auto-connect to Group'"
echo "   - Set Audio Quality to 'Best' (lowest latency)"
echo ""
echo "On Pi: ./jarvis_audio/scripts/launch_jarvis_audio.sh"
echo "See docs/pi_audio_routing.md for detailed setup"
echo ""
echo "Key: SonoBus must be launched with PipeWire JACK shim:"
echo "  LD_LIBRARY_PATH=/usr/lib/aarch64-linux-gnu/pipewire-0.3/jack sonobus --headless ..."
echo "  (launch_jarvis_audio.sh handles this automatically)"
echo ""
echo "OK: P6-01 Complete"
