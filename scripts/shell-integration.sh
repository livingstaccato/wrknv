#!/bin/bash
#
# wrknv Shell Integration Script
# ===============================
# Sets up shell aliases and environment for wrknv development
#

# Detect shell type
CURRENT_SHELL=$(basename "$SHELL")
RC_FILE=""

case "$CURRENT_SHELL" in
    bash)
        RC_FILE="$HOME/.bashrc"
        ;;
    zsh)
        RC_FILE="$HOME/.zshrc"
        ;;
    *)
        echo "⚠️  Unsupported shell: $CURRENT_SHELL"
        echo "Please manually add the aliases to your shell configuration"
        exit 1
        ;;
esac

# Define aliases
ALIASES='
# wrknv aliases
alias wrknv="wrknv"
alias we="wrknv"  # Short alias

# Tool installation shortcuts
alias tf-install="wrknv tf"
alias tofu-install="wrknv tf"
alias terraform-install="wrknv terraform"
alias go-install="wrknv go"
alias uv-install="wrknv uv"

# Status and sync
alias wrknv-status="wrknv status"
alias wrknv-sync="wrknv sync"

# Container shortcuts
alias wrknv-container="wrknv container"
alias wec="wrknv container"  # Short alias (wrknv container)
alias wec-start="wrknv container start"
alias wec-enter="wrknv container enter"
alias wec-stop="wrknv container stop"
alias wec-status="wrknv container status"

# Package shortcuts
alias wrknv-build="wrknv package build"
alias wrknv-verify="wrknv package verify"
alias wrknv-publish="wrknv package publish"

# Development helpers
alias activate-wrknv="source $(wrknv env-path)/bin/activate 2>/dev/null || echo \"No wrknv virtual environment found\""
'

# Check if aliases already exist
if grep -q "# wrknv aliases" "$RC_FILE" 2>/dev/null; then
    echo "✅ wrknv aliases already configured in $RC_FILE"
else
    echo "📝 Adding wrknv aliases to $RC_FILE..."
    echo "$ALIASES" >> "$RC_FILE"
    echo "✅ Aliases added successfully!"
fi

# Display next steps
echo ""
echo "🎉 Shell integration complete!"
echo ""
echo "To activate the aliases, run:"
echo "  source $RC_FILE"
echo ""
echo "Available shortcuts:"
echo "  we              - Short for wrknv"
echo "  wec             - Short for wrknv container"
echo "  tf-install      - Install OpenTofu"
echo "  go-install      - Install Go"
echo "  wec-start       - Start development container"
echo "  wec-enter       - Enter development container"
echo ""
echo "Run 'alias | grep wrknv' to see all available aliases"