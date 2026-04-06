# Testing Plan: Desktop Widget - Session 4
ID: FEA-004
Status: draft
Branch: feature/test-session-4
Created: 2026-04-05
Complexity: medium

## Summary
Test Add Trade with Partial Exits and View All Trades - create missing tests.

## Context
Fourth session in series of testing sessions for TradeLogger user journeys. Session 4 covers Partial Exits (needs E2E, verify unit) and View All Trades (needs E2E).

## Flows Covered

### Flow 1: Add Trade with Partial Exits
- Multiple exit transactions array
- P&L calculation with partial exits

### Flow 2: View All Trades
- Click "VIEW ALL TRADES →" button
- Opens web dashboard in browser

## Requirements
- [ ] Create E2E test for Partial Exits
- [ ] Verify/enhance Partial Exits unit tests
- [ ] Create E2E test for View All Trades
- [ ] Run all tests and verify pass
- [ ] Document test results

## Implementation Plan

### Phase 1: Partial Exits Testing
- Agent: @qa-tester
- Status: ⬜ pending
- Steps:
  - [ ] Analyze partial exits in `desktop/renderer/widget.js`
  - [ ] Create E2E test: Add trade with multiple partial exits
  - [ ] Add to `tests/e2e/test_trades.py`
  - [ ] Verify P&L calculation with partial exits in unit tests
  - [ ] Run tests and verify pass

### Phase 2: View All Trades Testing
- Agent: @qa-tester
- Status: ⬜ pending
- Steps:
  - [ ] Analyze View All button in `desktop/renderer/widget.js`
  - [ ] Create E2E test: Click opens trades page in browser
  - [ ] Add to `tests/e2e/test_widget.py`
  - [ ] Run test and verify pass

### Phase 3: Verification & Summary
- Agent: @devedu
- Status: ⬜ pending
- Steps:
  - [ ] Compile test results
  - [ ] Update session status to complete
  - [ ] Note any issues for follow-up

## Acceptance Criteria
- [ ] Partial Exits E2E test created and passing
- [ ] Partial Exits Unit tests verified
- [ ] View All Trades E2E test created and passing
- [ ] Session 4 marked as complete

## Notes
Reference: `docs/user-journeys.md` - Flows 5 & 7

## Approval
- [ ] User approved
- Approved by:
- Approved at:
