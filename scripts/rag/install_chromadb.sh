#!/bin/bash
# ChromaDB RAG System Installation Script
# Epstein Document Archive - RAG Dependencies

set -e

echo "=== ChromaDB RAG System Installation ==="
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"

# Install core dependencies
echo ""
echo "[1/4] Installing ChromaDB..."
pip install chromadb==0.4.22

echo ""
echo "[2/4] Installing sentence-transformers..."
pip install sentence-transformers==2.2.2

echo ""
echo "[3/4] Installing PyTorch (CPU version for efficiency)..."
pip install torch==2.1.2 --index-url https://download.pytorch.org/whl/cpu

echo ""
echo "[4/4] Installing additional dependencies..."
pip install tqdm pydantic fastapi uvicorn

echo ""
echo "=== Installation Summary ==="
echo "✅ ChromaDB: Vector database"
echo "✅ sentence-transformers: Embedding generation (all-MiniLM-L6-v2)"
echo "✅ PyTorch: ML framework (CPU-optimized)"
echo "✅ Additional tools: tqdm, pydantic, fastapi, uvicorn"

echo ""
echo "=== Verifying Installation ==="
python3 -c "import chromadb; print(f'ChromaDB version: {chromadb.__version__}')"
python3 -c "import sentence_transformers; print(f'sentence-transformers version: {sentence_transformers.__version__}')"
python3 -c "import torch; print(f'PyTorch version: {torch.__version__}')"

echo ""
echo "=== Installation Complete ==="
echo "Next steps:"
echo "  1. Run: python3 scripts/rag/build_vector_store.py"
echo "  2. Wait ~5-6 hours for 33,562 documents to be embedded"
echo "  3. Test: python3 scripts/rag/query_rag.py --query 'your query'"
