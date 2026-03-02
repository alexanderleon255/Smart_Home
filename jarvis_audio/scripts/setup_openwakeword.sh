#!/bin/bash
# P6-04: openWakeWord Setup

set -e

echo "=== openWakeWord Installation (P6-04) ==="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 not found"
    exit 1
fi

# Install dependencies
echo "Installing system dependencies..."
if ! command -v portaudio &> /dev/null; then
    brew install portaudio
fi

# Install Python packages
echo "Installing Python packages..."
pip3 install openwakeword pyaudio numpy scipy

# Download wake word models
echo "Downloading wake word models..."
python3 << 'EOF'
from openwakeword.model import Model

# Download default models
print("Downloading wake word models...")
model = Model()
print("✅ Models downloaded")
EOF

echo ""
echo "=== Testing Wake Word Detection ==="
echo "Run: python3 -m jarvis_audio.wake_word"
echo ""
echo "✅ P6-04 Complete"
