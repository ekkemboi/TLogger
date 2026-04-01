# TradeLogger UI Specification

A comprehensive design specification for the TradeLogger trading journal application. Use this document to recreate the UI in any design tool or frontend framework.

---

## Table of Contents

1. [Design System](#design-system)
2. [Navigation](#navigation)
3. [Dashboard Page](#dashboard-page)
4. [Trades Page](#trades-page)
5. [Accounts Page](#accounts-page)
6. [Components](#components)
7. [API Endpoints](#api-endpoints)

---

## Design System

### Color Palette

| Name | Hex Code | Usage |
|------|----------|-------|
| `bg-primary` | `#18181B` | Main page background |
| `bg-secondary` | `#0F0F10` | Cards, navigation background |
| `bg-surface` | `#141415` | Input fields, table rows |
| `text-primary` | `#FAFAFA` | Main text content |
| `text-secondary` | `#71717A` | Labels, placeholders, secondary text |
| `text-tertiary` | `#52525B` | Disabled states |
| `accent-primary` | `#FACC15` | Primary actions, highlights, active states |
| `success` | `#22C55E` | Positive values, winning trades |
| `error` | `#EF4444` | Negative values, losing trades, errors |
| `warning` | `#FACC15` | Warnings (same as accent) |
| `border-default` | `#27272A` | Borders, dividers, card outlines |

### Typography

| Font Family | Usage |
|-------------|-------|
| `JetBrains Mono` | Body text, labels, table cells, input fields, buttons |
| `Space Grotesk` | Page headings, metric values, large numbers |

**Font Sizes:**

| Element | Size | Weight |
|---------|------|--------|
| Page title | 24px (text-2xl) | Bold |
| Metric value | 20px (text-xl) | Bold (700) |
| Table cell | 13px (text-xs) | Normal (400) |
| Label | 10px (text-[10px]) | Semibold (600) |
| Small label | 9px (text-[9px]) | Semibold (600) |
| Badge | 10px (text-[10px]) | Bold (700) |

### Spacing System

| Token | Value | Usage |
|-------|-------|-------|
| Canvas width | 1440px | Desktop viewport |
| Content padding | 40px | Horizontal padding (px-10) |
| Section gap | 16px | Between major sections |
| Card padding | 12px | Inside cards (p-3) |
| Grid gap | 12px | Between grid items (gap-3) |
| Input padding | 8px 12px | Inside input fields |
| Button padding | 10px 18px | Inside buttons |

---

## Navigation

### Structure

```
+------------------------------------------------------------------+
|  [■]    TRADELOGGER     01 Dashboard   02 Trades   ...   [▼]   |
|                                          [Account Selector]        |
+------------------------------------------------------------------+
```

### Navigation Items

| Position | Label | Route | Number Badge |
|----------|-------|-------|--------------|
| 01 | Dashboard | `/` | 01 |
| 02 | Trades | `/trades` | 02 |
| 03 | Favorites | `/favorites` | 03 |
| 04 | Accounts | `/accounts` | 04 |

### Account Switcher

- Located in top-right corner of navigation
- Dropdown select element
- Default option: "All Accounts"
- Selection persists to localStorage
- Triggers `accountChanged` custom event on change for pages to reload data

---

## Dashboard Page

### Page Header

```
+--------------------------------------------------+
|  Dashboard                                       |
|  Monitor your trading performance and metrics    |
|                                     [FROM] [TO]  |
+--------------------------------------------------+
```

- Title: "Dashboard" (Space Grotesk, 24px, bold)
- Subtitle: "Monitor your trading performance and metrics" (text-secondary)
- Date filters: Two date inputs for date range filtering

---

### Metrics Section

Two rows of 4 metric cards each (8 total).

**Row 1:**

| Label | Element ID | Format | Color |
|-------|------------|--------|-------|
| TOTAL TRADES | `#total-trades` | Integer | White |
| WIN RATE | `#win-rate` | Percentage (e.g., "62.5%") | Green if >50% |
| TOTAL P&L | `#total-pnl` | Currency (e.g., "+$32,332.98") | Green/Red based on value |
| PROFIT FACTOR | `#profit-factor` | Decimal (e.g., "3.09") | White |

**Row 2:**

| Label | Element ID | Format | Color |
|-------|------------|--------|-------|
| AVG WIN | `#avg-win` | Currency | Green |
| AVG LOSS | `#avg-loss` | Currency | Red |
| BEST TRADE | `#best-trade` | Currency | Green |
| WORST TRADE | `#worst-trade` | Currency | Red |

**Card Structure:**
```html
<div class="card p-3">
  <p class="label text-[10px]">TOTAL TRADES</p>
  <p class="metric-value text-xl mt-1">56</p>
</div>
```

---

### Charts Section

**Layout:** 3-column grid with 2:1 ratio

```
+------------------------------------------+--------+
|                                          |        |
|          EQUITY CURVE                    | RECENT |
|          (Line Chart)                    |   P&L  |
|                                          | (Bar)  |
+------------------------------------------+--------+
```

#### Equity Curve (Line Chart)
- **Type:** Line chart with filled area
- **Border Color:** `#FACC15` (accent yellow)
- **Fill:** `rgba(250, 204, 21, 0.1)` (10% opacity yellow)
- **Tension:** 0.1 (slight curve)
- **Point Radius:** 0 (no dots on data points)
- **Grid Lines:** `#27272A`, 0.5px width
- **Y-Axis:** Currency format (e.g., "$50000")
- **X-Axis:** Trade number (1, 2, 3...)

#### Recent P&L (Bar Chart)
- **Type:** Vertical bar chart
- **Positive Bars:** `rgba(34, 197, 94, 0.7)` fill, `#22C55E` border
- **Negative Bars:** `rgba(239, 68, 68, 0.7)` fill, `#EF4444` border
- **Border Width:** 1px
- **Grid:** Same as equity curve

---

### By Symbol & Recent Activity

**Layout:** 2-column grid, fixed height `h-32` (128px)

#### Left Column - By Symbol
- **Doughnut Chart:** 80x80px, no legend
- **Legend:** 3-column grid with scroll (max-height: 96px)
- **Legend Items:** Color dot (8x8px) | Symbol name | Trade count

**Symbol Colors (in order):**
```javascript
[
  '#FACC15',  // Yellow
  '#22C55E',  // Green
  '#3B82F6',  // Blue
  '#EF4444',  // Red
  '#8B5CF6',  // Purple
  '#EC4899',  // Pink
  '#06B6D4',  // Cyan
  '#F97316'   // Orange
]
```

#### Right Column - Recent Activity
- Shows 2 most recent closed trades
- Each row displays:
  - Symbol name (bold)
  - Direction badge (LONG/SHORT)
  - P&L value (green/red colored)
- "View More →" link at bottom-right (links to `/trades`)

---

## Trades Page

### Table Structure

| Column | Width | Content |
|--------|-------|---------|
| ACCOUNT | fill | Account name |
| SYMBOL | 80px | Trading symbol (e.g., BTCUSDT) |
| DIRECTION | 60px | LONG or SHORT badge |
| ENTRY | 100px | Entry price |
| TAKE PROFIT | 100px | Target price |
| P&L | 100px | Profit/Loss (colored) |
| STATUS | 80px | CONFIRMED or CLOSED badge |
| DATE | 100px | Trade date (YYYY-MM-DD) |
| ACTIONS | 80px | Edit/Delete links |

### Features
- Search/filter by symbol, direction, status
- Pagination controls
- Sort by any column

---

## Accounts Page

### Table Structure

| Column | Width | Content |
|--------|-------|---------|
| ACCOUNT | fill | Account name |
| TRADES | 100px | Number of trades |
| TOTAL P&L | 120px | Total P&L for account |
| WIN RATE | 100px | Win percentage |
| OPENING BALANCE | 100px | Starting balance |
| STATUS | 80px | ACTIVE or INACTIVE badge |
| ACTIONS | 80px | Edit/Delete links |

### Add Account Modal

```
+--------------------------------+
|  New Account                   |
|                                |
|  ACCOUNT NAME                  |
|  [________________________]    |
|                                |
|  OPENING BALANCE               |
|  [________________________]    |
|                                |
|  [CANCEL]       [CREATE]     |
+--------------------------------+
```

### Edit Account Modal
Same as Add Account modal but with pre-populated fields.

---

## Components

### Cards
- **Background:** `#0F0F10`
- **Border:** `1px solid #27272A`
- **Padding:** 12px

### Buttons

**Primary (`.btn-primary`):**
- Background: `#FACC15`
- Text: `#18181B` (dark)
- Font: JetBrains Mono, 12px, Bold, Uppercase
- Padding: 10px 18px
- Hover: Darken 10%

**Secondary (`.btn-secondary`):**
- Background: Transparent
- Border: `1px solid #27272A`
- Text: `#FAFAFA`
- Hover: Background `#27272A`

**Danger (`.btn-danger`):**
- Background: `#EF4444`
- Text: `#FAFAFA`

### Input Fields
- Background: `#141415`
- Border: `1px solid #27272A`
- Text: `#FAFAFA`
- Font: JetBrains Mono, 13px
- Padding: 8px 12px
- Focus: Border color `#FACC15`

### Badges

**Success Badge:**
- Background: `rgba(34, 197, 94, 0.125)` (20% opacity green)
- Text: `#22C55E`
- Padding: 3px 6px

**Warning Badge:**
- Background: `rgba(250, 204, 21, 0.125)`
- Text: `#FACC15`

**Error Badge:**
- Background: `rgba(239, 68, 68, 0.125)`
- Text: `#EF4444`

### Tables
- Header: Uppercase, 11px, text-secondary
- Cells: 13px, text-primary
- Row alternating: `#0F0F10` / `#141415`
- Row border: `1px solid #27272A`

---

## API Endpoints

### Metrics

```
GET /api/metrics?account_id=<uuid>&start_date=<date>&end_date=<date>
```

**Response:**
```json
{
  "total_trades": 56,
  "confirmed_trades": 26,
  "closed_trades": 30,
  "winning_trades": 18,
  "losing_trades": 11,
  "win_rate": 0.6333,
  "total_pnl": 32332.98,
  "profit_factor": 3.09,
  "avg_pnl_per_trade": 1077.77,
  "avg_win": 2516.68,
  "avg_loss": -1407.64,
  "best_trade": 7897.53,
  "worst_trade": -5841.85,
  "recent_pnl": [100, -50, 200, 500, -100],
  "by_symbol": [
    {"symbol": "BTCUSDT", "count": 5, "pnl": 4381.01}
  ],
  "by_direction": [
    {"direction": "long", "count": 18, "pnl": 47606.50}
  ]
}
```

### Accounts

```
GET /api/accounts
```

**Response:**
```json
{
  "accounts": [
    {
      "id": "uuid",
      "name": "Default",
      "opening_balance": 10000.00,
      "is_active": true,
      "created_at": "2026-03-28T12:33:26.350646+00:00",
      "trade_count": 45,
      "total_pnl": 1234.56,
      "win_rate": 0.65
    }
  ]
}
```

```
POST /api/accounts
Body: {"name": "Personal", "opening_balance": 10000}

PUT /api/accounts/{id}
Body: {"name": "Updated Name", "opening_balance": 15000}

DELETE /api/accounts/{id}
```

### Trades

```
GET /api/trades?status=closed&account_id=<uuid>&symbol=BTCUSDT&page=1&per_page=20
```

**Response:**
```json
{
  "trades": [
    {
      "id": "uuid",
      "account_id": "uuid",
      "symbol": "BTCUSDT",
      "direction": "long",
      "entry_price": 67000.00,
      "exit_price": 68000.00,
      "take_profit": 68000.00,
      "stop_loss": 66000.00,
      "position_size": 0.1,
      "status": "closed",
      "pnl": 100.00,
      "trade_date": "2026-03-28"
    }
  ],
  "total": 56,
  "page": 1,
  "pages": 3
}
```

```
POST /api/trades
Body: {
  "account_id": "uuid",
  "symbol": "BTCUSDT",
  "direction": "long",
  "entry_price": 67000.00,
  "exit_price": 68000.00,
  "take_profit": 68000.00,
  "stop_loss": 66000.00,
  "position_size": 0.1,
  "trade_date": "2026-03-28"
}
```

---

## Tailwind Configuration

```javascript
tailwind.config = {
  theme: {
    extend: {
      colors: {
        'bg-primary': '#18181B',
        'bg-secondary': '#0F0F10',
        'bg-surface': '#141415',
        'text-primary': '#FAFAFA',
        'text-light': '#A1A1AA',
        'text-secondary': '#71717A',
        'text-tertiary': '#52525B',
        'accent-primary': '#FACC15',
        'success': '#22C55E',
        'error': '#EF4444',
        'warning': '#FACC15',
        'border-default': '#27272A',
      },
      fontFamily: {
        'mono': ['JetBrains Mono', 'monospace'],
        'display': ['Space Grotesk', 'sans-serif'],
      }
    }
  }
}
```

---

## External Dependencies

### Fonts (Google Fonts)
- JetBrains Mono: 400, 500, 600, 700
- Space Grotesk: 300, 400, 500, 600, 700

### CSS Framework
- Tailwind CSS (CDN): `https://cdn.tailwindcss.com`

### JavaScript Libraries
- Chart.js: `https://cdn.jsdelivr.net/npm/chart.js`

---

## File Structure

```
TradeLogger/
├── src/
│   ├── app.py                 # Flask application factory
│   ├── config.py              # Configuration (dev/test/prod)
│   ├── models.py              # SQLAlchemy models
│   ├── routes/
│   │   ├── accounts.py        # Account API endpoints
│   │   ├── trades.py          # Trade API endpoints
│   │   └── metrics.py         # Metrics API endpoint
│   └── services/
│       └── trade_service.py   # Business logic
├── web/
│   ├── templates/
│   │   ├── base.html          # Base template with navigation
│   │   ├── dashboard.html    # Dashboard page
│   │   ├── trades.html        # Trades list page
│   │   ├── accounts.html      # Accounts management page
│   │   └── favorites.html     # Favorite symbols page
│   └── routes/
│       └── __init__.py       # Web page routes
├── docs/
│   └── UI_SPEC.md            # This specification
└── tests/
    ├── conftest.py           # Test fixtures
    ├── test_trades.py        # Trade API tests
    └── test_metrics.py        # Metrics API tests
```

---

*Last Updated: March 2026*
