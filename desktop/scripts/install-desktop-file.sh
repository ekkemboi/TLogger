#!/bin/bash
# Install TradeLogger .desktop file for Linux protocol support

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_FILE="$SCRIPT_DIR/../build/tradelogger.desktop"

# Determine app path - use provided path or detect
if [ -n "$1" ]; then
    APP_PATH="$1"
else
    # Try to detect the app path
    if [ -f "$SCRIPT_DIR/../../dist/linux-unpacked/tradelogger" ]; then
        APP_PATH="$SCRIPT_DIR/../../dist/linux-unpacked/tradelogger"
    elif [ -f "/usr/bin/tradelogger" ]; then
        APP_PATH="/usr/bin/tradelogger"
    else
        echo "Error: Could not detect TradeLogger executable path"
        echo "Usage: $0 /path/to/tradelogger"
        exit 1
    fi
fi

echo "Installing TradeLogger desktop file..."
echo "App path: $APP_PATH"

# Create user applications directory if it doesn't exist
mkdir -p ~/.local/share/applications

# Copy and customize the desktop file
sed "s|Exec=/usr/bin/tradelogger|Exec=$APP_PATH|g" "$DESKTOP_FILE" > ~/.local/share/applications/tradelogger.desktop

# Register the protocol handler
xdg-mime default tradelogger.desktop x-scheme-handler/tradelogger

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database ~/.local/share/applications
fi

echo "✓ TradeLogger protocol handler installed"
echo "  - Protocol: tradelogger://"
echo "  - Desktop file: ~/.local/share/applications/tradelogger.desktop"
echo ""
echo "Test with: xdg-open 'tradelogger://auth?code=test123'"
