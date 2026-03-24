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

### 4. Web Dashboard (Flask Templates + Tailwind + Chart.js)
- Metrics dashboard (win rate, P&L, profit factor)
- Trade history with filtering
- Trade detail view with screenshot

## Data Flow

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

## Technology Decisions

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Backend | Flask + SQLAlchemy | Simple, proven, good ORM |
| Database | PostgreSQL | Robust, supports arrays (tags), good for analytics |
| Desktop | Electron + Bun | Cross-platform, Bun for speed |
| Web Frontend | Tailwind CSS + Chart.js | Fast styling, good charting |
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
