# Feature: Trading Journal Enhancements
ID: FEA-007
Status: planning
Branch: feature/journal-enhancements
Created: 2026-05-17
Complexity: medium

## Summary
Upgrade TradeLogger's journal with CSV import from broker platforms, live broker sync (cTrader, MT4, Tradovate, etc.), and advanced analytics — turning it from a manual trade entry tool into a comprehensive trading journal matching FXReplay's capabilities.

## Context
TradeLogger already has manual trade entry, tags, partial exits, and basic metrics. The gap is automated data entry (CSV import / broker sync) and deep analytics (time-based analysis, performance calendar, Monte Carlo, etc.).

---

## Requirements

### R1: Universal CSV Import
- [ ] Import trades from CSV files exported by any broker platform
- [ ] Smart column mapping (auto-detect common column names)
- [ ] Support MT4/MT5, Tradovate, NinjaTrader, cTrader, TradeLocker formats
- [ ] Preview before import (show mapped columns, first 5 rows)
- [ ] Handle duplicate detection (skip existing trades by trade ID or date+symbol)
- [ ] Validation: required fields, data types, error reporting
- [ ] Import result summary (X created, Y skipped, Z errors)

### R2: Live Broker Sync
- [ ] API-based trade synchronization
- [ ] Support cTrader API (REST/WebSocket)
- [ ] Support MT4/MT5 via CSV or MT API
- [ ] Support Tradovate REST API
- [ ] Configurable sync interval (every 15min, 1h, daily)
- [ ] Broker connection management UI (add/edit/remove connections)
- [ ] Secure credential storage (encrypted at rest)
- [ ] Sync status dashboard (last sync, errors, trade count)

### R3: Advanced Analytics
- [ ] **Time-based analytics**: Win rate and P&L by hour, day of week, session (London/NY/Asia)
- [ ] **Performance calendar**: Monthly calendar view with green/red P&L cells
- [ ] **Monte Carlo simulation**: Run 1000 simulations of random trade sequences
- [ ] **Drawdown analysis**: Max drawdown, average drawdown, recovery time
- [ ] **Tag analysis**: Win rate and P&L by tag combinations (which setups work best)
- [ ] **Equity curve**: Cumulative P&L chart with drawdown overlay
- [ ] **Sharpe ratio & risk metrics**: Risk-adjusted return calculations
- [ ] **P&L distribution**: Histogram of trade outcomes

### R4: Journal UI Improvements
- [ ] Advanced trade filter with AND/OR logic and include/exclude
- [ ] Filter by tag combination, date range, account, direction, outcome
- [ ] Saved filter presets
- [ ] Bulk tag/edit trades
- [ ] Quick stats bar (today's P&L, open positions, win rate)

---

## Architecture / Design

### New Models

```python
class BrokerConnection(db.Model):
    """Broker API connection configuration."""
    __tablename__ = "broker_connections"
    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    broker = db.Column(db.String(50), nullable=False)  # ctrader, mt4, tradovate, etc
    label = db.Column(db.String(100))  # user-friendly name
    api_key = db.Column(db.Text, nullable=True)  # encrypted
    api_secret = db.Column(db.Text, nullable=True)  # encrypted
    account_id = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    last_sync_at = db.Column(db.DateTime(timezone=True))
    sync_interval = db.Column(db.Integer, default=60)  # minutes
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
```

### New Service: ImportService
- CSV parsing engine with format detection
- Column mapping (smart defaults + user overrides)
- Duplicate detection
- Batch trade creation
- Error reporting

### New Service: BrokerSyncService
- Abstract sync interface with broker-specific implementations
- Scheduled sync via APScheduler or Celery
- API rate limiting and retry logic
- Webhook support for real-time sync

### New Service: AnalyticsService
- Aggregation queries for time-based analytics
- Monte Carlo simulation engine
- Calendar-based performance calculation
- All queries operate on the existing `trades` table

### New API Routes: /api/import/*
- POST /api/import/csv — upload CSV file
- POST /api/import/preview — preview CSV mapping
- GET /api/import/templates — download CSV templates by broker
- GET /api/import/history — import history

### New API Routes: /api/brokers/*
- GET /api/brokers — list broker connections
- POST /api/brokers — add broker connection
- PUT /api/brokers/{id} — update connection
- DELETE /api/brokers/{id} — remove connection
- POST /api/brokers/{id}/sync — trigger manual sync
- GET /api/brokers/{id}/sync-status — last sync status

### New API Routes: /api/analytics/*
- GET /api/analytics/time-based — win rate by hour/day/session
- GET /api/analytics/calendar — performance calendar data
- GET /api/analytics/monte-carlo — run simulation
- GET /api/analytics/drawdown — drawdown analysis
- GET /api/analytics/tags — tag combination analysis
- GET /api/analytics/equity — equity curve data
- GET /api/analytics/risk-metrics — Sharpe ratio, etc.

### Frontend Additions
- **Import page** (`/import`): Drag-and-drop CSV upload, column mapping UI, preview table
- **Brokers page** (`/brokers`): Connection management, sync config, status
- **Analytics page** (`/analytics`): Time-based charts, calendar, Monte Carlo, distribution
- **Enhanced trades page**: Advanced filter bar, quick stats, bulk actions

---

## Implementation Plan

### Phase 1: CSV Import
- Agent: @devedu
- Status: ⬜ pending
- Steps:
  - [ ] Create `ImportService` with CSV parsing engine
  - [ ] Support MT4/MT5, Tradovate, NinjaTrader, cTrader, TradeLocker formats
  - [ ] Auto-detect column mapping with validation
  - [ ] Duplicate detection (by trade date + symbol + direction + entry price)
  - [ ] Create import API endpoints
  - [ ] Build import frontend (drag-and-drop, preview, results)
  - [ ] Add `/import` sidebar link
  - [ ] Write unit tests for import service
  - [ ] Write E2E tests for import flow

### Phase 2: Broker Sync
- Agent: @devedu
- Status: ⬜ pending
- Steps:
  - [ ] Create `BrokerConnection` model and migration
  - [ ] Create `BrokerSyncService` with abstract interface
  - [ ] Implement cTrader sync adapter
  - [ ] Implement Tradovate sync adapter
  - [ ] Implement MT4/MT5 CSV-based sync adapter
  - [ ] Encrypted credential storage
  - [ ] Create broker API endpoints
  - [ ] Build broker management frontend
  - [ ] Add scheduled sync (APScheduler)
  - [ ] Write unit tests for sync service
  - [ ] Write broker integration tests

### Phase 3: Advanced Analytics
- Agent: @devedu
- Status: ⬜ pending
- Steps:
  - [ ] Create `AnalyticsService`
  - [ ] Implement time-based analytics (hour, day, session)
  - [ ] Implement performance calendar
  - [ ] Implement Monte Carlo simulation
  - [ ] Implement drawdown analysis
  - [ ] Implement tag combination analysis
  - [ ] Implement equity curve data
  - [ ] Implement risk metrics (Sharpe, Sortino, profit factor)
  - [ ] Create analytics API endpoints
  - [ ] Build analytics frontend (charts, calendar, distributions)
  - [ ] Add `/analytics` sidebar link
  - [ ] Write unit tests for analytics service

### Phase 4: Journal UI Overhaul
- Agent: @devedu
- Status: ⬜ pending
- Steps:
  - [ ] Build advanced filter bar (AND/OR, include/exclude)
  - [ ] Add quick stats bar to trades page
  - [ ] Add bulk tag/edit functionality
  - [ ] Add saved filter presets (localStorage)
  - [ ] Performance optimization for large trade lists
  - [ ] Update trades.html with enhanced UI

---

## Files to Create/Modify
| File | Action | Purpose |
|------|--------|---------|
| `src/models.py` | modify | Add BrokerConnection model |
| `src/services/import_service.py` | create | CSV import engine |
| `src/services/broker_sync_service.py` | create | Broker sync engine |
| `src/services/analytics_service.py` | create | Advanced analytics |
| `src/routes/import_routes.py` | create | Import API blueprint |
| `src/routes/broker_routes.py` | create | Broker API blueprint |
| `src/routes/analytics_routes.py` | create | Analytics API blueprint |
| `src/app.py` | modify | Register new blueprints |
| `src/config.py` | modify | Add broker/import config |
| `web/templates/import.html` | create | CSV import page |
| `web/templates/brokers.html` | create | Broker management page |
| `web/templates/analytics.html` | create | Analytics dashboard page |
| `web/templates/trades.html` | modify | Enhanced filter bar, quick stats |
| `web/routes/__init__.py` | modify | Add new web routes |
| `web/templates/base.html` | modify | Add Import & Analytics sidebar links |
| `migrations/versions/*.py` | create | Schema migration |
| `tests/test_import.py` | create | Unit tests |
| `tests/test_broker_sync.py` | create | Unit tests |
| `tests/test_analytics.py` | create | Unit tests |
| `tests/e2e/test_import.py` | create | E2E tests |
| `tests/e2e/test_analytics.py` | create | E2E tests |
| `pyproject.toml` | modify | Add dependencies (csv, apscheduler, etc.) |

---

## Acceptance Criteria
- [ ] User can upload a CSV from MT4 and see trades imported correctly
- [ ] CSV preview shows correctly mapped columns before import
- [ ] Duplicate trades are skipped (not duplicated)
- [ ] User can connect a cTrader account and sync trades
- [ ] Sync runs automatically at configured intervals
- [ ] Time-based analytics show win rate by hour and day of week correctly
- [ ] Performance calendar shows green/red days
- [ ] Monte Carlo simulation runs and displays distribution chart
- [ ] Tag analysis shows which tag combinations have highest win rate
- [ ] Equity curve chart displays cumulative P&L with drawdown shading
- [ ] Advanced filters work with AND/OR logic

## Risks & Mitigations
| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Broker API changes break sync | med | Abstract sync interface; test with sandbox APIs first |
| CSV format variations | high | Parser with multiple format profiles + user override |
| Monte Carlo is CPU-intensive | med | Run server-side with timeout; cache results |
| API rate limits on broker sync | med | Configurable sync intervals; retry with backoff |

## Notes
- Start with CSV import (highest value, lowest complexity)
- Then add cTrader API (has good REST API docs)
- Then Tradovate and MT4
- Analytics queries should use SQL aggregation (not Python iteration) for performance
- Monte Carlo: random shuffle of actual trades, run 1000 iterations
- Session analysis: morning/afternoon/evening + London/NY/Asia session detection

## Approval
- [ ] User approved
- Approved by:
- Approved at:
- Comments:
