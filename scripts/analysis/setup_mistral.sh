#!/bin/bash
# Setup Mistral Entity Disambiguation
# This script installs dependencies and runs initial tests

set -e  # Exit on error

echo "=========================================="
echo "Mistral Entity Disambiguation Setup"
echo "=========================================="

# Check Python version
echo ""
echo "Checking Python version..."
python3 --version

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python 3.9+ required. Found: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python version OK"

# Check available RAM
echo ""
echo "Checking system resources..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    TOTAL_RAM=$(sysctl -n hw.memsize | awk '{print int($1/1024/1024/1024)}')
    echo "Total RAM: ${TOTAL_RAM}GB"

    if [ "$TOTAL_RAM" -lt 16 ]; then
        echo "⚠️  Warning: 16GB+ RAM recommended. Found: ${TOTAL_RAM}GB"
        echo "   Model may run slowly or fail to load."
    else
        echo "✅ RAM sufficient"
    fi
else
    # Linux
    TOTAL_RAM=$(free -g | awk '/^Mem:/{print $2}')
    echo "Total RAM: ${TOTAL_RAM}GB"

    if [ "$TOTAL_RAM" -lt 16 ]; then
        echo "⚠️  Warning: 16GB+ RAM recommended. Found: ${TOTAL_RAM}GB"
    else
        echo "✅ RAM sufficient"
    fi
fi

# Install dependencies
echo ""
echo "Installing dependencies..."
echo ""

# Detect system and install appropriate torch
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS - use MPS support
    echo "Detected macOS - installing with Apple Silicon support"
    pip3 install torch torchvision torchaudio
else
    # Linux - check for CUDA
    if command -v nvidia-smi &> /dev/null; then
        echo "Detected NVIDIA GPU - installing with CUDA support"
        pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    else
        echo "No GPU detected - installing CPU-only version (will be slower)"
        pip3 install torch torchvision torchaudio
    fi
fi

# Install other dependencies
echo ""
echo "Installing transformers and dependencies..."
pip3 install -r /Users/masa/Projects/Epstein/requirements-mistral.txt

echo ""
echo "✅ Dependencies installed successfully"

# Download model (optional, will auto-download on first use)
echo ""
echo "=========================================="
echo "Model Download"
echo "=========================================="
echo ""
echo "The Mistral-7B-Instruct model (~14GB) will be downloaded on first use."
echo "Would you like to download it now? (y/n)"
read -r DOWNLOAD_NOW

if [ "$DOWNLOAD_NOW" = "y" ]; then
    echo ""
    echo "Downloading Mistral-7B-Instruct..."
    python3 -c "
from transformers import AutoTokenizer, AutoModelForCausalLM
print('Downloading model...')
tokenizer = AutoTokenizer.from_pretrained('mistralai/Mistral-7B-Instruct-v0.2')
model = AutoModelForCausalLM.from_pretrained('mistralai/Mistral-7B-Instruct-v0.2')
print('✅ Model downloaded successfully')
"
    echo "✅ Model cached locally"
else
    echo "⏭️  Skipping download - model will download on first use"
fi

# Run tests
echo ""
echo "=========================================="
echo "Running Test Cases"
echo "=========================================="
echo ""
echo "Would you like to run test cases? (y/n)"
echo "(This will test disambiguation on 'Ghislaine' and other known entities)"
read -r RUN_TESTS

if [ "$RUN_TESTS" = "y" ]; then
    echo ""
    echo "Running tests..."
    cd /Users/masa/Projects/Epstein
    python3 scripts/analysis/mistral_entity_disambiguator.py
else
    echo "⏭️  Skipping tests"
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Test the disambiguator:"
echo "   python3 scripts/analysis/mistral_entity_disambiguator.py"
echo ""
echo "2. Run batch disambiguation (high priority only):"
echo "   python3 scripts/analysis/batch_entity_disambiguation.py --priority high"
echo ""
echo "3. Dry run (preview without saving):"
echo "   python3 scripts/analysis/batch_entity_disambiguation.py --dry-run"
echo ""
echo "4. Process specific entities:"
echo "   python3 scripts/analysis/batch_entity_disambiguation.py --entities 'Ghislaine' 'Nadia'"
echo ""
