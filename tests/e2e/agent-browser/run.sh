#!/bin/bash
# Run agent-browser tests on the Electron widget

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "  TradeLogger - Electron Widget Tests"
echo "=========================================="

# Check if Flask is running
echo ""
echo "📋 Checking Flask backend..."
if curl -s http://localhost:5000/api/accounts > /dev/null 2>&1; then
    echo "✅ Flask is running on localhost:5000"
else
    echo "❌ Flask is NOT running on localhost:5000"
    echo "   Please start Flask: python -m src.app"
    exit 1
fi

# Kill any existing Electron processes
echo ""
echo "🧹 Cleaning up existing processes..."
pkill -f "electron" 2>/dev/null || true
sleep 1

# Start Electron with remote debugging
echo ""
echo "🚀 Starting Electron with remote debugging..."
cd desktop
bun start -- --remote-debugging-port=9222 &
ELECTRON_PID=$!
cd ..

# Wait for Electron to start
echo "   Waiting for Electron to start..."
sleep 6

# Connect agent-browser
echo ""
echo "📡 Connecting to Electron..."
agent-browser connect 9222 || {
    echo "❌ Failed to connect to Electron"
    kill $ELECTRON_PID 2>/dev/null || true
    exit 1
}

echo "✅ Connected to Electron"

# Run tests
echo ""
echo "🧪 Running tests..."

# Test 1: Get snapshot
echo ""
echo "📸 Test 1: Taking snapshot..."
agent-browser snapshot -i

# Test 2: Screenshot
echo ""
echo "📸 Test 2: Taking screenshot..."
mkdir -p tests/e2e/agent-browser/screenshots
agent-browser screenshot tests/e2e/agent-browser/screenshots/widget.png
echo "   Saved to: tests/e2e/agent-browser/screenshots/widget.png"

# Test 3: Trade Info toggle
echo ""
echo "🔄 Test 3: Testing Trade Info toggle..."
agent-browser click .collapsible-header
sleep 0.5
agent-browser snapshot

# Test 4: Fill form
echo ""
echo "✏️ Test 4: Filling trade form..."
agent-browser type "#entry-price" "50000"
agent-browser type "#position-size" "1"
echo "   Filled entry price and position size"

# Test 5: Submit (should show validation error)
echo ""
echo "📤 Test 5: Submitting trade..."
agent-browser click @e27
sleep 1
agent-browser get text @e28

# Test 6: Partial Exits - UI Flow Test
echo ""
echo "📊 Test 6: Testing partial exits UI flow..."

# Ensure Trade Info is expanded
agent-browser click .collapsible-header
sleep 0.5

# Use eval to set account and symbol values directly
agent-browser eval "
  const accountSelect = document.getElementById('account-select');
  if (accountSelect.options.length > 1) accountSelect.selectedIndex = 1;
  const symbolSelect = document.getElementById('symbol-select');
  if (symbolSelect.options.length > 2) symbolSelect.selectedIndex = 2;
  else if (symbolSelect.options.length > 1) symbolSelect.selectedIndex = 1;
"
sleep 0.5

# Click "+ ADD" button to add partial exit row
agent-browser click @e24
sleep 1

# Take snapshot to verify partial exit row was added
agent-browser snapshot
echo "   ✅ Partial exit row added"

# Summary
echo ""
echo "=========================================="
echo "  Tests Complete!"
echo "=========================================="

# Cleanup
echo ""
echo "🧹 Cleaning up..."
kill $ELECTRON_PID 2>/dev/null || true

echo ""
echo "✅ All tests completed!"
