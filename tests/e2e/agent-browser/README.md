# Agent-Browser E2E Tests

End-to-end tests for the TradeLogger desktop widget using agent-browser to connect directly to the Electron app.

## Why agent-browser?

- Tests the **actual Electron app** (not a file:// URL)
- More reliable - same environment as production
- Can take real screenshots of the desktop app
- Better for testing Electron-specific features

## Prerequisites

1. **Flask backend running:**
   ```bash
   cd /home/ekkemboi/PROJECTS/TradeLogger
   python -m src.app
   ```

2. **agent-browser installed:**
   ```bash
   which agent-browser
   # Should return: /home/ekkemboi/.bun/bin/agent-browser
   ```

## Running Tests

### Option 1: Shell Script (Recommended)

```bash
# From project root
bash tests/e2e/agent-browser/run.sh
```

This will:
1. Check Flask is running
2. Start Electron with remote debugging (port 9222)
3. Connect agent-browser to Electron
4. Run interactive tests
5. Take screenshots
6. Clean up

### Option 2: Python pytest

```bash
# From project root
pytest tests/e2e/agent-browser/test_widget.py -v -s
```

## Test Commands

### Manual Testing

```bash
# Start Electron
cd desktop
bun start -- --remote-debugging-port=9222

# In another terminal - connect and test
agent-browser connect 9222

# Get snapshot (shows all elements with refs)
agent-browser snapshot -i

# Take screenshot
agent-browser screenshot widget.png

# Click element
agent-browser click @e5

# Fill form
agent-browser fill #entry-price 50000

# Select dropdown
agent-browser select #account-select 1

# Get text
agent-browser get text #status-message

# Get HTML
agent-browser get html #status-message
```

## Output

Screenshots are saved to:
- `tests/e2e/agent-browser/screenshots/widget.png`

## Troubleshooting

### "Connection refused"

- Make sure Electron started with `--remote-debugging-port=9222`
- Wait longer for app to start (try 10 seconds)
- Check port: `lsof -i :9222`

### "Element not found"

- Use `agent-browser snapshot -i` to see current element tree
- Element refs change each snapshot - note new refs

### Tests fail

- Check Flask is running: `curl http://localhost:5000/api/accounts`
- Check browser console: Look for CORS or network errors
