# Feature: Backtesting System with TradingView Charts
ID: FEA-006
Status: planning
Branch: feature/backtesting-system
Created: 2026-05-17
Complexity: large

## Summary
A full-featured manual backtesting system with TradingView chart integration, historical market replay, on-chart trade entry/management, and auto risk controls — feeding results directly into the existing Trade database.

## Context
TradeLogger currently only supports live/csv-imported trade journaling. Traders need a way to practice strategies against historical data before risking real capital. FXReplay's backtesting (Replay Mode) is the industry benchmark — this feature brings that capability to TradeLogger.

---

## Requirements

### R1: Historical Price Data
- [ ] Price data model: OHLCV candles + tick data storage
- [ ] Built-in data downloader/source for Forex, Futures, Indices, Stocks
- [ ] Admin endpoint to ingest/refresh historical data
- [ ] Data back to at least 2012 for major assets

### R2: TradingView Chart Integration
- [ ] Embed TradingView lightweight charts or TradingView widget
- [ ] Chart shows historical candles for selected symbol & timeframe
- [ ] Ability to step through candles forward/backward (replay mode)
- [ ] Drawing tools for trendlines, support/resistance, etc.
- [ ] Multiple chart layouts (1, 2, 4 charts side-by-side)

### R3: Market Replay Engine
- [ ] Play/pause/stop controls for replaying historical data
- [ ] Speed control (1x, 2x, 5x, 10x, custom)
- [ ] Jump to specific date/time
- [ ] Show candle-by-candle progression (not just final state)
- [ ] Seconds-level precision on Pro plan

### R4: On-Chart Trade Entry
- [ ] Click on chart to enter a trade (set entry, SL, TP)
- [ ] Visual trade markers on chart (entry line, SL, TP levels)
- [ ] Position sizing with auto-calculated lot size based on risk %
- [ ] Trade direction (long/short) selection
- [ ] Auto breakeven (move SL to entry when price moves X pips in favor)

### R5: Backtesting Session Management
- [ ] Session creation with symbol, timeframe, starting balance
- [ ] Real-time P&L tracking during session
- [ ] Session summary on end (trades taken, win rate, P&L, drawdown)
- [ ] Ability to save/replay a session

### R6: Integration with Existing Trade DB
- [ ] Backtesting trades stored in same `trades` table as live trades
- [ ] `session_id` column to differentiate backtest vs live
- [ ] Results auto-populate the Journal

---

## Architecture / Design

### New Models

```python
class Asset(db.Model):
    """Asset/symbol with metadata."""
    __tablename__ = "assets"
    id = db.Column(db.String(36), primary_key=True)
    symbol = db.Column(db.String(50), nullable=False, unique=True)
    name = db.Column(db.String(200))
    asset_type = db.Column(db.String(50))  # forex, futures, stock, index, crypto
    point_value = db.Column(db.Numeric(18, 8), default=1)
    tick_size = db.Column(db.Numeric(18, 8))
    min_lot = db.Column(db.Numeric(18, 8))
    is_active = db.Column(db.Boolean, default=True)

class PriceCandle(db.Model):
    """OHLCV candle data."""
    __tablename__ = "price_candles"
    id = db.Column(db.String(36), primary_key=True)
    asset_id = db.Column(db.String(36), db.ForeignKey("assets.id"), nullable=False)
    symbol = db.Column(db.String(50), nullable=False)  # denormalized for speed
    timeframe = db.Column(db.String(10), nullable=False)  # 1m, 5m, 1h, 1d, etc
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False)
    open = db.Column(db.Numeric(18, 8), nullable=False)
    high = db.Column(db.Numeric(18, 8), nullable=False)
    low = db.Column(db.Numeric(18, 8), nullable=False)
    close = db.Column(db.Numeric(18, 8), nullable=False)
    volume = db.Column(db.Numeric(18, 2))
    __table_args__ = (
        db.Index("ix_candles_symbol_tf_ts", "symbol", "timeframe", "timestamp"),
    )

class BacktestSession(db.Model):
    """Backtesting replay session."""
    __tablename__ = "backtest_sessions"
    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    symbol = db.Column(db.String(50), nullable=False)
    timeframe = db.Column(db.String(10), nullable=False)
    starting_balance = db.Column(db.Numeric(18, 2), nullable=False)
    current_balance = db.Column(db.Numeric(18, 2))
    start_date = db.Column(db.DateTime(timezone=True))
    end_date = db.Column(db.DateTime(timezone=True))
    status = db.Column(db.String(20), default="active")  # active, paused, completed
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    completed_at = db.Column(db.DateTime(timezone=True))
```

### Trade Model Modifications
- Add `session_id` (nullable FK to backtest_sessions)
- Add `is_backtest` boolean column
- These are minimal changes — the existing Trade model handles all trade data

### New Service: ReplayService
- Manages replay state (current candle index, speed, etc.)
- In-memory session state (not persisted — performance critical)
- Candle progression logic
- Trade execution on candle close

### New Route: /api/backtest/*
- GET /api/backtest/assets — list available assets with data
- GET /api/backtest/candles?symbol=X&timeframe=Y&start=Z&end=W — get candle data
- POST /api/backtest/sessions — create session
- GET /api/backtest/sessions — list sessions
- GET /api/backtest/sessions/{id} — get session details
- PUT /api/backtest/sessions/{id}/controls — play/pause/stop/speed
- POST /api/backtest/sessions/{id}/trades — enter trade during replay
- GET /api/backtest/sessions/{id}/summary — end-of-session report

### New Web Page: /backtest
- New sidebar link: "Backtest" (with chart icon)
- Full TradingView chart component
- Replay controls bar (play/pause/speed slider/jump-to-date)
- Trade panel (current positions, P&L, account balance)
- Session config modal (select symbol, timeframe, starting balance)

### Frontend Architecture
- TradingView Charting Library (lightweight) or TradingView widget
- HTMX + vanilla JS for interactivity (matching existing pattern)
- WebSocket or polling for real-time P&L updates during replay

---

## Implementation Plan

### Phase 1: Data Layer — Asset Model & Price Data
- Agent: @devedu
- Status: ⬜ pending
- Steps:
  - [ ] Create `Asset` model and `PriceCandle` model
  - [ ] Create Alembic migration
  - [ ] Add `session_id` and `is_backtest` to `Trade` model
  - [ ] Create `BacktestSession` model
  - [ ] Build data ingestion endpoint (admin-only)
  - [ ] Write seed script for initial asset catalog
  - [ ] Write unit tests for models

### Phase 2: Backend — Replay Service & API
- Agent: @devedu
- Status: ⬜ pending
- Steps:
  - [ ] Implement `ReplayService` (candle iteration, P&L calc, auto-breakeven)
  - [ ] Create `backtest_bp` blueprint with all endpoints
  - [ ] Implement session CRUD
  - [ ] Implement candle data serving (paginated, efficient)
  - [ ] Implement trade entry during replay (reuses existing TradeService)
  - [ ] Implement session summary/analytics
  - [ ] Write unit tests for service and routes
  - [ ] Write API integration tests

### Phase 3: Frontend — TradingView Chart Integration
- Agent: @devedu
- Status: ⬜ pending
- Steps:
  - [ ] Add TradingView charting library (lightweight-charts or custom widget)
  - [ ] Build `backtest.html` template with full layout
  - [ ] Implement chart rendering from candle data
  - [ ] Add sidebar link for "Backtest"
  - [ ] Implement replay controls (play/pause/speed)
  - [ ] Implement chart-based trade entry (click to place entry, SL, TP)
  - [ ] Add visual trade markers on chart
  - [ ] Show real-time P&L & balance during session
  - [ ] Add session config modal
  - [ ] Add session history view

### Phase 4: Testing & Polish
- Agent: @qa-tester
- Status: ⬜ pending
- Steps:
  - [ ] Write E2E tests for backtest flow (Playwright)
  - [ ] Test replay engine with various timeframes
  - [ ] Test trade entry on chart
  - [ ] Test session import to journal
  - [ ] Performance test with large candle datasets
  - [ ] Dark mode support for charts
  - [ ] Edge cases: empty data, missing candles, fast-forward

---

## Files to Create/Modify
| File | Action | Purpose |
|------|--------|---------|
| `src/models.py` | modify | Add Asset, PriceCandle, BacktestSession models; modify Trade |
| `src/services/replay_service.py` | create | Market replay engine |
| `src/services/data_service.py` | create | Historical data management |
| `src/routes/backtest.py` | create | Backtest API blueprint |
| `src/app.py` | modify | Register backtest blueprint |
| `src/config.py` | modify | Add backtest config (data dir, etc.) |
| `web/templates/backtest.html` | create | Backtest page with chart & controls |
| `web/routes/__init__.py` | modify | Add /backtest web route |
| `web/templates/base.html` | modify | Add Backtest sidebar link |
| `web/static/js/backtest.js` | create | Frontend replay logic |
| `web/static/js/chart.js` | create | TradingView chart integration |
| `migrations/versions/*.py` | create | Schema migration |
| `tests/test_backtest.py` | create | Unit tests |
| `tests/e2e/test_backtest.py` | create | E2E tests |
| `pyproject.toml` | modify | Add dependencies (tradingview lib, etc.) |

---

## Acceptance Criteria
- [ ] User can create a backtest session with symbol, timeframe, starting balance
- [ ] TradingView chart renders historical candles correctly
- [ ] Replay controls work: play, pause, speed change, jump-to-date
- [ ] User can enter a trade by clicking on the chart (entry, SL, TP)
- [ ] Trade is created in the `trades` table with `is_backtest=true`
- [ ] P&L updates in real-time during replay
- [ ] Session summary shows correct metrics (win rate, total P&L, drawdown)
- [ ] Backtest trades appear in the Journal with a "Backtest" badge
- [ ] Auto-breakeven works when price moves X pips in favor
- [ ] At least 3 asset types (Forex, Futures, Index) have data available

## Risks & Mitigations
| Risk | Likelihood | Mitigation |
|------|------------|------------|
| TradingView charting library licensing | med | Use lightweight-charts (free open-source) or TradingView widget (free tier) |
| Large candle datasets slow down replay | med | Server-side pagination, WebSocket streaming, worker threads |
| Historical data source availability | high | Start with free sources (Yahoo Finance, Alpha Vantage) + user-upload CSV |
| Performance on seconds-level data | med | Downsample to higher timeframe when zoomed out; cache aggressively |

## Notes
- TradingView Lightweight Charts (https://tradingview.github.io/lightweight-charts/) is open-source and free
- For data: start with CSV import (user provides their own historical data), then add API sources
- The backtest replay happens **client-side** for speed — server serves candle data, browser does the stepping
- Trade validation happens server-side on trade entry
- Auto-breakeven: a configurable rule that moves SL to entry price after profit reaches X ticks/pips

## Approval
- [ ] User approved
- Approved by:
- Approved at:
- Comments:
