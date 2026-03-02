#!/bin/bash
# P6-06: Piper TTS Setup

set -e

echo "=== Piper TTS Installation (P6-06) ==="

INSTALL_DIR="$HOME/.local/piper"
MODEL_DIR="$INSTALL_DIR/models"

# Create directories
mkdir -p "$INSTALL_DIR" "$MODEL_DIR"

# Download Piper binary for macOS
echo "Downloading Piper for macOS..."
cd "$INSTALL_DIR"

if [ ! -f "piper" ]; then
    # Download latest release
    curl -L https://github.com/rhasspy/piper/releases/latest/download/piper_macos_arm64.tar.gz -o piper.tar.gz
    tar -xzf piper.tar.gz
    rm piper.tar.gz
    chmod +x piper
    echo "✅ Piper downloaded"
else
    echo "✅ Piper already installed"
fi

# Download voice model
echo "Downloading voice model (en_US-lessac-medium)..."
cd "$MODEL_DIR"

if [ ! -f "en_US-lessac-medium.onnx" ]; then
    curl -L https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx -o en_US-lessac-medium.onnx
    curl -L https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json -o en_US-lessac-medium.onnx.json
    echo "✅ Voice model downloaded"
else
    echo "✅ Voice model already exists"
fi

echo ""
echo "=== Piper Installation Complete ==="
echo "Installed to: $INSTALL_DIR"
echo "Model: $MODEL_DIR/en_US-lessac-medium.onnx"
echo ""
echo "Test: echo 'Hello from Jarvis' | $INSTALL_DIR/piper --model $MODEL_DIR/en_US-lessac-medium.onnx --output_file test.wav"
echo ""
echo "✅ P6-06 Complete"
