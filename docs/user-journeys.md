# User Journeys - TradeLogger

### Part 1: Desktop Widget (9 Flows)

---

#### 1. Login Flow
| Step | User Action | System Response |
|------|-------------|-----------------|
| 1 | Launch desktop widget | Display Login View |
| 2 | Click "Open Browser Login" | Browser opens to `/login?source=desktop` |
| 3 | Authenticate in browser (Google OAuth) | Session created, tokens generated |
| 4 | Auth callback via protocol | Widget receives tokens |
| 5 | Token validation | Auth status check via `/api/auth/status` |
| 6 | Success | Show Trade View, load accounts/favorites |

**API Used:**
- `POST /api/auth/login` - Web login
- `GET /api/auth/status` - Verify session
- `POST /api/auth/refresh` - Token refresh

**Test Cases:**
| Type | Group | Description | Test File |
|------|-------|-------------|-----------|
| E2E | Login | Complete login flow from widget to authenticated state | `tests/e2e/test_widget.py` |
| E2E | Login | Expired token triggers refresh flow | `tests/e2e/test_widget.py` |
| Unit | Auth | Token validation logic | `tests/test_auth.py` |
| Unit | Auth | Refresh token generation | `tests/test_auth.py` |

---

#### 2. Logout Flow
| Step | User Action | System Response |
|------|-------------|-----------------|
| 1 | Click Logout button in user bar | Clear stored tokens from main process |
| 2 | - | In-memory tokens cleared, UI switches to Login View |

**Test Cases:**
| Type | Group | Description | Test File |
|------|-------|-------------|-----------|
| E2E | Logout | Click logout clears tokens and shows login view | *Needs creation* |

---

#### 3. Settings Menu Flow
| Step | User Action | System Response |
|------|-------------|-----------------|
| 1 | Click ☰ Menu button in header | Settings panel slides in from right |
| 2 | Toggle Always on Top | `setAlwaysOnTop()` Electron API, window stays on top |
| 3 | Toggle Dark Mode | Theme switches, saved to localStorage `theme` |
| 4 | Click × button or click outside panel | Settings panel closes |

**Test Cases:**
| Type | Group | Description | Test File |
|------|-------|-------------|-----------|
| Unit | Settings | Theme toggle updates body dataset | *Needs creation* |
| Unit | Settings | Always on top persists to localStorage | *Needs creation* |

---

#### 4. Add Trade (Basic)
| Step | User Action | System Response |
|------|-------------|-----------------|
| 1 | Fill form: Date, Account, Symbol | Auto-remembers last selection |
| 2 | Select Direction (Long/Short) | - |
| 3 | Select Outcome (Win/Loss/Break Even) | - |
| 4 | Enter Entry Price, Position Size | - |
| 5 | Optionally enter Stop Loss, Take Profit | Validation: Long TP > entry, Short TP < entry |
| 6 | Optionally enter Notes | - |
| 7 | Click SAVE TRADE | POST to `/api/trades` |
| 8 | Success | Show P&L status message, clear form, refresh recent trades |
| 9 | Error | Show validation error message |

**API Used:**
- `POST /api/trades` - Create trade
- `GET /api/trades?per_page=2` - List recent trades
- `GET /api/accounts` - Load accounts dropdown
- `GET /api/favorites` - Load symbols dropdown

**Test Cases:**
| Type | Group | Description | Test File |
|------|-------|-------------|-----------|
| E2E | Trade | Create trade with all basic fields | `tests/e2e/test_trades.py::test_trades_add_new_button_exists` |
| E2E | Trade | Validation errors show for invalid prices | `tests/e2e/test_price_validation.py` |
| Unit | Trade | Long TP must be > entry price | `tests/test_price_validation.py::test_long_tp_less_than_entry_fails` |
| Unit | Trade | Short TP must be < entry price | `tests/test_price_validation.py` |
| Unit | Trade | TradeService.create() calculation | `tests/test_trades.py::test_create_trade_success` |

---

#### 5. Add Trade with Partial Exits
| Step | User Action | System Response |
|------|-------------|-----------------|
| 1 | Complete basic trade form | - |
| 2 | Click + ADD button in Partial Exits section | New row renders with qty, exit_price, fees inputs |
| 3 | Enter qty (quantity exiting) | - |
| 4 | Enter exit_price | - |
| 5 | Enter fees (optional) | - |
| 6 | Repeat steps 2-5 for multiple partial exits | - |
| 7 | Click × on a partial exit row | Removes that exit from array |
| 8 | Click SAVE TRADE | Trade posted with `exit_transactions` array |
| 9 | Success | Trade saved with partial exit data, P&L calculated |

**Test Cases:**
| Type | Group | Description | Test File |
|------|-------|-------------|-----------|
| E2E | Trade | Create trade with multiple partial exits | *Needs creation* |
| Unit | Trade | P&L calculation with partial exits | *Needs verification in service tests* |

---

#### 6. Add Trade with Screenshot
| Step | User Action | System Response |
|------|-------------|-----------------|
| 1 | Complete basic trade form | - |
| 2 | Click Choose File in Screenshot field | File picker opens |
| 3 | Select image file (accepts image/*) | Filename displays |
| 4 | Click SAVE TRADE | FormData upload with screenshot file |
| 5 | Success | Trade and screenshot saved to `SCREENSHOT_DIR` |

**API Used:**
- `POST /api/trades` (multipart/form-data) - Create trade with file
- `GET /api/screenshots/<filename>` - Serve screenshot

**Test Cases:**
| Type | Group | Description | Test File |
|------|-------|-------------|-----------|
| E2E | Trade | Create trade with screenshot attachment | `tests/e2e/test_trades.py` |
| Unit | Trade | Screenshot file upload handling | `tests/test_fix_screenshot.py` |

---

#### 7. View All Trades
| Step | User Action | System Response |
|------|-------------|-----------------|
| 1 | Click VIEW ALL TRADES → button | Browser opens to web dashboard |
| 2 | - | Navigate to `http://localhost:5000/trades` |

**Test Cases:**
| Type | Group | Description | Test File |
|------|-------|-------------|-----------|
| E2E | Widget | Click view all opens external URL | *Needs creation* |

---

#### 8. Window Controls
| Step | User Action | System Response |
|------|-------------|-----------------|
| 1 | Click Float button (▼) | Widget collapses to header-only, window resize to 48px |
| 2 | Click Float button (▲) | Widget expands to full form, window resize to 700px |
| 3 | Click Minimize (—) | Window minimizes to taskbar |
| 4 | Click Close (×) | Confirmation dialog appears |
| 5 | Confirm close | Widget window closes |

**Test Cases:**
| Type | Group | Description | Test File |
|------|-------|-------------|-----------|
| E2E | Electron | Float toggle resizes window correctly | `tests/e2e/agent-browser/test_widget_electron.py` |

---

#### 9. Auto-Save Preferences
| Step | User Action | System Response |
|------|-------------|-----------------|
| 1 | Select Account from dropdown | Save to localStorage `lastAccountId` |
| 2 | Select Symbol from dropdown | Save to localStorage `lastSymbol` |
| 3 | Toggle Dark Mode | Save to localStorage `theme` |
| 4 | Toggle Always on Top | Save to localStorage `alwaysOnTop` |
| 5 | Return to widget later | Auto-select last used account and symbol |

**Test Cases:**
| Type | Group | Description | Test File |
|------|-------|-------------|-----------|
| Unit | Settings | Auto-select last used account on load | *Needs creation* |

---

### Part 2: Web Dashboard (7 Flows)

---

#### 1. Web Login/Logout
| Step | User Action | System Response |
|------|-------------|-----------------|
| 1 | Navigate to `/login` | Display login page with "Sign in with Google" |
| 2 | Click "Sign in with Google" | Redirect to Google OAuth |
| 3 | Authorize application | Redirect back with auth code |
| 4 | Session created | Redirect to `/dashboard` |
| 5 | Success | User sees dashboard with their data |

| Step | User Action | System Response |
|------|-------------|-----------------|
| 1 | Click user menu → Logout | Clear session cookies |
| 2 | - | Redirect to `/login` |

**API Used:**
- `POST /api/auth/login` - OAuth login
- `GET /api/auth/status` - Verify session

**Test Cases:**
| Type | Group | Description | Test File |
|------|-------|-------------|-----------|
| E2E | Auth | Google OAuth login flow | `tests/e2e/conftest.py` fixtures |
| Unit | Auth | Token generation | `tests/test_auth.py` |

---

#### 2. Dashboard View
| Step | User Action | System Response |
|------|-------------|-----------------|
| 1 | Navigate to `/dashboard` | Load metrics via HTMX |
| 2 | Page displays | 8 metric cards render: |
| | | - Total Trades |
| | | - Win Rate |
| | | - Total P&L |
| | | - Profit Factor |
| | | - Avg Win |
| | | - Avg Loss |
| | | - Best Trade |
| | | - Worst Trade |
| 3 | Optionally filter by date range | From/To date inputs filter metrics |
| 4 | Metrics update | GET `/api/metrics?start=...&end=...` |

**API Used:**
- `GET /api/metrics` - Fetch aggregated metrics
- `GET /api/metrics?start=&end=` - Filtered metrics

**Test Cases:**
| Type | Group | Description | Test File |
|------|-------|-------------|-----------|
| E2E | Dashboard | Dashboard loads successfully | `tests/e2e/test_dashboard.py::test_dashboard_loads_successfully` |
| E2E | Dashboard | Displays all stats cards | `tests/e2e/test_dashboard.py::test_dashboard_displays_stats` |

---

#### 3. Trade List (with Filters)
| Step | User Action | System Response |
|------|-------------|-----------------|
| 1 | Navigate to `/trades` | Trade table loads via HTMX |
| 2 | View table | Columns: Symbol, Direction, Entry, Exit, Size, P&L, Date |
| 3 | Filter by Symbol | Select from dropdown, table updates |
| 4 | Filter by Direction | Select Long/Short, table updates |
| 5 | Filter by Date Range | Select start/end dates, table updates |
| 6 | View stats bar | Filtered count, P&L, win rate, avg P&L |
| 7 | Pagination | Click page numbers to navigate |

**API Used:**
- `GET /api/trades` - List trades with filters
- Query params: `symbol`, `direction`, `start`, `end`, `page`, `per_page`

**Test Cases:**
| Type | Group | Description | Test File |
|------|-------|-------------|-----------|
| E2E | Trades | Trades page loads | `tests/e2e/test_trades.py::test_trades_page_loads` |
| E2E | Trades | Table displays data | `tests/e2e/test_trades.py::test_trades_table_displays` |
| E2E | Trades | Filter by symbol works | `tests/e2e/test_trades.py::test_trades_filter_by_symbol` |

---

#### 4. Trade Detail/Edit
| Step | User Action | System Response |
|------|-------------|-----------------|
| 1 | Click on a trade row | Trade detail modal opens |
| 2 | View trade details | All fields displayed |
| 3 | Click Edit button | Fields become editable |
| 4 | Modify fields | Entry price, stop loss, take profit, notes |
| 5 | Click Save | PUT `/api/trades/<id>` |
| 6 | Success | Modal closes, table updates |
| 7 | Click Delete | Confirmation dialog |
| 8 | Confirm delete | DELETE `/api/trades/<id>`, row removed |

**API Used:**
- `GET /api/trades/<id>` - Get single trade
- `PUT /api/trades/<id>` - Update trade
- `DELETE /api/trades/<id>` - Delete trade

**Test Cases:**
| Type | Group | Description | Test File |
|------|-------|-------------|-----------|
| E2E | Trades | Edit button exists | `tests/e2e/test_trades.py::test_trades_edit_exists` |
| E2E | Trades | Delete button exists | `tests/e2e/test_trades.py::test_trades_delete_exists` |
| Unit | Trade | Update trade service | `tests/test_edit_trade.py` |

---

#### 5. Favorites Management
| Step | User Action | System Response |
|------|-------------|-----------------|
| 1 | Navigate to `/favorites` | Favorites table loads |
| 2 | Click + ADD button | Add favorite form/modal opens |
| 3 | Enter Symbol | e.g., BTCUSDT |
| 4 | Enter Point Value | e.g., 0.01 |
| 5 | Enter Fees | e.g., 0.1 |
| 6 | Click Save | POST `/api/favorites` |
| 7 | Success | Row added to table |
| 8 | Click Edit on a row | Fields become editable |
| 9 | Modify and Save | PUT `/api/favorites/<id>` |

**API Used:**
- `GET /api/favorites` - List favorites
- `POST /api/favorites` - Create favorite
- `PUT /api/favorites/<id>` - Update favorite
- `DELETE /api/favorites/<id>` - Delete favorite

**Test Cases:**
| Type | Group | Description | Test File |
|------|-------|-------------|-----------|
| E2E | Favorites | Favorites page loads | `tests/e2e/test_favorites.py::test_favorites_page_loads` |
| E2E | Favorites | Table displays data | `tests/e2e/test_favorites.py::test_favorites_table_displays` |
| E2E | Favorites | Add button exists | `tests/e2e/test_favorites.py::test_favorites_add_button_exists` |
| E2E | Favorites | Edit exists | `tests/e2e/test_favorites.py::test_favorites_edit_exists` |

---

#### 6. Account Management
| Step | User Action | System Response |
|------|-------------|-----------------|
| 1 | Navigate to `/accounts` | Accounts table loads |
| 2 | Click + ADD button | Add account form/modal opens |
| 3 | Enter Account Name | e.g., Main Trading |
| 4 | Click Save | POST `/api/accounts` |
| 5 | Success | Row added to table |
| 6 | Click Edit on a row | Modify name |
| 7 | Click Delete | Remove account |

**API Used:**
- `GET /api/accounts` - List accounts
- `POST /api/accounts` - Create account
- `PUT /api/accounts/<id>` - Update account
- `DELETE /api/accounts/<id>` - Delete account

**Test Cases:**
| Type | Group | Description | Test File |
|------|-------|-------------|-----------|
| Unit | Accounts | CRUD operations | `tests/test_accounts.py` |

---

#### 7. HTMX Navigation
| Step | User Action | System Response |
|------|-------------|-----------------|
| 1 | Click sidebar item (e.g., Dashboard) | HTMX GET request |
| 2 | - | Only main content area updates |
| 3 | - | Sidebar persists |
| 4 | - | URL updates to `/dashboard` |
| 5 | - | Active state highlights sidebar item |
| 6 | Click another sidebar item | Content swaps without full reload |

**Test Cases:**
| Type | Group | Description | Test File |
|------|-------|-------------|-----------|
| E2E | HTMX | Sidebar navigation no duplication | `tests/e2e/test_htmx_navigation.py::test_htmx_sidebar_navigation_no_duplication` |
| E2E | HTMX | Content visible after nav | `tests/e2e/test_htmx_navigation.py::test_htmx_navigation_content_visible` |
| E2E | HTMX | URL updates on nav | `tests/e2e/test_htmx_navigation.py::test_htmx_navigation_url_updates` |
| E2E | HTMX | Active state updates | `tests/e2e/test_htmx_navigation.py::test_htmx_active_state_updates` |

---

## Summary - Test Coverage

| Section | Total Flows | E2E Tests | Unit Tests | Status |
|---------|-------------|-----------|------------|--------|
| **Desktop Widget** | **9** | | | |
| Login | | ✅ 2 | ✅ 2 | Complete |
| Logout | | ⚠️ 1 needs creation | - | Needs work |
| Settings | | - | ⚠️ 2 needs creation | Needs work |
| Add Trade | | ✅ 2 | ✅ 3 | Complete |
| Partial Exits | | ⚠️ 1 needs creation | ⚠️ 1 verify | Needs work |
| Screenshot | | ⚠️ 1 verify | ✅ 1 | Needs verification |
| View All | | ⚠️ 1 needs creation | - | Needs work |
| Window Controls | | ✅ 1 | - | Complete |
| Auto-Save | | - | ⚠️ 1 needs creation | Needs work |
| **Web Dashboard** | **7** | | | |
| Login/Logout | | ⚠️ OAuth flow | ✅ 1 | Partial |
| Dashboard | | ✅ 2 | - | Complete |
| Trade List | | ✅ 3 | - | Complete |
| Trade Edit | | ⚠️ verify | ✅ 1 | Partial |
| Favorites | | ✅ 4 | ✅ 4 | Complete |
| Accounts | | - | ✅ 1 | Partial |
| HTMX Nav | | ✅ 5 | - | Complete |
| **TOTAL** | **16** | | | |

**Legend:**
- ✅ = Exists and verified
- ⚠️ = Needs creation or verification

**Totals:**
- Desktop Widget: 9 user flows
- Web Dashboard: 7 user flows
- **Total: 16 user flows**
