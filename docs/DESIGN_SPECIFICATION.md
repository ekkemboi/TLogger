# TradeLogger - Design Specification Document

**Version:** 1.0  
**Date:** 2026-04-02  
**Purpose:** Comprehensive reference for UI designers to understand app functionality, data models, user flows, and requirements

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Data Architecture](#2-data-architecture)
3. [Business Logic & Rules](#3-business-logic--rules)
4. [User Workflows](#4-user-workflows)
5. [Page Specifications](#5-page-specifications)
6. [API Contract](#6-api-contract)
7. [Component Inventory](#7-component-inventory)
8. [Sample Data Sets](#8-sample-data-sets)
9. [Functional Requirements](#9-functional-requirements)
10. [Accessibility & UX Requirements](#10-accessibility--ux-requirements)

---

## 1. Executive Summary

### 1.1 App Purpose
TradeLogger is a comprehensive trade journaling system designed for active traders to record, analyze, and improve their trading performance. It captures trade details, calculates profit/loss, tracks multiple accounts, and provides analytics to identify patterns and optimize strategies.

### 1.2 Target Users
- Day traders and swing traders
- Futures, forex, crypto, and stock traders
- Traders managing multiple accounts
- Users who want detailed performance analytics

### 1.3 Platform Overview

| Platform | Technology | Purpose |
|----------|------------|---------|
| **Web Application** | Flask + HTML/Tailwind | Full-featured dashboard, trade management, analytics |
| **Desktop Widget** | Electron | Quick trade entry, always-on-top convenience |
| **Backend API** | Flask REST API | Data persistence, business logic |
| **Database** | PostgreSQL | Trade records, user data, configurations |

### 1.4 Core Value Proposition
- **Capture** trades quickly from any device
- **Calculate** accurate P&L with point values and fees
- **Analyze** performance with metrics and charts
- **Improve** through data-driven insights

---

## 2. Data Architecture

### 2.1 Core Entities

#### 2.1.1 User
Authentication and user management entity.

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| id | UUID | Yes | Primary key | "550e8400-e29b-41d4-a716-446655440000" |
| email | String(255) | Yes | Unique email address | "trader@example.com" |
| name | String(100) | Yes | Display name | "John Trader" |
| profile_picture | String(500) | No | Avatar URL | "https://lh3.googleusercontent.com/..." |
| auth_provider | String(20) | Yes | "email" or "google" | "email" |
| google_id | String(100) | No | Google OAuth ID | "123456789012345678901" |
| password_hash | String(255) | Conditional | Bcrypt hash (null for Google users) | "$2b$12$..." |
| is_active | Boolean | Yes | Account status | true |
| created_at | DateTime | Auto | Account creation | "2024-01-15T10:30:00Z" |
| updated_at | DateTime | Auto | Last update | "2024-03-20T14:22:00Z" |

**Relationships:**
- One-to-Many with Trade
- One-to-Many with Account
- One-to-Many with FavoriteProduct

**Constraints:**
- Email must be unique
- Either password_hash OR google_id must be set
- auth_provider must be "email" or "google"

---

#### 2.1.2 Account
Trading account entity for users with multiple accounts.

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| id | UUID | Yes | Primary key | "550e8400-e29b-41d4-a716-446655440001" |
| user_id | UUID | Yes | FK to User | "550e8400-e29b-41d4-a716-446655440000" |
| name | String(100) | Yes | Account name | "Futures Account" |
| opening_balance | Numeric(18,2) | No | Starting balance | 25000.00 |
| is_active | Boolean | Yes | Soft delete flag | true |
| created_at | DateTime | Auto | Creation timestamp | "2024-01-15T10:30:00Z" |

**Computed Fields (API Response):**
| Field | Type | Calculation |
|-------|------|-------------|
| trade_count | Integer | COUNT(trades WHERE account_id = this.id) |
| total_pnl | Numeric | SUM(trades.pnl WHERE account_id = this.id) |
| profit_percent | Numeric | (total_pnl / opening_balance) * 100 |

**Sample Account Data:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Futures Account",
  "opening_balance": 25000.00,
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "trade_count": 156,
  "total_pnl": 3450.75,
  "profit_percent": 13.80
}
```

---

#### 2.1.3 FavoriteProduct
Frequently traded symbols with default settings.

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| id | UUID | Yes | Primary key | "550e8400-e29b-41d4-a716-446655440002" |
| user_id | UUID | Yes | FK to User | "550e8400-e29b-41d4-a716-446655440000" |
| symbol | String(50) | Yes | Trading symbol | "MNQ" |
| point_value | Numeric(18,8) | No | Dollar value per point | 2.00 |
| fees | Numeric(18,8) | No | Default fees per trade | 2.50 |
| is_active | Boolean | Yes | Soft delete flag | true |
| created_at | DateTime | Auto | Creation timestamp | "2024-01-15T10:30:00Z" |

**Sample Favorite Data:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "symbol": "ES",
  "point_value": 50.00,
  "fees": 5.00,
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Common Point Values Reference:**
| Symbol | Market | Point Value | Typical Fees |
|--------|--------|-------------|--------------|
| ES | S&P 500 Futures | $50.00 | $5.00 |
| NQ | Nasdaq Futures | $20.00 | $5.00 |
| MNQ | Micro Nasdaq | $2.00 | $2.50 |
| BTC | Bitcoin | $1.00 | Varies |
| ETH | Ethereum | $1.00 | Varies |

---

#### 2.1.4 Trade (Core Entity)
Trade journal entry - the primary data entity.

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| id | UUID | Yes | Primary key | "550e8400-e29b-41d4-a716-446655440003" |
| user_id | UUID | Yes | FK to User | "550e8400-e29b-41d4-a716-446655440000" |
| account_id | UUID | Yes | FK to Account | "550e8400-e29b-41d4-a716-446655440001" |
| symbol | String(50) | Yes | Trading symbol | "BTCUSDT" |
| direction | Enum | Yes | "long" or "short" | "long" |
| entry_price | Numeric(18,8) | Yes | Entry price | 67234.50 |
| exit_price | Numeric(18,8) | No | Exit price (closed trades) | 68500.00 |
| stop_loss | Numeric(18,8) | No | Stop loss level | 66800.00 |
| take_profit | Numeric(18,8) | No | Take profit target | 68500.00 |
| position_size | Numeric(18,8) | No | Contracts/shares | 0.1 |
| status | Enum | Auto | "pending", "confirmed", "closed" | "closed" |
| outcome | Enum | No | "WIN", "LOSS", "BREAK_EVEN" | "WIN" |
| pnl | Numeric(18,8) | Auto | Calculated profit/loss | 126.55 |
| fees | Numeric(18,8) | No | Trade fees | 0.00 |
| trade_duration | Interval | Auto | Time in trade | "2:30:00" |
| notes | Text | No | Free-form notes | "Breakout trade" |
| tags | JSON | No | Array of strings | ["breakout", "btc"] |
| screenshot_path | String(500) | No | Screenshot filename | "trade_123_screenshot.png" |
| exit_transactions | JSON | No | Legacy partial exits | See 2.1.6 |
| trade_date | Date | No | Trade date | "2024-03-15" |
| created_at | DateTime | Auto | Entry creation | "2024-03-15T10:30:00Z" |
| confirmed_at | DateTime | Auto | When confirmed | "2024-03-15T10:30:00Z" |
| exited_at | DateTime | Auto | When closed | "2024-03-15T13:00:00Z" |
| updated_at | DateTime | Auto | Last update | "2024-03-15T13:00:00Z" |

**Enums:**
```python
TradeDirection = ["long", "short"]
TradeStatus = ["pending", "confirmed", "closed"]
TradeOutcome = ["WIN", "LOSS", "BREAK_EVEN"]
```

**Sample Trade Data:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "account_id": "550e8400-e29b-41d4-a716-446655440001",
  "account_name": "Futures Account",
  "symbol": "BTCUSDT",
  "direction": "long",
  "entry_price": 67234.50,
  "exit_price": 68500.00,
  "stop_loss": 66800.00,
  "take_profit": 68500.00,
  "position_size": 0.1,
  "status": "closed",
  "outcome": "win",
  "pnl": 126.55,
  "fees": 0.00,
  "trade_duration": "2:30:00",
  "notes": "Breakout trade on 4H support level",
  "tags": ["breakout", "btc", "4h"],
  "screenshot_path": null,
  "exit_transactions": null,
  "partial_exits": [],
  "trade_date": "2024-03-15",
  "created_at": "2024-03-15T10:30:00Z",
  "confirmed_at": "2024-03-15T10:30:00Z",
  "exited_at": "2024-03-15T13:00:00Z",
  "updated_at": "2024-03-15T13:00:00Z"
}
```

---

#### 2.1.5 TradePartialExit
Track partial position exits for scaling out of trades.

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| id | UUID | Yes | Primary key | "550e8400-e29b-41d4-a716-446655440004" |
| trade_id | UUID | Yes | FK to Trade | "550e8400-e29b-41d4-a716-446655440003" |
| qty | Numeric(18,8) | Yes | Quantity exited | 0.5 |
| exit_price | Numeric(18,8) | Yes | Exit price | 18550.00 |
| fees | Numeric(18,8) | No | Fees for this exit | 2.50 |
| created_at | DateTime | Auto | Exit timestamp | "2024-03-15T11:00:00Z" |

**Sample Partial Exit:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440004",
  "trade_id": "550e8400-e29b-41d4-a716-446655440003",
  "qty": 1.0,
  "exit_price": 18550.00,
  "fees": 2.50,
  "created_at": "2024-03-15T11:00:00Z"
}
```

---

### 2.2 Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    User     │◄──────┤   Account   │◄──────│    Trade    │
│  (1)        │  1:M  │   (M)       │  1:M  │   (M)       │
└─────────────┘       └─────────────┘       └──────┬──────┘
       ▲                                           │
       │                                           │ 1:M
       │                                    ┌──────┴──────┐
       │                                    │ TradePartial│
       │                                    │   Exit (M)  │
       │                                    └─────────────┘
       │
       │ 1:M                              
┌──────┴──────┐
│  Favorite   │
│  Product(M) │
└─────────────┘
```

**Relationship Details:**
- **User → Accounts**: One user can have multiple accounts (1:M)
- **User → Trades**: One user can have multiple trades (1:M)
- **User → Favorites**: One user can have multiple favorite symbols (1:M)
- **Account → Trades**: One account can have multiple trades (1:M)
- **Trade → Partial Exits**: One trade can have multiple partial exits (1:M)

---

## 3. Business Logic & Rules

### 3.1 Trade Status Lifecycle

```
┌──────────┐    Confirm    ┌──────────┐    Close     ┌──────────┐
│  PENDING │──────────────►│ CONFIRMED│─────────────►│  CLOSED  │
└──────────┘               └──────────┘              └──────────┘
     │                          │
     │ Create with              │ Open position
     │ minimal data             │
     └──────────────────────────┘
```

**Status Definitions:**

| Status | Condition | Description |
|--------|-----------|-------------|
| **PENDING** | `status = "pending"` | Initial state, trade not yet active |
| **CONFIRMED** | `status = "confirmed"` AND no exit data | Open position, actively managed |
| **CLOSED** | `exit_price IS NOT NULL` OR `exit_transactions IS NOT NULL` | Position exited |

**Status Transitions:**
- PENDING → CONFIRMED: When trade is confirmed (sets confirmed_at)
- CONFIRMED → CLOSED: When exit_price or exit_transactions are added
- Automatic determination based on data presence

---

### 3.2 Price Validation by Direction

#### 3.2.1 LONG Trades
**Rules:**
- Take Profit must be **GREATER THAN** Entry Price
- Stop Loss must be **LESS THAN** Entry Price

**Validation Logic:**
```
IF direction = "long":
  IF take_profit <= entry_price:
    ERROR: "Take profit must be greater than entry price for long trades"
  IF stop_loss >= entry_price:
    ERROR: "Stop loss must be less than entry price for long trades"
```

**Visual Representation:**
```
Price
  ↑
  │     TP (valid)
  │      ↑
  │   Entry
  │      ↓
  │     SL (valid)
  └──────────────►
```

#### 3.2.2 SHORT Trades
**Rules:**
- Take Profit must be **LESS THAN** Entry Price
- Stop Loss must be **GREATER THAN** Entry Price

**Validation Logic:**
```
IF direction = "short":
  IF take_profit >= entry_price:
    ERROR: "Take profit must be less than entry price for short trades"
  IF stop_loss <= entry_price:
    ERROR: "Stop loss must be greater than entry price for short trades"
```

**Visual Representation:**
```
Price
  ↑
  │     SL (valid)
  │      ↓
  │   Entry
  │      ↑
  │     TP (valid)
  └──────────────►
```

---

### 3.3 P&L Calculation Formula

#### 3.3.1 Basic P&L (Full Exit)
```
P&L = (price_diff × position_size × point_value) - fees

Where:
- LONG: price_diff = exit_price - entry_price
- SHORT: price_diff = entry_price - exit_price
```

**Example (LONG):**
```
Entry: 67234.50
Exit: 68500.00
Position: 0.1 BTC
Point Value: 1.0
Fees: 0.00

P&L = ((68500.00 - 67234.50) × 0.1 × 1.0) - 0.00
P&L = (1265.50 × 0.1) - 0.00
P&L = 126.55
```

#### 3.3.2 P&L with Partial Exits
```
Total P&L = SUM(partial_exit_pnl) + remaining_position_pnl - total_fees

Where:
- partial_exit_pnl = (exit_price - entry_price) × qty × point_value
- remaining_position_pnl = (take_profit - entry_price) × remaining_qty × point_value
- remaining_qty = position_size - SUM(partial_exit_qty)
```

**Example with Partial Exits:**
```
Entry: 18500.00
Position: 2 contracts
Point Value: 2.00

Partial Exit 1:
  - Qty: 1 contract
  - Exit: 18550.00
  - P&L: (18550 - 18500) × 1 × 2.00 = 100.00

Partial Exit 2:
  - Qty: 0.5 contracts
  - Exit: 18600.00
  - P&L: (18600 - 18500) × 0.5 × 2.00 = 100.00

Remaining Position:
  - Qty: 0.5 contracts (2 - 1 - 0.5)
  - Take Profit: 18700.00
  - P&L: (18700 - 18500) × 0.5 × 2.00 = 200.00

Total P&L = 100.00 + 100.00 + 200.00 - fees
Total P&L = 400.00 - fees
```

#### 3.3.3 Outcome Determination
```
IF pnl > 0:
  outcome = "WIN"
ELIF pnl < 0:
  outcome = "LOSS"
ELSE:
  outcome = "BREAK_EVEN"
```

---

### 3.4 User Data Isolation

**Rule:** Users can only access data they own.

**Implementation:**
- Every query includes `WHERE user_id = current_user_id`
- API returns 404 (not 403) for unauthorized access to avoid revealing existence
- JWT token contains user_id for all requests

**Example Query Pattern:**
```sql
SELECT * FROM trades 
WHERE user_id = 'current-user-uuid' 
  AND id = 'requested-trade-id'
```

**Unauthorized Access Response:**
```json
{
  "error": "Trade not found"
}
// Returns 404 even if trade exists but belongs to different user
```

---

### 3.5 Soft Delete vs Hard Delete

| Entity | Delete Type | Implementation |
|--------|-------------|----------------|
| **User** | Hard Delete | Not supported (deactivate instead) |
| **Account** | Soft Delete | Set `is_active = false` |
| **Trade** | Hard Delete | Permanent deletion with screenshot cleanup |
| **Favorite** | Soft Delete | Set `is_active = false` |
| **Partial Exit** | Hard Delete | Permanent deletion |

**Rationale:**
- **Accounts/Favorites**: Soft delete preserves history, allows reactivation
- **Trades**: Hard delete because they're journal entries (if user wants it gone, it's gone)
- **Soft deleted items**: Filtered from all queries (`WHERE is_active = true`)

---

## 4. User Workflows

### 4.1 Authentication Flows

#### 4.1.1 Email/Password Registration

```
┌─────────┐    Enter name,      ┌──────────┐    Validate    ┌─────────┐
│  Start  │───► email, password │ Validate │───► password   │  Error  │
└─────────┘    ────────────────►│   Input  │    strength    └─────────┘
                                └────┬─────┘
                                     │ Valid
                                     ▼
                              ┌──────────────┐
                              │ Check email  │
                              │   unique?    │
                              └──────┬───────┘
                                     │
                        ┌────────────┼────────────┐
                        │ Exists     │            │ New
                        ▼            │            ▼
                  ┌─────────┐        │    ┌──────────────┐
                  │  Error  │        │    │ Create user  │
                  │ Email   │        │    │ Hash password│
                  │ in use  │        │    └──────┬───────┘
                  └─────────┘        │           │
                                     │           ▼
                                     │    ┌──────────────┐
                                     └───►│ Generate JWT │
                                          │ Set cookies  │
                                          └──────┬───────┘
                                                 │
                                                 ▼
                                          ┌──────────────┐
                                          │  Redirect to │
                                          │   Dashboard  │
                                          └──────────────┘
```

**Password Requirements:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)

**Validation Errors:**
| Error | Message |
|-------|---------|
| Weak password | "Password must be at least 8 characters long" |
| Missing uppercase | "Password must contain at least one uppercase letter" |
| Missing lowercase | "Password must contain at least one lowercase letter" |
| Missing digit | "Password must contain at least one digit" |
| Missing special | "Password must contain at least one special character" |
| Email exists | "Email address already registered" |

---

#### 4.1.2 Email/Password Login

```
┌─────────┐    Enter email      ┌──────────┐    User exists?   ┌─────────┐
│  Start  │───► and password    │  Lookup  │────────────────►│  Error  │
└─────────┘    ────────────────►│   User   │    and active?  │ Invalid │
                                └────┬─────┘                 │credentials
                                     │ Yes
                                     ▼
                              ┌──────────────┐
                              │ Verify       │
                              │ password     │
                              │ hash         │
                              └──────┬───────┘
                                     │
                        ┌────────────┼────────────┐
                        │ Invalid    │            │ Valid
                        ▼            │            ▼
                  ┌─────────┐        │    ┌──────────────┐
                  │  Error  │        │    │ Generate     │
                  │ Invalid │        │    │ access token │
                  │credentials      │    │ Generate     │
                  └─────────┘        │    │ refresh token│
                                     │    └──────┬───────┘
                                     │           │
                                     │           ▼
                                     │    ┌──────────────┐
                                     └───►│ Set HttpOnly │
                                          │ cookies      │
                                          └──────┬───────┘
                                                 │
                                                 ▼
                                          ┌──────────────┐
                                          │  Redirect to │
                                          │   original   │
                                          │   page or    │
                                          │  dashboard   │
                                          └──────────────┘
```

---

#### 4.1.3 Google OAuth Login

```
┌─────────┐    Click Google    ┌──────────┐    Generate      ┌─────────┐
│  Start  │───► Sign In button │ Generate │───► state param  │ Redirect│
└─────────┘    ───────────────►│   State  │    store in      │  to     │
                               └────┬─────┘    session       │ Google  │
                                    │                         └────┬────┘
                                    │                              │
                                    ▼                              │
                             ┌──────────────┐                     │
                             │ Redirect to  │─────────────────────┘
                             │ Google OAuth │
                             │   consent    │
                             └──────────────┘
                                    │
                                    │ User approves
                                    ▼
                             ┌──────────────┐
                             │ Google       │
                             │ callback to  │
                             │ /auth/callback│
                             └──────┬───────┘
                                    │
                                    ▼
                             ┌──────────────┐
                             │ Verify state │
                             │ parameter    │
                             │ matches      │
                             └──────┬───────┘
                                    │
                        ┌───────────┼───────────┐
                        │ Invalid   │           │ Valid
                        ▼           │           ▼
                  ┌─────────┐       │    ┌──────────────┐
                  │  Error  │       │    │ Exchange     │
                  │ Invalid │       │    │ code for     │
                  │ state   │       │    │ access token │
                  └─────────┘       │    └──────┬───────┘
                                    │           │
                                    │           ▼
                                    │    ┌──────────────┐
                                    │    │ Get user     │
                                    │    │ info from    │
                                    │    │ Google       │
                                    │    └──────┬───────┘
                                    │           │
                                    │           ▼
                                    │    ┌──────────────┐
                                    │    │ Create or    │
                                    │    │ update user  │
                                    │    │ record       │
                                    │    └──────┬───────┘
                                    │           │
                                    └───────────┤
                                                ▼
                                         ┌──────────────┐
                                         │ Generate JWT │
                                         │ tokens       │
                                         └──────┬───────┘
                                                │
                                                ▼
                                         ┌──────────────┐
                                         │ Set cookies  │
                                         │ Redirect to  │
                                         │ dashboard    │
                                         └──────────────┘
```

---

#### 4.1.4 Token Refresh

**Automatic Refresh Strategy:**
- Access token expires: 15 minutes
- Refresh token expires: 7 days
- Frontend refreshes: Every 13 minutes (before expiry)
- On 401 response: Attempt refresh once, then redirect to login

```
┌──────────┐     Token near      ┌──────────┐    POST /auth/refresh   ┌──────────┐
│ Frontend │────► expiry (13min) │  Timer   │──────────────────────►│  Backend │
│   App    │    ────────────────►│  Fires   │   with refresh token   │          │
└──────────┘                     └──────────┘                        └────┬─────┘
                                                                          │
                                                                          ▼
                                                                   ┌──────────┐
                                                                   │ Validate │
                                                                   │ refresh  │
                                                                   │  token   │
                                                                   └────┬─────┘
                                                                        │
                                                          ┌─────────────┼─────────────┐
                                                          │ Invalid/    │             │ Valid
                                                          │ Expired     │             │
                                                          ▼             │             ▼
                                                    ┌──────────┐        │      ┌──────────┐
                                                    │ Redirect │        │      │ Generate │
                                                    │ to login │        │      │ new      │
                                                    └──────────┘        │      │ tokens   │
                                                                        │      └────┬─────┘
                                                                        │           │
                                                                        └───────────┤
                                                                                    ▼
                                                                             ┌──────────┐
                                                                             │ Set new  │
                                                                             │ cookies  │
                                                                             └──────────┘
```

---

### 4.2 Trade Management Flows

#### 4.2.1 Creating a Trade

**Entry Points:**
1. **Web Application**: Full form with all fields
2. **Desktop Widget**: Quick entry with essential fields

**Web Form Flow:**
```
┌──────────┐    Navigate to    ┌──────────┐    Click       ┌──────────┐
│  User    │────► Trades page  │  Table   │───► "Add New"  │  Modal   │
│          │    ──────────────►│  View    │   ───────────►│  Opens   │
└──────────┘                   └──────────┘               └────┬─────┘
                                                               │
                                                               ▼
                                                        ┌──────────────┐
                                                        │ Form Fields: │
                                                        │ - Account    │
                                                        │ - Symbol     │
                                                        │ - Direction  │
                                                        │ - Entry Price│
                                                        │ - Stop Loss  │
                                                        │ - Take Profit│
                                                        │ - Position   │
                                                        │   Size       │
                                                        │ - Notes      │
                                                        │ - Tags       │
                                                        │ - Trade Date │
                                                        └──────┬───────┘
                                                               │
                                                               │ User fills
                                                               ▼
                                                        ┌──────────────┐
                                                        │ Auto-fetch   │
                                                        │ defaults from│
                                                        │ favorites    │
                                                        └──────┬───────┘
                                                               │
                                                               │ Validation:
                                                               │ - Required
                                                               │   fields
                                                               │ - Price
                                                               │   direction
                                                               └──────┬───────┘
                                                                      │
                                                        ┌─────────────┼─────────────┐
                                                        │ Invalid     │             │ Valid
                                                        ▼             │             ▼
                                                  ┌──────────┐        │      ┌──────────┐
                                                  │ Show     │        │      │ POST to  │
                                                  │ errors   │        │      │ /trades  │
                                                  │ inline   │        │      └────┬─────┘
                                                  └──────────┘        │           │
                                                                      │           ▼
                                                                      │    ┌──────────┐
                                                                      │    │ Calculate│
                                                                      │    │ P&L      │
                                                                      │    │ if exit  │
                                                                      │    │ price    │
                                                                      │    └────┬─────┘
                                                                      │           │
                                                                      └───────────┤
                                                                                  ▼
                                                                           ┌──────────┐
                                                                           │ Save to  │
                                                                           │ database │
                                                                           └────┬─────┘
                                                                               │
                                                                               ▼
                                                                        ┌──────────┐
                                                                        │ Return   │
                                                                        │ success  │
                                                                        │ with     │
                                                                        │ trade    │
                                                                        │ data     │
                                                                        └────┬─────┘
                                                                            │
                                                                            ▼
                                                                     ┌──────────┐
                                                                     │ Close    │
                                                                     │ modal    │
                                                                     │ Refresh  │
                                                                     │ table    │
                                                                     └──────────┘
```

**Validation Rules:**
| Field | Validation | Error Message |
|-------|------------|---------------|
| symbol | Required, max 50 chars | "Symbol is required" |
| direction | Required, enum check | "Direction must be 'long' or 'short'" |
| entry_price | Required, > 0 | "Entry price must be greater than 0" |
| stop_loss | Optional, validated per direction | See 3.2 |
| take_profit | Optional, validated per direction | See 3.2 |
| position_size | Optional, > 0 | "Position size must be greater than 0" |

---

#### 4.2.2 Editing a Trade

**Edit Scenarios:**
1. **Modify trade details** (symbol, prices, notes, etc.)
2. **Add partial exits** (scale out of position)
3. **Remove partial exits** (correction)
4. **Close trade** (add exit price)

**Flow:**
```
┌──────────┐    Click Edit    ┌──────────┐    Load trade    ┌──────────┐
│  Trade   │─────────────────►│  Modal   │───────────────►│  Form    │
│  Row     │                  │  Opens   │   data         │  Populated│
└──────────┘                  └──────────┘                └────┬─────┘
                                                               │
                                                               ▼
                                                        ┌──────────────┐
                                                        │ Edit Mode:   │
                                                        │ - All fields │
                                                        │   editable   │
                                                        │ - Partial    │
                                                        │   exits can  │
                                                        │   be added/  │
                                                        │   removed    │
                                                        └──────┬───────┘
                                                               │
                                                               │ User modifies
                                                               ▼
                                                        ┌──────────────┐
                                                        │ Add Partial  │
                                                        │ Exit:        │
                                                        │ - Qty        │
                                                        │ - Exit Price │
                                                        │ - Fees       │
                                                        └──────┬───────┘
                                                               │
                                                               │ Recalculate
                                                               │ P&L
                                                               ▼
                                                        ┌──────────────┐
                                                        │ Validation   │
                                                        └──────┬───────┘
                                                               │
                                                 ┌─────────────┼─────────────┐
                                                 │ Invalid     │             │ Valid
                                                 ▼             │             ▼
                                           ┌──────────┐        │      ┌──────────┐
                                           │ Show     │        │      │ PUT to   │
                                           │ errors   │        │      │ /trades/ │
                                           │          │        │      │ :id      │
                                           └──────────┘        │      └────┬─────┘
                                                               │           │
                                                               └───────────┤
                                                                           ▼
                                                                    ┌──────────┐
                                                                    │ Update   │
                                                                    │ database │
                                                                    │ Recalc   │
                                                                    │ P&L      │
                                                                    └────┬─────┘
                                                                        │
                                                                        ▼
                                                                 ┌──────────┐
                                                                 │ Close    │
                                                                 │ modal    │
                                                                 │ Show     │
                                                                 │ success  │
                                                                 └──────────┘
```

---

#### 4.2.3 Viewing Trade Details

**View Mode Features:**
- Read-only display of all fields
- P&L calculation breakdown
- Partial exits list with individual P&L
- Screenshot display (if attached)
- Tags displayed as badges
- Notes in formatted text
- Trade duration calculation

---

#### 4.2.4 Deleting a Trade

**Flow:**
```
┌──────────┐    Click Delete    ┌──────────┐    User confirms   ┌──────────┐
│  Trade   │───────────────────►│ Confirm  │──────────────────►│ DELETE   │
│  Row     │                    │ Dialog   │   "Yes, delete"   │ /trades/ │
└──────────┘                    └──────────┘                   │ :id      │
                                                               └────┬─────┘
                                                                    │
                                                                    ▼
                                                             ┌──────────┐
                                                             │ Remove   │
                                                             │ from DB  │
                                                             │ Delete   │
                                                             │ screenshot│
                                                             │ file if  │
                                                             │ exists   │
                                                             └────┬─────┘
                                                                  │
                                                                  ▼
                                                           ┌──────────┐
                                                           │ Return   │
                                                           │ success  │
                                                           └────┬─────┘
                                                                │
                                                                ▼
                                                         ┌──────────┐
                                                         │ Remove   │
                                                         │ row from │
                                                         │ table    │
                                                         │ Show     │
                                                         │ toast    │
                                                         └──────────┘
```

---

### 4.3 Account Management Flows

#### 4.3.1 Creating an Account

**Fields:**
- Name (required, max 100 chars)
- Opening Balance (optional, default 0)

**Flow:**
1. User clicks "Add Account" button
2. Modal opens with form
3. User enters name and optional balance
4. Validation: Name required, unique per user
5. POST to `/api/accounts`
6. Account appears in table and global account switcher

---

#### 4.3.2 Editing an Account

**Editable Fields:**
- Name
- Opening Balance
- Is Active (reactivation)

**Flow:**
1. Click Edit on account row
2. Modal opens with current values
3. User modifies fields
4. PUT to `/api/accounts/:id`
5. Table updates with new values
6. Metrics recalculate automatically

---

#### 4.3.3 Deactivating an Account

**Soft Delete Flow:**
1. Click Delete on account row
2. Confirmation dialog: "Deactivating will hide this account from filters. Existing trades remain."
3. User confirms
4. DELETE to `/api/accounts/:id` (sets is_active = false)
5. Account disappears from:
   - Accounts table
   - Global account switcher
   - Trade creation dropdown
6. Existing trades still reference account (shown as "Account Name (Inactive)")

---

#### 4.3.4 Viewing Account Performance

**Metrics Displayed:**
- Trade count
- Total P&L
- Profit percentage (vs opening balance)
- Win rate
- Average P&L per trade

**Drill Down:**
- Click account name to view all trades for that account
- Applies account filter automatically

---

### 4.4 Favorite Products Flows

#### 4.4.1 Adding a Favorite Symbol

**Fields:**
- Symbol (required, auto-uppercase)
- Point Value (optional, default 1.0)
- Fees (optional, default 0.0)

**Validation:**
- Symbol required
- Symbol unique per user
- Point value > 0
- Fees >= 0

**Auto-Population:**
When creating a trade with a favorited symbol:
- Point value auto-fills from favorite
- Fees auto-fill from favorite
- User can override

---

#### 4.4.2 Editing a Favorite

**Use Case:** Adjusting point values or fees as market conditions change

**Flow:**
1. Click Edit on favorite row
2. Modify point value or fees
3. Save updates
4. Future trades use new defaults
5. Existing trades unchanged (historical accuracy)

---

### 4.5 Analysis Flows

#### 4.5.1 Dashboard Analytics

**Default View:**
- Date range: Last 30 days
- Account: All accounts
- Metrics update automatically

**User Interactions:**
1. **Change Date Range:**
   - Click "From" date picker
   - Click "To" date picker
   - Metrics recalculate
   - Charts update

2. **Filter by Account:**
   - Use global account switcher
   - All dashboard data updates
   - URL may update for shareability

3. **Hover Charts:**
   - Equity curve: Show P&L value at date
   - Recent P&L: Show trade details

---

#### 4.5.2 Trade History Analysis

**Filtering:**
- By symbol (search input)
- By direction (dropdown)
- By date range (date pickers)
- By account (global switcher)

**Sorting:**
- Default: Date descending (newest first)
- Click column headers to sort

**Pagination:**
- 15 trades per page
- Page numbers at bottom
- Previous/Next buttons

**Statistics Bar:**
Shows aggregated data for current filter:
- Filtered trade count
- Filtered total P&L
- Filtered win rate
- Filtered average P&L

---

### 4.6 Desktop Widget Workflows

#### 4.6.1 Quick Trade Entry

**Widget Layout:**
- Collapsible header (Trade Info)
- Main form fields
- Recent trades panel
- Settings button

**Trade Info Section (Collapsible):**
- Trade Date (default: today)
- Account (dropdown)
- Symbol (searchable dropdown)

**Main Form Fields:**
- Direction (Long/Short toggle)
- Outcome (Win/Loss/Break Even)
- Entry Price
- Position Size
- Stop Loss (optional)
- Take Profit (optional)
- Partial Exits (add/remove rows)
- Notes textarea
- Screenshot upload

**Flow:**
```
┌──────────────┐
│  Widget Open │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│ Expand Trade Info│
│ (if needed)      │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Select Account   │
│ Select Symbol    │
│ (auto-populates  │
│  defaults)       │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Set Direction    │
│ Enter Entry Price│
│ Enter Position   │
│ Size             │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Add Partial Exit?│
│ (optional)       │
└──────┬───────────┘
       │
       ├── No ───┐
       │         ▼
       │  ┌──────────────┐
       │  │ Set Take     │
       │  │ Profit       │
       │  │ (for P&L)    │
       │  └──────┬───────┘
       │         │
       │◄────────┘
       ▼
┌──────────────────┐
│ Add Notes        │
│ Attach Screenshot│
│ (optional)       │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Click SAVE TRADE │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Validate fields  │
│ Calculate P&L    │
│ POST to API      │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Show P&L result  │
│ Flash success    │
│ Clear form       │
│ Update recent    │
│ trades panel     │
└──────────────────┘
```

---

#### 4.6.2 Widget Settings

**Settings Panel:**
- Always on Top toggle
- Dark/Light mode toggle
- View All Trades link (opens browser)

**Always on Top:**
- When enabled: Widget stays above other windows
- Useful while using TradingView or broker platform

---

## 5. Page Specifications

### 5.1 Dashboard Page (`/`)

**Purpose:** High-level trading performance overview

**Layout Structure:**
```
┌─────────────────────────────────────────────────────────────┐
│  NAVBAR (60px height)                                       │
│  - Logo | Dashboard | Trades | Accounts | Favorites         │
│  - Theme Toggle | Account Switcher | User Profile           │
├─────────────────────────────────────────────────────────────┤
│  MAIN CONTENT AREA                                          │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ FILTER BAR (Date Range + Account)                    │  │
│  │ FROM [date picker] TO [date picker]                  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ METRICS GRID (4x2 = 8 cards)                         │  │
│  │ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐          │  │
│  │ │ Total  │ │ Win    │ │ Total  │ │ Profit │          │  │
│  │ │Trades  │ │ Rate   │ │ P&L    │ │ Factor │          │  │
│  │ └────────┘ └────────┘ └────────┘ └────────┘          │  │
│  │ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐          │  │
│  │ │ Avg    │ │ Avg    │ │ Best   │ │ Worst  │          │  │
│  │ │ Win    │ │ Loss   │ │ Trade  │ │ Trade  │          │  │
│  │ └────────┘ └────────┘ └────────┘ └────────┘          │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────┐ ┌──────────────────────────┐  │
│  │                          │ │                          │  │
│  │   EQUITY CURVE CHART     │ │   RECENT P&L CHART       │  │
│  │   (Line chart)           │ │   (Bar chart)            │  │
│  │                          │ │   Green/Red bars         │  │
│  │                          │ │                          │  │
│  └──────────────────────────┘ └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Components:**

| Component | Data Source | Interaction |
|-----------|-------------|-------------|
| **Date Range** | User input | On change: refresh all metrics |
| **Account Switcher** | `/api/accounts` | Global filter affects all pages |
| **Metric Cards** | `/api/metrics` | Static display, no interaction |
| **Equity Curve** | `recent_pnl` from metrics | Hover: show value at date |
| **Recent P&L** | `by_symbol` or `recent_pnl` | Hover: show trade details |

**Empty State:**
- Message: "No trades found for the selected period"
- Call to action: "Add your first trade" button

---

### 5.2 Trades List Page (`/trades`)

**Purpose:** View, filter, and manage all trades

**Layout Structure:**
```
┌─────────────────────────────────────────────────────────────┐
│  NAVBAR                                                     │
├─────────────────────────────────────────────────────────────┤
│  MAIN CONTENT                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ FILTER BAR                                           │  │
│  │ Symbol: [search]  Direction: [all/long/short]        │  │
│  │ From: [date] To: [date]         [Reset] [Apply]      │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ STATS BAR (based on current filter)                  │  │
│  │ Count: 156 | P&L: +$3,450 | Win Rate: 60% | Avg: $22 │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ ACTION BAR                                           │  │
│  │                           [+ Add New Trade]          │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ TRADES TABLE                                         │  │
│  │ ┌──────┬────────┬───────┬─────┬───────┬─────┬───────┐ │  │
│  │ │Acct  │Symbol  │Dir    │SL   │Entry  │TP   │P&L    │ │  │
│  │ ├──────┼────────┼───────┼─────┼───────┼─────┼───────┤ │  │
│  │ │Main  │BTC     │LONG   │...  │...    │...  │+$126  │ │  │
│  │ │Main  │ETH     │SHORT  │...  │...    │...  │-$45   │ │  │
│  │ │...   │...     │...    │...  │...    │...  │...    │ │  │
│  │ └──────┴────────┴───────┴─────┴───────┴─────┴───────┘ │  │
│  │                                                      │  │
│  │ Pagination: [<] 1 2 3 ... 10 [>]                    │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Table Columns:**

| Column | Data Field | Format | Sortable |
|--------|------------|--------|----------|
| Account | account_name | Text | Yes |
| Symbol | symbol | Uppercase | Yes |
| Direction | direction | Badge (Long/Short) | Yes |
| Stop Loss | stop_loss | Number (2 decimals) | Yes |
| Entry | entry_price | Number (2 decimals) | Yes |
| Take Profit | take_profit | Number (2 decimals) | Yes |
| P&L | pnl | Currency, colored | Yes |
| Date | trade_date | Date (YYYY-MM-DD) | Yes |
| Actions | - | View / Edit / Delete | No |

**Row Interactions:**
- **Click row:** Open view modal (read-only)
- **Click Edit:** Open edit modal
- **Click Delete:** Show confirmation, then remove

**Pagination:**
- 15 rows per page
- Page numbers with ellipsis for many pages
- Previous/Next buttons
- Shows "Showing 1-15 of 156 trades"

---

### 5.3 Trade Edit/View Modal

**Purpose:** Create, view, or edit trade details

**Layout Structure:**
```
┌───────────────────────────────────────────────────────────┐
│  Create Trade / Edit Trade / View Trade          [X Close]│
├───────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ TRADE INFO (Collapsible)                           │  │
│  │ - Trade Date: [date picker]                        │  │
│  │ - Account: [dropdown]                              │  │
│  │ - Symbol: [search input with favorites]            │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ TRADE DETAILS                                      │  │
│  │ - Direction: [Long ▢] [Short ▢]                    │  │
│  │ - Outcome: [Win ▢] [Loss ▢] [Break Even ▢]         │  │
│  │ - Entry Price: [number]                            │  │
│  │ - Position Size: [number]                          │  │
│  │ - Stop Loss: [number] (optional)                   │  │
│  │ - Take Profit: [number] (optional)                 │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ PARTIAL EXITS (Expandable)                         │  │
│  │ [+ Add Partial Exit]                               │  │
│  │ ┌──────┬───────────┬──────┬────────┐               │  │
│  │ │ Qty  │Exit Price │ Fees │ Remove │               │  │
│  │ ├──────┼───────────┼──────┼────────┤               │  │
│  │ │ 1.0  │ 18550.00  │ 2.50 │   [X]  │               │  │
│  │ └──────┴───────────┴──────┴────────┘               │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ NOTES & SCREENSHOT                                 │  │
│  │ - Tags: [tag input] [tag1] [tag2] [x]              │  │
│  │ - Notes: [textarea]                                │  │
│  │ - Screenshot: [Choose File] [preview thumbnail]    │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ CALCULATED P&L                                     │  │
│  │ Total P&L: +$126.55                                │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│                    [Cancel]  [Save Trade]                   │
│                                                             │
└───────────────────────────────────────────────────────────┘
```

**Field Specifications:**

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| Trade Date | Date picker | Yes | Not in future |
| Account | Dropdown | Yes | Must select valid account |
| Symbol | Text input | Yes | Auto-uppercase |
| Direction | Radio/Toggle | Yes | Long or Short |
| Outcome | Radio | No | Win/Loss/Break Even |
| Entry Price | Number | Yes | > 0 |
| Position Size | Number | No | > 0 |
| Stop Loss | Number | No | Validated per direction |
| Take Profit | Number | No | Validated per direction |
| Tags | Tag input | No | Comma-separated, stored as array |
| Notes | Textarea | No | Max 5000 chars |
| Screenshot | File upload | No | Max 5MB, images only |

**Partial Exit Fields:**
| Field | Type | Required |
|-------|------|----------|
| Qty | Number | Yes |
| Exit Price | Number | Yes |
| Fees | Number | No |

---

### 5.4 Accounts Page (`/accounts`)

**Purpose:** Manage trading accounts

**Layout Structure:**
```
┌─────────────────────────────────────────────────────────────┐
│  NAVBAR                                                     │
├─────────────────────────────────────────────────────────────┤
│  MAIN CONTENT                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ ACTION BAR                                           │  │
│  │ [+ Add Account]                                      │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ ACCOUNTS TABLE                                       │  │
│  │ ┌────────────┬──────────────┬───────┬───────┬────────┐│  │
│  │ │ Name       │Open Balance  │Trades │P&L    │Actions ││  │
│  │ ├────────────┼──────────────┼───────┼───────┼────────┤│  │
│  │ │ Futures    │$25,000.00    │  156  │+$3,450│Edit/Del││  │
│  │ │ Crypto     │$10,000.00    │   42  │-$850  │Edit/Del││  │
│  │ │ Stocks     │$50,000.00    │   89  │+$1,200│Edit/Del││  │
│  │ └────────────┴──────────────┴───────┴───────┴────────┘│  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Table Columns:**

| Column | Data | Format |
|--------|------|--------|
| Name | name | Text |
| Opening Balance | opening_balance | Currency |
| Trades | trade_count | Integer (computed) |
| P&L | total_pnl | Currency, colored |
| Profit % | profit_percent | Percentage, colored |
| Status | is_active | Active/Inactive badge |
| Actions | - | Edit / Deactivate |

---

### 5.5 Favorites Page (`/favorites`)

**Purpose:** Manage frequently traded symbols with default settings

**Layout Structure:**
```
┌─────────────────────────────────────────────────────────────┐
│  NAVBAR                                                     │
├─────────────────────────────────────────────────────────────┤
│  MAIN CONTENT                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ ACTION BAR                                           │  │
│  │ [+ Add Symbol]                                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ FAVORITES TABLE                                      │  │
│  │ ┌────────┬─────────────┬──────┬───────────┬─────────┐ │  │
│  │ │Symbol  │Point Value  │Fees  │Status     │Actions  │ │  │
│  │ ├────────┼─────────────┼──────┼───────────┼─────────┤ │  │
│  │ │ES      │$50.00       │$5.00 │Active     │Edit/Del │ │  │
│  │ │NQ      │$20.00       │$5.00 │Active     │Edit/Del │ │  │
│  │ │MNQ     │$2.00        │$2.50 │Active     │Edit/Del │ │  │
│  │ │BTC     │$1.00        │$0.50 │Active     │Edit/Del │ │  │
│  │ └────────┴─────────────┴──────┴───────────┴─────────┘ │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ HELP TEXT                                            │  │
│  │ Point values represent the dollar amount per point.  │  │
│  │ Example: ES (E-mini S&P) = $50 per point.            │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

### 5.6 Login Page (`/login`)

**Purpose:** User authentication

**Layout Structure:**
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                      ┌───────────────────┐                  │
│                      │                   │                  │
│                      │   [Logo]          │                  │
│                      │   TRADELOGGER     │                  │
│                      │                   │                  │
│                      ├───────────────────┤                  │
│                      │                   │                  │
│                      │ [Sign In] [Register]                  │
│                      │                   │                  │
│                      ├───────────────────┤                  │
│                      │                   │                  │
│                      │ [Google Button]   │                  │
│                      │                   │                  │
│                      ├─────────┬─────────┤                  │
│                      │  ─────  │  ─────  │                  │
│                      │    or   │         │                  │
│                      ├─────────┴─────────┤                  │
│                      │                   │                  │
│                      │ Email: [        ] │                  │
│                      │                   │                  │
│                      │ Password: [     ] │                  │
│                      │                   │                  │
│                      │ [  Sign In  ]     │                  │
│                      │                   │                  │
│                      └───────────────────┘                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Tab Content:**

**Sign In Tab:**
- Email field
- Password field
- Sign In button

**Register Tab:**
- Name field
- Email field
- Password field
- Confirm Password field
- Create Account button

**Common:**
- Google OAuth button
- Divider with "or"

---

## 6. API Contract

### 6.1 Authentication Endpoints

#### POST /api/auth/register
Register new user with email/password.

**Request:**
```json
{
  "email": "trader@example.com",
  "password": "SecurePass123!",
  "name": "John Trader"
}
```

**Success Response (201):**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "trader@example.com",
    "name": "John Trader",
    "auth_provider": "email",
    "is_active": true,
    "created_at": "2024-03-15T10:30:00Z",
    "updated_at": "2024-03-15T10:30:00Z"
  }
}
```

**Error Response (400):**
```json
{
  "error": "Email address already registered"
}
```

---

#### POST /api/auth/login
Authenticate user with email/password.

**Request:**
```json
{
  "email": "trader@example.com",
  "password": "SecurePass123!"
}
```

**Success Response (200):**
```json
{
  "message": "Login successful",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "trader@example.com",
    "name": "John Trader",
    "auth_provider": "email",
    "is_active": true
  }
}
```
**Note:** JWT tokens set as HttpOnly cookies.

**Error Response (401):**
```json
{
  "error": "Invalid email or password"
}
```

---

#### GET /api/auth/google/login
Initiate Google OAuth flow.

**Response:** Redirects to Google OAuth consent screen.

---

#### GET /api/auth/callback
Handle Google OAuth callback.

**Query Parameters:**
- `code` - Authorization code from Google
- `state` - CSRF protection state

**Success:** Redirects to dashboard with cookies set.

**Error Response (400):**
```json
{
  "error": "Invalid state parameter"
}
```

---

#### POST /api/auth/refresh
Refresh access token using refresh token.

**Request:** None (uses refresh_token cookie)

**Success Response (200):**
```json
{
  "message": "Token refreshed successfully"
}
```

**Error Response (401):**
```json
{
  "error": "Invalid or expired refresh token"
}
```

---

#### POST /api/auth/logout
Clear authentication cookies.

**Success Response (200):**
```json
{
  "message": "Logout successful"
}
```

---

#### GET /api/auth/me
Get current authenticated user info.

**Success Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "trader@example.com",
  "name": "John Trader",
  "profile_picture": null,
  "auth_provider": "email",
  "is_active": true,
  "created_at": "2024-03-15T10:30:00Z",
  "updated_at": "2024-03-15T10:30:00Z"
}
```

**Error Response (401):**
```json
{
  "error": "Authentication required"
}
```

---

#### GET /api/auth/status
Check authentication status (public endpoint).

**Success Response (200):**
```json
{
  "authenticated": true,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "trader@example.com",
    "name": "John Trader"
  }
}
```

Or if not authenticated:
```json
{
  "authenticated": false,
  "user": null
}
```

---

### 6.2 Trade Endpoints

#### GET /api/trades
List trades with filtering and pagination.

**Query Parameters:**
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| symbol | string | Filter by symbol | - |
| direction | string | "long" or "short" | - |
| status | string | "pending", "confirmed", "closed" | - |
| account_id | string | Filter by account UUID | - |
| start_date | date | ISO date (YYYY-MM-DD) | - |
| end_date | date | ISO date (YYYY-MM-DD) | - |
| page | integer | Page number | 1 |
| per_page | integer | Items per page | 50 |

**Success Response (200):**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440003",
      "account_id": "550e8400-e29b-41d4-a716-446655440001",
      "account_name": "Futures Account",
      "symbol": "BTCUSDT",
      "direction": "long",
      "entry_price": 67234.50,
      "exit_price": 68500.00,
      "stop_loss": 66800.00,
      "take_profit": 68500.00,
      "position_size": 0.1,
      "status": "closed",
      "outcome": "win",
      "pnl": 126.55,
      "fees": 0.00,
      "trade_date": "2024-03-15",
      "created_at": "2024-03-15T10:30:00Z"
    }
  ],
  "total": 156,
  "page": 1,
  "per_page": 50,
  "pages": 4
}
```

---

#### POST /api/trades
Create a new trade.

**Request:**
```json
{
  "account_id": "550e8400-e29b-41d4-a716-446655440001",
  "symbol": "BTCUSDT",
  "direction": "long",
  "entry_price": 67234.50,
  "stop_loss": 66800.00,
  "take_profit": 68500.00,
  "position_size": 0.1,
  "notes": "Breakout trade",
  "tags": ["breakout", "btc"],
  "trade_date": "2024-03-15"
}
```

**Success Response (201):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "account_id": "550e8400-e29b-41d4-a716-446655440001",
  "symbol": "BTCUSDT",
  "direction": "long",
  "entry_price": 67234.50,
  "status": "confirmed",
  "pnl": null,
  "created_at": "2024-03-15T10:30:00Z"
}
```

**Error Response (400):**
```json
{
  "error": "Symbol is required"
}
```

---

#### GET /api/trades/:id
Get single trade details.

**Success Response (200):**
Full trade object with all fields.

**Error Response (404):**
```json
{
  "error": "Trade not found"
}
```

---

#### PUT /api/trades/:id
Update trade details.

**Request:** Same as POST, all fields optional.

**Success Response (200):**
Updated trade object.

---

#### DELETE /api/trades/:id
Delete a trade permanently.

**Success Response (200):**
```json
{
  "message": "Trade deleted successfully"
}
```

---

### 6.3 Partial Exit Endpoints

#### GET /api/trades/:id/partial-exits
List partial exits for a trade.

**Success Response (200):**
```json
{
  "partial_exits": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440004",
      "trade_id": "550e8400-e29b-41d4-a716-446655440003",
      "qty": 1.0,
      "exit_price": 18550.00,
      "fees": 2.50,
      "created_at": "2024-03-15T11:00:00Z"
    }
  ]
}
```

---

#### POST /api/trades/:id/partial-exits
Add partial exit to trade.

**Request:**
```json
{
  "qty": 0.5,
  "exit_price": 18600.00,
  "fees": 2.50
}
```

**Success Response (201):**
Created partial exit object.

---

### 6.4 Metrics Endpoint

#### GET /api/metrics
Get trading statistics.

**Query Parameters:**
- `account_id` - Filter by account
- `start_date` - ISO date
- `end_date` - ISO date

**Success Response (200):**
```json
{
  "total_trades": 156,
  "winning_trades": 94,
  "losing_trades": 62,
  "win_rate": 0.6026,
  "total_pnl": 8475.50,
  "avg_pnl_per_trade": 54.33,
  "avg_win": 145.75,
  "avg_loss": -84.25,
  "best_trade": 425.00,
  "worst_trade": -180.50,
  "profit_factor": 1.84,
  "by_symbol": [
    {
      "symbol": "ES",
      "count": 45,
      "pnl": 3200.00
    },
    {
      "symbol": "NQ",
      "count": 38,
      "pnl": 2800.50
    }
  ],
  "by_direction": [
    {
      "direction": "long",
      "count": 89,
      "pnl": 6200.00
    },
    {
      "direction": "short",
      "count": 67,
      "pnl": 2275.50
    }
  ],
  "recent_pnl": [75, -25, 120, 45, -60, 90, 30, -15, 55, 80]
}
```

---

### 6.5 Account Endpoints

#### GET /api/accounts
List all accounts for current user.

**Success Response (200):**
```json
{
  "accounts": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "Futures Account",
      "opening_balance": 25000.00,
      "is_active": true,
      "trade_count": 156,
      "total_pnl": 3450.75,
      "profit_percent": 13.80,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

#### POST /api/accounts
Create new account.

**Request:**
```json
{
  "name": "Crypto Account",
  "opening_balance": 10000.00
}
```

**Success Response (201):**
Created account object.

---

#### PUT /api/accounts/:id
Update account.

**Request:**
```json
{
  "name": "Updated Account Name",
  "opening_balance": 15000.00,
  "is_active": true
}
```

**Success Response (200):**
Updated account object.

---

#### DELETE /api/accounts/:id
Soft delete account (sets is_active = false).

**Success Response (200):**
```json
{
  "message": "Account deactivated successfully"
}
```

---

### 6.6 Favorite Endpoints

#### GET /api/favorites
List favorite products.

**Success Response (200):**
```json
{
  "favorites": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "symbol": "ES",
      "point_value": 50.00,
      "fees": 5.00,
      "is_active": true,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

#### POST /api/favorites
Create favorite symbol.

**Request:**
```json
{
  "symbol": "MNQ",
  "point_value": 2.00,
  "fees": 2.50
}
```

**Success Response (201):**
Created favorite object.

---

#### PUT /api/favorites/:id
Update favorite.

**Request:**
```json
{
  "point_value": 2.50,
  "fees": 3.00
}
```

---

#### DELETE /api/favorites/:id
Soft delete favorite.

**Success Response (200):**
```json
{
  "message": "Favorite removed successfully"
}
```

---

## 7. Component Inventory

### 7.1 Reusable Components

#### 7.1.1 Metric Card
**Purpose:** Display single metric with label

**Props:**
| Prop | Type | Description |
|------|------|-------------|
| value | string/number | The metric value |
| label | string | Metric name |
| trend | string | "up", "down", or null |
| format | string | "currency", "percentage", "number" |

**Example:**
```
┌────────────────┐
│     $3,450     │
│   Total P&L    │
└────────────────┘
```

---

#### 7.1.2 Data Table
**Purpose:** Display tabular data with sorting

**Props:**
| Prop | Type | Description |
|------|------|-------------|
| columns | array | Column definitions |
| data | array | Row data |
| pagination | object | { page, perPage, total } |
| onSort | function | Sort callback |
| onRowClick | function | Row click handler |

**Features:**
- Sortable column headers
- Pagination controls
- Row hover effects
- Action buttons column

---

#### 7.1.3 Form Input
**Purpose:** Text/number input with validation

**Props:**
| Prop | Type | Description |
|------|------|-------------|
| type | string | "text", "email", "password", "number", "date" |
| label | string | Input label |
| placeholder | string | Placeholder text |
| required | boolean | Required field |
| error | string | Error message |
| value | any | Current value |
| onChange | function | Change handler |

---

#### 7.1.4 Button
**Purpose:** Action trigger

**Variants:**
- Primary (main action)
- Secondary (alternative action)
- Danger (destructive action)
- Ghost (low emphasis)

**Props:**
| Prop | Type | Description |
|------|------|-------------|
| variant | string | Button style variant |
| size | string | "sm", "md", "lg" |
| disabled | boolean | Disabled state |
| loading | boolean | Loading spinner |
| onClick | function | Click handler |

---

#### 7.1.5 Badge
**Purpose:** Status indicator

**Variants:**
- Success (green)
- Warning (amber)
- Error (red)
- Neutral (gray)

**Props:**
| Prop | Type | Description |
|------|------|-------------|
| variant | string | Badge color variant |
| children | string | Badge text |

**Examples:**
```
[WIN] [LOSS] [PENDING] [CONFIRMED] [CLOSED]
```

---

#### 7.1.6 Modal
**Purpose:** Overlay dialog

**Props:**
| Prop | Type | Description |
|------|------|-------------|
| isOpen | boolean | Show/hide modal |
| onClose | function | Close handler |
| title | string | Modal title |
| size | string | "sm", "md", "lg", "xl" |
| children | node | Modal content |

**Features:**
- Backdrop click to close
- Escape key to close
- Focus trap inside modal

---

#### 7.1.7 Date Picker
**Purpose:** Select date

**Props:**
| Prop | Type | Description |
|------|------|-------------|
| value | date | Selected date |
| onChange | function | Change handler |
| minDate | date | Minimum selectable date |
| maxDate | date | Maximum selectable date |

---

#### 7.1.8 Select/Dropdown
**Purpose:** Select from list of options

**Props:**
| Prop | Type | Description |
|------|------|-------------|
| options | array | { value, label } pairs |
| value | string | Selected value |
| onChange | function | Change handler |
| placeholder | string | Default text |
| searchable | boolean | Enable search/filter |

---

#### 7.1.9 Tag Input
**Purpose:** Add/remove tags

**Props:**
| Prop | Type | Description |
|------|------|-------------|
| tags | array | Current tags |
| onAdd | function | Add tag handler |
| onRemove | function | Remove tag handler |
| suggestions | array | Autocomplete suggestions |

---

#### 7.1.10 File Upload
**Purpose:** Upload screenshot files

**Props:**
| Prop | Type | Description |
|------|------|-------------|
| accept | string | File types (e.g., "image/*") |
| maxSize | number | Max file size in MB |
| onUpload | function | Upload handler |
| preview | boolean | Show preview thumbnail |

---

#### 7.1.11 Chart - Line
**Purpose:** Display equity curve

**Props:**
| Prop | Type | Description |
|------|------|-------------|
| data | array | { x, y } data points |
| xAxis | string | X axis label |
| yAxis | string | Y axis label |
| color | string | Line color |

---

#### 7.1.12 Chart - Bar
**Purpose:** Display recent P&L

**Props:**
| Prop | Type | Description |
|------|------|-------------|
| data | array | { label, value } data points |
| positiveColor | string | Color for positive values |
| negativeColor | string | Color for negative values |

---

#### 7.1.13 Tabs
**Purpose:** Switch between content panels

**Props:**
| Prop | Type | Description |
|------|------|-------------|
| tabs | array | { id, label, content } |
| activeTab | string | Currently active tab ID |
| onChange | function | Tab change handler |

---

#### 7.1.14 Toast/Notification
**Purpose:** Show temporary messages

**Variants:**
- Success
- Error
- Warning
- Info

**Props:**
| Prop | Type | Description |
|------|------|-------------|
| message | string | Toast message |
| variant | string | Toast type |
| duration | number | Auto-dismiss time (ms) |
| onClose | function | Close handler |

---

### 7.2 Component States

#### 7.2.1 Default State
Normal appearance, ready for interaction.

#### 7.2.2 Hover State
Visual feedback when mouse is over element.

#### 7.2.3 Active/Selected State
Element is currently active or selected.

#### 7.2.4 Disabled State
Element cannot be interacted with.
- Reduced opacity
- No hover effects
- Cursor: not-allowed

#### 7.2.5 Loading State
Action in progress.
- Loading spinner or skeleton
- Reduced opacity
- Disable interactions

#### 7.2.6 Error State
Validation error or failure.
- Red border/text
- Error message
- Shake animation (optional)

#### 7.2.7 Success State
Action completed successfully.
- Green checkmark
- Success message
- Brief highlight

---

## 8. Sample Data Sets

### 8.1 New User Scenario

**User Registration:**
```json
POST /api/auth/register
{
  "email": "newtrader@example.com",
  "password": "SecurePass123!",
  "name": "New Trader"
}
```

**Initial State:**
- No accounts
- No trades
- No favorites
- Empty dashboard

---

### 8.2 Active Trader Scenario

**User:**
```json
{
  "id": "user-123",
  "email": "activetrader@example.com",
  "name": "Active Trader",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Accounts:**
```json
[
  {
    "id": "acct-1",
    "name": "Futures",
    "opening_balance": 25000.00,
    "trade_count": 89,
    "total_pnl": 4200.50
  },
  {
    "id": "acct-2",
    "name": "Crypto",
    "opening_balance": 10000.00,
    "trade_count": 67,
    "total_pnl": -800.25
  }
]
```

**Favorites:**
```json
[
  { "symbol": "ES", "point_value": 50.00, "fees": 5.00 },
  { "symbol": "NQ", "point_value": 20.00, "fees": 5.00 },
  { "symbol": "BTC", "point_value": 1.00, "fees": 0.50 }
]
```

**Recent Trades:**
```json
[
  {
    "symbol": "ES",
    "direction": "long",
    "entry_price": 5200.00,
    "exit_price": 5215.00,
    "position_size": 2,
    "pnl": 1500.00,
    "outcome": "win",
    "trade_date": "2024-03-20"
  },
  {
    "symbol": "NQ",
    "direction": "short",
    "entry_price": 18200.00,
    "exit_price": 18250.00,
    "position_size": 1,
    "pnl": -100.00,
    "outcome": "loss",
    "trade_date": "2024-03-19"
  }
]
```

---

### 8.3 Complex Trade with Partial Exits

**Trade:**
```json
{
  "id": "trade-complex-1",
  "account_id": "acct-1",
  "symbol": "MNQ",
  "direction": "long",
  "entry_price": 18500.00,
  "position_size": 2,
  "stop_loss": 18450.00,
  "take_profit": 18700.00,
  "status": "closed",
  "outcome": "win",
  "pnl": 287.50,
  "notes": "Scaled out at multiple targets",
  "tags": ["scale-out", "nq", "futures"],
  "trade_date": "2024-03-15",
  "partial_exits": [
    {
      "id": "exit-1",
      "qty": 1,
      "exit_price": 18550.00,
      "fees": 2.50,
      "created_at": "2024-03-15T11:30:00Z"
    },
    {
      "id": "exit-2",
      "qty": 0.5,
      "exit_price": 18600.00,
      "fees": 2.50,
      "created_at": "2024-03-15T12:00:00Z"
    }
  ],
  "created_at": "2024-03-15T10:00:00Z",
  "confirmed_at": "2024-03-15T10:00:00Z",
  "exited_at": "2024-03-15T14:00:00Z"
}
```

**P&L Breakdown:**
- Partial Exit 1: (18550 - 18500) × 1 × 2.00 = $100.00
- Partial Exit 2: (18600 - 18500) × 0.5 × 2.00 = $100.00
- Remaining 0.5: (18700 - 18500) × 0.5 × 2.00 = $200.00
- Total Fees: $5.00
- **Final P&L: $395.00 - $5.00 = $390.00**

---

### 8.4 Dashboard Metrics Data

**Full Metrics Response:**
```json
{
  "total_trades": 156,
  "winning_trades": 94,
  "losing_trades": 62,
  "win_rate": 0.6026,
  "total_pnl": 8475.50,
  "avg_pnl_per_trade": 54.33,
  "avg_win": 145.75,
  "avg_loss": -84.25,
  "best_trade": 425.00,
  "worst_trade": -180.50,
  "profit_factor": 1.84,
  "by_symbol": [
    { "symbol": "ES", "count": 45, "pnl": 3200.00 },
    { "symbol": "NQ", "count": 38, "pnl": 2800.50 },
    { "symbol": "MNQ", "count": 28, "pnl": 1200.00 },
    { "symbol": "BTC", "count": 25, "pnl": 800.00 },
    { "symbol": "ETH", "count": 20, "pnl": 475.00 }
  ],
  "by_direction": [
    { "direction": "long", "count": 89, "pnl": 6200.00 },
    { "direction": "short", "count": 67, "pnl": 2275.50 }
  ],
  "recent_pnl": [
    75, -25, 120, 45, -60, 90, 30, -15, 55, 80,
    -40, 110, 25, -30, 85, 50, -20, 95, 40, -35
  ]
}
```

---

## 9. Functional Requirements

### 9.1 Core Features (Must-Have)

| Feature | Priority | Description |
|---------|----------|-------------|
| **Trade CRUD** | P0 | Create, read, update, delete trades |
| **P&L Calculation** | P0 | Automatic profit/loss with point values |
| **Account Management** | P0 | Multiple trading accounts per user |
| **Authentication** | P0 | Secure login/registration |
| **Dashboard Metrics** | P0 | Win rate, profit factor, charts |
| **Trade Filtering** | P0 | Filter by symbol, date, account, direction |
| **Partial Exits** | P0 | Scale out of positions |
| **Favorites** | P0 | Symbol presets with defaults |
| **Dark/Light Mode** | P0 | Theme switching |

### 9.2 Important Features (Should-Have)

| Feature | Priority | Description |
|---------|----------|-------------|
| **Screenshot Upload** | P1 | Attach chart images to trades |
| **Tags** | P1 | Categorize trades |
| **Trade Duration** | P1 | Calculate time in trade |
| **Export Data** | P1 | CSV/Excel export |
| **Bulk Operations** | P1 | Bulk assign trades to accounts |

### 9.3 Nice-to-Have Features

| Feature | Priority | Description |
|---------|----------|-------------|
| **Advanced Charts** | P2 | Drawdown analysis, equity curve |
| **Trade Journal** | P2 | Detailed journaling beyond notes |
| **Import Data** | P2 | Import from broker CSV |
| **Mobile App** | P2 | Native mobile experience |
| **Sharing** | P2 | Share trade reports |

### 9.4 Technical Constraints

| Constraint | Description |
|------------|-------------|
| **Browser Support** | Chrome, Firefox, Safari, Edge (last 2 versions) |
| **Responsive** | Mobile-friendly layouts |
| **Performance** | Page load < 2s, API response < 500ms |
| **Security** | HTTPS only, CSRF protection, XSS prevention |
| **Accessibility** | WCAG 2.1 AA compliance |

---

## 10. Accessibility & UX Requirements

### 10.1 Keyboard Navigation

**Global Shortcuts:**
| Key | Action |
|-----|--------|
| `Tab` | Navigate to next focusable element |
| `Shift + Tab` | Navigate to previous element |
| `Enter` | Activate button or link |
| `Space` | Toggle checkbox or expand section |
| `Escape` | Close modal or dropdown |
| `Ctrl/Cmd + K` | Open command palette (future) |

**Form Navigation:**
- All form inputs must be reachable via Tab
- Logical tab order (top to bottom, left to right)
- Focus visible on all interactive elements

**Modal Navigation:**
- Focus trap inside modal when open
- Return focus to trigger element on close

---

### 10.2 Screen Reader Support

**Required ARIA Labels:**
```html
<!-- Buttons -->
<button aria-label="Add new trade">+</button>

<!-- Navigation -->
<nav aria-label="Main navigation">

<!-- Tables -->
<table aria-label="Trades list">

<!-- Modals -->
<div role="dialog" aria-labelledby="modal-title" aria-modal="true">
  <h2 id="modal-title">Edit Trade</h2>
</div>

<!-- Form errors -->
<input aria-invalid="true" aria-describedby="email-error">
<span id="email-error">Email is required</span>

<!-- Loading states -->
<button aria-busy="true" aria-label="Loading, please wait">
  <span class="spinner"></span>
</button>
```

**Semantic HTML:**
- Use `<button>` for actions, not `<div>`
- Use `<a>` for navigation, not `<span>`
- Use proper heading hierarchy (h1 → h2 → h3)
- Use `<label>` for all form inputs

---

### 10.3 Responsive Breakpoints

| Breakpoint | Width | Description |
|------------|-------|-------------|
| **Mobile** | < 640px | Single column, stacked layout |
| **Tablet** | 640px - 1024px | Two columns where applicable |
| **Desktop** | 1024px - 1440px | Full layout |
| **Large** | > 1440px | Max-width container, centered |

**Mobile Adaptations:**
- Navigation collapses to hamburger menu
- Tables become horizontal scroll or card view
- Modals become full-screen sheets
- Touch targets minimum 44px × 44px

---

### 10.4 Error Handling

**Form Validation:**
- Inline validation on blur
- Clear error messages
- Highlight invalid fields
- Prevent submission until valid

**Error Messages:**
| Scenario | Message | Action |
|----------|---------|--------|
| Network error | "Network error. Please check your connection." | Retry button |
| Validation fail | Field-specific error | Fix field |
| Server error | "Something went wrong. Please try again." | Retry |
| Unauthorized | "Session expired. Please log in again." | Redirect to login |
| Not found | "Trade not found." | Back button |

**Toast Notifications:**
- Success: Auto-dismiss after 3s
- Error: Persistent until dismissed
- Info: Auto-dismiss after 5s
- Warning: Persistent until dismissed

---

### 10.5 Loading States

**Page Loading:**
- Skeleton screens for data tables
- Spinner for dashboard metrics
- Progress indicator for file uploads

**Button Loading:**
```
[Save Trade] → [⏳ Saving...] → [✓ Saved]
```

**Table Loading:**
- Show 5 skeleton rows
- Fade in actual data when loaded

---

### 10.6 Empty States

**No Trades:**
- Icon: Chart or document icon
- Message: "No trades yet. Start journaling your first trade!"
- CTA: "Add Trade" button

**No Accounts:**
- Icon: Wallet icon
- Message: "Create your first trading account to get started."
- CTA: "Add Account" button

**No Favorites:**
- Icon: Star icon
- Message: "Add frequently traded symbols for quick access."
- CTA: "Add Symbol" button

**Filtered Results Empty:**
- Icon: Search icon
- Message: "No trades match your filters."
- CTA: "Clear Filters" button

---

## Document End

---

**For UI Designers:**

This specification provides all functional requirements without prescribing visual design. Use this to understand:
- What data exists and how it relates
- What users need to accomplish
- How the application behaves
- What components are needed

**Design decisions left to designers:**
- Color palettes (except the CSS variables provided)
- Typography sizes and weights
- Spacing and layout grids
- Animation and transitions
- Visual hierarchy and emphasis
- Iconography style
- Button shapes and shadows
- Card styles and elevations

**Questions?** Refer to this document for any functional requirements. For technical implementation details, consult the development team.
