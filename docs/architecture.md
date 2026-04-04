# TradeLogger - Architecture Document

## System Overview

TradeLogger is a trade logging system that captures trades from TradingView via Chrome DevTools Protocol (CDP), stores them in PostgreSQL, and provides a web dashboard for analysis.

## Components

### 1. Desktop Widget (Electron + Bun)
- Connects to Chrome via CDP to read TradingView trade panel
- Shows editable form with extracted trade data
- Auto-captures screenshot on confirmation
- Sends confirmed trade to Flask backend via API

### 2. Backend (Flask + SQLAlchemy + Flask-SocketIO)
- REST API for trade CRUD operations
- WebSocket for real-time updates
- Screenshot storage management
- Metrics calculation

### 3. Database (PostgreSQL)
- Trade storage with full trade details
- Indexes for efficient querying
- Support for tags and notes

### 4. Web Dashboard (Flask + Jinja2 + HTMX + Tailwind CSS + Chart.js)
- **Layout**: Left sidebar (260px) with persistent navigation
- **Navigation**: HTMX-powered SPA-like behavior (no full page reloads)
- **Styling**: Tailwind CSS with green primary color (#22C55E)
- **Typography**: System font stack (ui-sans-serif, system-ui, sans-serif)
- **Features**:
  - Metrics dashboard (win rate, P&L, profit factor)
  - Trade history with filtering
  - Trade detail view with screenshot
  - Favorites management for quick product selection

## Data Flow

### Trade Capture Flow

```
1. User places trade on TradingView
2. Electron widget connects to Chrome via CDP
3. Widget reads trade panel DOM → extracts values
4. Widget shows editable form
5. User verifies/edits → clicks Confirm
6. Widget auto-captures screenshot
7. Trade + screenshot sent to Flask backend
8. Flask stores in PostgreSQL
9. Web dashboard displays metrics and history
```

### HTMX Navigation Flow

```
1. User clicks sidebar link
2. HTMX intercepts click via hx-get attribute
3. HTMX makes AJAX request with withCredentials: true
4. Server detects HTMX request via HX-Request: true header
5. Server returns only content block (no sidebar/header)
6. HTMX swaps content in <main> element (hx-target="main")
7. URL updates via hx-push-url="true"
8. JavaScript re-initializes page-specific handlers
9. Sidebar and global state persist across navigation
```

## HTMX Navigation

### Overview
The v2 sidebar redesign uses HTMX for SPA-like navigation without full page reloads. This provides a smoother user experience while maintaining server-side rendering benefits.

### Navigation Pattern

**Sidebar Links:**
```html
<a href="/trades"
   hx-get="/trades"
   hx-target="main"
   hx-push-url="true">
  Trades
</a>
```

**Key Attributes:**
- `hx-get`: Makes AJAX GET request instead of full navigation
- `hx-target="main"`: Swaps content only inside the `<main>` element
- `hx-push-url="true"`: Updates browser URL for history/refresh support

### Template Structure

**base.html** uses conditional rendering based on request type:

```html
{% if not htmx_request %}
  <!-- Full page: sidebar, header, scripts -->
  <aside class="sidebar">...</aside>
  <main>{% block content %}{% endblock %}</main>
  <script>...</script>
{% else %}
  <!-- HTMX request: content only -->
  <main>{% block content %}{% endblock %}</main>
{% endif %}
```

**HTMX Request Detection:**
```python
@app.context_processor
def inject_htmx():
    return {"htmx_request": request.headers.get("HX-Request") == "true"}
```

### Configuration

**withCredentials Setup:**
```javascript
document.body.addEventListener('htmx:configRequest', function(evt) {
    evt.detail.withCredentials = true;
});
```

This ensures authentication cookies are sent with all HTMX requests.

### Benefits

1. **Performance**: Only content area refreshes, not entire page
2. **State Persistence**: Sidebar state, scroll position preserved
3. **History**: Browser back/forward buttons work correctly
4. **Progressive Enhancement**: Works without JavaScript (falls back to full page loads)
5. **Server-Side Rendering**: Maintains SEO and accessibility benefits

### Considerations

- **JavaScript Re-initialization**: Page-specific scripts must re-run after content swap
- **Event Handlers**: Use event delegation or re-attach handlers after HTMX swaps
- **Meta Tags**: Title updates require `hx-swap-oob` or manual handling

## HTMX Considerations

### Authentication with HTMX
All HTMX requests must include authentication cookies. This is configured via the `htmx:configRequest` event:

```javascript
document.body.addEventListener('htmx:configRequest', function(evt) {
    evt.detail.withCredentials = true;
});
```

### Server-Side Detection
The backend detects HTMX requests via the `HX-Request` header:

```python
@app.context_processor
def inject_htmx():
    return {"htmx_request": request.headers.get("HX-Request") == "true"}
```

### Out-of-Band (OOB) Updates
For updating elements outside the main content area (e.g., flash messages, account dropdown):

```html
<!-- In the response -->
<div id="flash-messages" hx-swap-oob="true">
  <div class="alert">Trade saved!</div>
</div>
<main><!-- Main content --></main>
```

### Event Handling
Use `htmx:afterSwap` to re-initialize JavaScript after content loads:

```javascript
document.body.addEventListener('htmx:afterSwap', function(evt) {
    if (evt.detail.target.tagName === 'MAIN') {
        initPageSpecificScripts();
    }
});
```

### Testing HTMX Navigation
The E2E tests verify:
1. Sidebar links trigger AJAX requests (not full page loads)
2. Only `<main>` content is swapped
3. URL updates correctly via `hx-push-url`
4. Authentication cookies are sent with requests
5. Browser back/forward buttons work

## API Design

### Trade Endpoints

```
POST   /api/trades              -- Create trade (with screenshot upload)
GET    /api/trades              -- List trades (filters: symbol, direction, date range)
GET    /api/trades/:id          -- Get single trade with screenshot
PUT    /api/trades/:id          -- Update trade (notes, tags, exit_price, fees)
DELETE /api/trades/:id          -- Delete trade
GET    /api/trades/pending      -- List trades without exit (open positions)
```

### Metrics Endpoint

```
GET    /api/metrics             -- Trading metrics (win rate, P&L, stats)
```

## Database Schema

```sql
CREATE TYPE trade_direction AS ENUM ('long', 'short');
CREATE TYPE trade_status AS ENUM ('pending', 'confirmed', 'closed');

CREATE TABLE trades (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol          VARCHAR(50) NOT NULL,
    direction       trade_direction NOT NULL,
    entry_price     DECIMAL(18, 8) NOT NULL,
    exit_price      DECIMAL(18, 8),
    stop_loss       DECIMAL(18, 8),
    take_profit     DECIMAL(18, 8),
    position_size   DECIMAL(18, 8),
    status          trade_status NOT NULL DEFAULT 'confirmed',
    pnl             DECIMAL(18, 8),
    fees            DECIMAL(18, 8) DEFAULT 0,
    trade_duration  INTERVAL,
    notes           TEXT,
    tags            TEXT[],
    screenshot_path VARCHAR(500),
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    confirmed_at    TIMESTAMP WITH TIME ZONE,
    exited_at       TIMESTAMP WITH TIME ZONE,
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_trades_status ON trades(status);
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_created_at ON trades(created_at);
CREATE INDEX idx_trades_direction ON trades(direction);
```

## New Files (v2 Sidebar Redesign)

### Template Partials

| File | Purpose |
|------|---------|
| `web/templates/partials/account_dropdown.html` | User account dropdown for out-of-band (OOB) updates |
| `web/templates/partials/navlink.html` | Reusable navigation link with HTMX attributes |

### E2E Tests

| File | Purpose |
|------|---------|
| `tests/e2e/test_htmx_navigation.py` | End-to-end tests for HTMX navigation behavior |
| `tests/e2e/test_sidebar.py` | Sidebar interaction and persistence tests |

### Styling

| File | Purpose |
|------|---------|
| `web/static/css/sidebar-v2.css` | v2 sidebar-specific styles |
| `web/static/js/htmx-config.js` | HTMX global configuration |

## Technology Decisions

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Backend | Flask + SQLAlchemy | Simple, proven, good ORM |
| Database | PostgreSQL | Robust, supports arrays (tags), good for analytics |
| Desktop | Electron + Bun | Cross-platform, Bun for speed |
| Web Frontend | Jinja2 + HTMX + Tailwind CSS + Chart.js | Server-rendered with SPA-like UX, fast styling, good charting |
| HTMX | 2.x | Progressive enhancement, minimal JS, AJAX navigation |
| Package Manager | uv (Python), Bun (JS) | Fast, modern |

## Security Considerations

- **CDP Access**: Chrome debugging port only accessible locally
- **API Authentication**: Add API key for production deployment
- **Screenshot Storage**: Local filesystem, not exposed publicly
- **SQL Injection**: SQLAlchemy ORM prevents this
- **CORS**: Restrict to localhost for Electron widget

## Infrastructure (Development)

- **Development**: localhost:5000 (Flask), localhost:3000 (Electron)
- **Database**: Local PostgreSQL instance
- **Screenshots**: Local filesystem in ~/PROJECTS/TradeLogger/screenshots/

## Future Considerations

- VPS deployment for 24/7 access
- Notion integration for trade export
- Multiple account support
- Trade tagging and filtering
- Export to CSV/Excel
