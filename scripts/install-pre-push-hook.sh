#!/bin/bash
# Script to install the pre-push hook
# This creates a symlink from .git/hooks/pre-push to scripts/pre-push-hook.sh

set -e

# Get the project root directory (where this script is located)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
HOOK_SOURCE="$PROJECT_ROOT/scripts/pre-push-hook.sh"
HOOK_TARGET="$PROJECT_ROOT/.git/hooks/pre-push"

# Check if we're in a git repository
if [ ! -d "$PROJECT_ROOT/.git" ]; then
    echo "Error: Not in a git repository"
    exit 1
fi

# Check if hook source exists
if [ ! -f "$HOOK_SOURCE" ]; then
    echo "Error: Hook script not found at $HOOK_SOURCE"
    exit 1
fi

# Make hook script executable
chmod +x "$HOOK_SOURCE"

# Create .git/hooks directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/.git/hooks"

# Remove existing hook if it exists
if [ -f "$HOOK_TARGET" ] || [ -L "$HOOK_TARGET" ]; then
    echo "Removing existing pre-push hook..."
    rm "$HOOK_TARGET"
fi

# Create symlink (or copy on Windows if symlinks don't work)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows: copy instead of symlink
    echo "Installing pre-push hook (Windows)..."
    cp "$HOOK_SOURCE" "$HOOK_TARGET"
    chmod +x "$HOOK_TARGET"
else
    # Unix: create symlink
    echo "Installing pre-push hook (Unix)..."
    ln -s "$HOOK_SOURCE" "$HOOK_TARGET"
    chmod +x "$HOOK_TARGET"
fi

echo "✓ Pre-push hook installed successfully!"
echo ""
echo "NOTE: This hook is currently disabled. Tests should be run manually."
echo "To run tests manually:"
echo "  python scripts/run-wiki-tests.py"
echo "  (or: bash scripts/run-wiki-tests.sh)"
echo ""
echo "To skip the hook: git push --no-verify"
