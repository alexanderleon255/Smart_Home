#!/bin/bash
# P6-05: whisper.cpp Setup

set -e

echo "=== whisper.cpp Installation (P6-05) ==="

INSTALL_DIR="$HOME/.local/whisper.cpp"
MODEL_DIR="$INSTALL_DIR/models"

# Install build dependencies
echo "Installing build dependencies..."
brew install cmake

# Clone whisper.cpp
if [ -d "$INSTALL_DIR" ]; then
    echo "✅ whisper.cpp already cloned"
    cd "$INSTALL_DIR"
    git pull
else
    echo "Cloning whisper.cpp..."
    git clone https://github.com/ggerganov/whisper.cpp.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# Build
echo "Building whisper.cpp..."
make

# Download model
mkdir -p "$MODEL_DIR"
echo "Downloading Whisper small model..."
if [ ! -f "$MODEL_DIR/ggml-small.bin" ]; then
    bash ./models/download-ggml-model.sh small
    echo "✅ Model downloaded"
else
    echo "✅ Model already exists"
fi

echo ""
echo "=== whisper.cpp Installation Complete ==="
echo "Installed to: $INSTALL_DIR"
echo "Model: $MODEL_DIR/ggml-small.bin"
echo ""
echo "Test: $INSTALL_DIR/main -m $MODEL_DIR/ggml-small.bin -f <audio.wav>"
echo ""
echo "✅ P6-05 Complete"
