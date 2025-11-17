#!/bin/bash
#
# Epstein Archive - Script Runner
# Automatically sets up and uses project virtual environment
#

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv"
REQUIREMENTS="$PROJECT_ROOT/requirements.txt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Epstein Document Archive - Script Runner${NC}"
echo "==========================================="

# Check if venv exists
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv "$VENV_DIR"
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate venv
source "$VENV_DIR/bin/activate"

# Check/install requirements
if [ -f "$REQUIREMENTS" ]; then
    echo "Checking requirements..."
    pip install -q -r "$REQUIREMENTS" > /dev/null 2>&1 || {
        echo -e "${YELLOW}Installing requirements...${NC}"
        pip install -r "$REQUIREMENTS"
    }
    echo -e "${GREEN}✓ Requirements satisfied${NC}"
fi

# If no arguments, show menu
if [ $# -eq 0 ]; then
    echo ""
    echo "Usage: ./run.sh <command> [args...]"
    echo ""
    echo "Available Commands:"
    echo "-------------------"
    echo ""
    echo "Analysis:"
    echo "  disambiguate          - Find and merge duplicate entities"
    echo "  entity-stats          - Generate entity statistics report"
    echo "  network               - Rebuild entity relationship network"
    echo "  timeline              - Build timeline from dated documents"
    echo ""
    echo "Classification:"
    echo "  classify              - Classify all documents"
    echo "  classify-status       - Show classification statistics"
    echo ""
    echo "Search:"
    echo "  search-entity <name>  - Search by entity name"
    echo "  search-connections <name> - Show entity connections"
    echo "  search-type <type>    - Search by document type"
    echo ""
    echo "Extraction:"
    echo "  ocr-status            - Check OCR progress"
    echo "  extract-emails        - Extract emails from OCR results"
    echo ""
    echo "Visualization:"
    echo "  visualize-network     - Generate network visualization"
    echo "  visualize-timeline    - Generate timeline visualization"
    echo ""
    echo "Examples:"
    echo "  ./run.sh search-entity \"Clinton\""
    echo "  ./run.sh search-connections \"Ghislaine\""
    echo "  ./run.sh ocr-status"
    echo ""
    exit 0
fi

COMMAND=$1
shift

case "$COMMAND" in
    # Analysis
    disambiguate)
        python3 "$PROJECT_ROOT/scripts/analysis/entity_disambiguator.py" "$@"
        ;;
    entity-stats)
        python3 "$PROJECT_ROOT/scripts/analysis/entity_statistics.py" "$@"
        ;;
    network)
        python3 "$PROJECT_ROOT/scripts/analysis/rebuild_flight_network.py" "$@"
        ;;
    timeline)
        python3 "$PROJECT_ROOT/scripts/analysis/timeline_builder.py" "$@"
        ;;

    # Classification
    classify)
        python3 "$PROJECT_ROOT/scripts/classification/classify_all_documents.py" "$@"
        ;;
    classify-status)
        python3 "$PROJECT_ROOT/scripts/classification/classification_status.py" "$@"
        ;;

    # Search
    search-entity)
        python3 "$PROJECT_ROOT/scripts/search/entity_search.py" --entity "$@"
        ;;
    search-connections)
        python3 "$PROJECT_ROOT/scripts/search/entity_search.py" --connections "$@"
        ;;
    search-type)
        python3 "$PROJECT_ROOT/scripts/search/entity_search.py" --type "$@"
        ;;

    # Extraction
    ocr-status)
        python3 "$PROJECT_ROOT/scripts/extraction/check_ocr_status.py" "$@"
        ;;
    extract-emails)
        python3 "$PROJECT_ROOT/scripts/extraction/extract_emails.py" "$@"
        ;;

    # Visualization
    visualize-network)
        python3 "$PROJECT_ROOT/scripts/visualization/network_visualizer.py" "$@"
        ;;
    visualize-timeline)
        python3 "$PROJECT_ROOT/scripts/visualization/timeline_visualizer.py" "$@"
        ;;

    # Unknown command
    *)
        echo -e "${RED}Unknown command: $COMMAND${NC}"
        echo "Run './run.sh' without arguments to see available commands"
        exit 1
        ;;
esac
