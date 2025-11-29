#!/bin/bash
#
# Shell Completion Installation Script for epstein-cli
# Automatically detects your shell and installs appropriate completions
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLI_SCRIPT="$PROJECT_ROOT/epstein-cli.py"

echo -e "${BLUE}Epstein CLI Shell Completion Installer${NC}"
echo "========================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 is not installed${NC}"
    exit 1
fi

# Check if argcomplete is installed
if ! python3 -c "import argcomplete" 2>/dev/null; then
    echo -e "${YELLOW}Installing argcomplete...${NC}"
    pip3 install argcomplete || {
        echo -e "${RED}Failed to install argcomplete${NC}"
        echo "Please run: pip3 install argcomplete"
        exit 1
    }
fi

# Detect shell
DETECTED_SHELL=""
if [ -n "$BASH_VERSION" ]; then
    DETECTED_SHELL="bash"
elif [ -n "$ZSH_VERSION" ]; then
    DETECTED_SHELL="zsh"
elif [ -n "$FISH_VERSION" ]; then
    DETECTED_SHELL="fish"
else
    # Try to detect from SHELL environment variable
    case "$SHELL" in
        */bash)
            DETECTED_SHELL="bash"
            ;;
        */zsh)
            DETECTED_SHELL="zsh"
            ;;
        */fish)
            DETECTED_SHELL="fish"
            ;;
        *)
            echo -e "${YELLOW}Could not detect shell automatically${NC}"
            ;;
    esac
fi

# Allow override via argument
if [ -n "$1" ]; then
    DETECTED_SHELL="$1"
fi

if [ -z "$DETECTED_SHELL" ]; then
    echo "Usage: $0 [bash|zsh|fish]"
    echo ""
    echo "Please specify your shell, or run this script from within your shell"
    exit 1
fi

echo -e "Detected shell: ${GREEN}$DETECTED_SHELL${NC}"
echo ""

# Generate completions
echo -e "${YELLOW}Generating $DETECTED_SHELL completions...${NC}"
python3 "$CLI_SCRIPT" --install-completion "$DETECTED_SHELL"

echo ""
echo -e "${GREEN}✓ Completions generated successfully!${NC}"
echo ""

# Provide activation instructions based on shell
case "$DETECTED_SHELL" in
    bash)
        echo -e "${BLUE}Bash Activation Instructions:${NC}"
        echo "1. Add to ~/.bashrc:"
        echo ""
        echo "    source $PROJECT_ROOT/completions/epstein-cli.bash"
        echo ""
        echo "2. Reload your shell:"
        echo ""
        echo "    source ~/.bashrc"
        echo ""
        echo "OR install system-wide (requires sudo):"
        echo ""
        echo "    sudo cp $PROJECT_ROOT/completions/epstein-cli.bash /etc/bash_completion.d/"
        ;;

    zsh)
        echo -e "${BLUE}Zsh Activation Instructions:${NC}"
        echo "1. Add to ~/.zshrc (before compinit):"
        echo ""
        echo "    fpath=($PROJECT_ROOT/completions \$fpath)"
        echo "    autoload -U compinit && compinit"
        echo ""
        echo "2. Reload your shell:"
        echo ""
        echo "    source ~/.zshrc"
        echo ""
        echo "OR copy to user completions:"
        echo ""
        echo "    mkdir -p ~/.zsh/completions"
        echo "    cp $PROJECT_ROOT/completions/_epstein-cli ~/.zsh/completions/"
        echo "    # Add to ~/.zshrc: fpath=(~/.zsh/completions \$fpath)"
        ;;

    fish)
        echo -e "${BLUE}Fish Activation Instructions:${NC}"
        echo "1. Copy to fish completions directory:"
        echo ""
        echo "    mkdir -p ~/.config/fish/completions"
        echo "    cp $PROJECT_ROOT/completions/epstein-cli.fish ~/.config/fish/completions/"
        echo ""
        echo "2. Completions will activate automatically on next shell start"
        echo ""
        echo "OR install system-wide (requires sudo):"
        echo ""
        echo "    sudo cp $PROJECT_ROOT/completions/epstein-cli.fish /usr/share/fish/vendor_completions.d/"
        ;;
esac

echo ""
echo -e "${GREEN}Installation complete!${NC}"
echo ""
echo "Test your completions:"
echo "  $ epstein-cli [TAB]"
echo "  $ epstein-cli search --[TAB]"
echo ""
