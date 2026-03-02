#!/bin/bash
# P6-02: BlackHole Audio Routing Setup

set -e

echo "=== BlackHole Installation (P6-02) ==="

# Install BlackHole
echo "Installing BlackHole 2ch..."
if brew list --cask blackhole-2ch &> /dev/null; then
    echo "✅ BlackHole already installed"
else
    brew install --cask blackhole-2ch
    echo "✅ BlackHole installed"
fi

echo ""
echo "=== Post-Installation Steps ==="
echo "1. Open Audio MIDI Setup (in /Applications/Utilities/)"
echo "2. Create Multi-Output Device:"
echo "   - Click '+' → Create Multi-Output Device"
echo "   - Check 'BlackHole 2ch'"
echo "   - Check your speakers/headphones"
echo "   - Name it 'Jarvis Output'"
echo ""
echo "3. Set Piper TTS to output to 'Jarvis Output'"
echo "4. Set SonoBus to input from 'BlackHole 2ch'"
echo ""
echo "See docs/audio_routing.md for routing diagram"
echo ""
echo "✅ P6-02 Complete"
