#!/bin/bash
# P6-01: SonoBus Audio Bridge Setup

set -e

echo "=== SonoBus Installation (P6-01) ==="

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "Error: Homebrew not installed. Install from https://brew.sh"
    exit 1
fi

# Install SonoBus
echo "Installing SonoBus..."
if brew list --cask sonobus &> /dev/null; then
    echo "✅ SonoBus already installed"
else
    brew install --cask sonobus
    echo "✅ SonoBus installed"
fi

echo ""
echo "=== Post-Installation Steps ==="
echo "1. On Mac: Open SonoBus"
echo "2. On iPhone: Install SonoBus from App Store"
echo "3. Connect both devices to same network or Tailscale"
echo "4. In SonoBus on both devices:"
echo "   - Use same Group Name"
echo "   - Enable 'Auto-connect to Group'"
echo "   - Set Audio Quality to 'Best' (lowest latency)"
echo ""
echo "See docs/sonobus_config.md for detailed setup"
echo ""
echo "✅ P6-01 Complete"
