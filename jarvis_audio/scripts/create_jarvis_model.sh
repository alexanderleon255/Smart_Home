#!/bin/bash
# P6-07: Create Jarvis Ollama Model

set -e

echo "=== Creating Jarvis Ollama Model (P6-07) ==="

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "Error: Ollama not installed"
    echo "Install from: https://ollama.ai"
    exit 1
fi

# Check if base model exists
echo "Checking for base model (llama3.1:8b-instruct)..."
if ! ollama list | grep -q "llama3.1:8b-instruct"; then
    echo "Pulling base model..."
    ollama pull llama3.1:8b-instruct
fi

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MODELFILE="$SCRIPT_DIR/../Modelfile.jarvis"

# Create Jarvis model
echo "Creating Jarvis model..."
ollama create jarvis -f "$MODELFILE"

echo ""
echo "=== Testing Jarvis Model ==="
echo "Running test query..."
ollama run jarvis "Hello, what can you do?" --verbose

echo ""
echo "=== Jarvis Model Created Successfully ==="
echo "Run: ollama run jarvis"
echo "Test: ollama run jarvis 'Turn on the living room light'"
echo ""
echo "✅ P6-07 Complete"
