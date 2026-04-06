# Testing Plan: Desktop Widget - Session 1
ID: FEA-001
Status: draft
Branch: feature/test-session-1
Created: 2026-04-05
Complexity: small

## Summary
Test Login Flow and Add Trade (Basic) - verify existing tests pass.

## Context
First session in series of testing sessions for TradeLogger user journeys. This session covers the two foundational flows that already have test coverage.

## Flows Covered

### Flow 1: Login Flow
- Desktop widget login via browser OAuth
- Token storage and auto-refresh

### Flow 2: Add Trade (Basic)
- Form fill with all basic fields
- Price validation logic
- API create trade

## Requirements
- [ ] Run existing E2E tests for Login Flow
- [ ] Run existing Unit tests for Login Flow
- [ ] Run existing E2E tests for Add Trade (Basic)
- [ ] Run existing Unit tests for Add Trade (Basic)
- [ ] Fix any failing tests
- [ ] Document test results

## Implementation Plan

### Phase 1: Login Flow Testing
- Agent: @qa-tester
- Status: ⬜ pending
- Steps:
  - [ ] Run `tests/e2e/test_widget.py` - Login tests
  - [ ] Run `tests/test_auth.py` - Token validation tests
  - [ ] Verify all pass
  - [ ] Document results

### Phase 2: Add Trade (Basic) Testing
- Agent: @qa-tester
- Status: ⬜ pending
- Steps:
  - [ ] Run `tests/e2e/test_trades.py` - Add trade E2E
  - [ ] Run `tests/test_price_validation.py` - Validation unit tests
  - [ ] Run `tests/test_trades.py::test_create_trade_success`
  - [ ] Verify all pass
  - [ ] Document results

### Phase 3: Verification & Summary
- Agent: @devedu
- Status: ⬜ pending
- Steps:
  - [ ] Compile test results
  - [ ] Update session status to complete
  - [ ] Note any issues for follow-up

## Acceptance Criteria
- [ ] Login Flow E2E tests pass
- [ ] Login Flow Unit tests pass
- [ ] Add Trade (Basic) E2E tests pass
- [ ] Add Trade (Basic) Unit tests pass
- [ ] Session 1 marked as complete

## Notes
Reference: `docs/user-journeys.md` - Flows 1 & 4

## Approval
- [ ] User approved
- Approved by:
- Approved at:
