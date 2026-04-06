# Testing Plan: Desktop Widget - Session 2
ID: FEA-002
Status: draft
Branch: feature/test-session-2
Created: 2026-04-05
Complexity: small

## Summary
Test Window Controls and Add Trade with Screenshot - verify existing tests, create missing unit tests.

## Context
Second session in series of testing sessions for TradeLogger user journeys. Session 2 covers Window Controls (existing E2E) and Screenshot upload (existing unit, verify E2E).

## Flows Covered

### Flow 1: Window Controls
- Float toggle (collapse/expand)
- Minimize to taskbar
- Close with confirmation

### Flow 2: Add Trade with Screenshot
- File upload with trade
- Screenshot storage and retrieval

## Requirements
- [ ] Run existing E2E tests for Window Controls
- [ ] Verify Screenshot E2E test exists and passes
- [ ] Run existing Unit tests for Screenshot
- [ ] Fix any failing tests
- [ ] Document test results

## Implementation Plan

### Phase 1: Window Controls Testing
- Agent: @qa-tester
- Status: ⬜ pending
- Steps:
  - [ ] Run `tests/e2e/agent-browser/test_widget_electron.py` - Float toggle
  - [ ] Verify window resize works correctly
  - [ ] Document results

### Phase 2: Screenshot Upload Testing
- Agent: @qa-tester
- Status: ⬜ pending
- Steps:
  - [ ] Check for existing E2E screenshot test
  - [ ] Run existing unit test: `tests/test_fix_screenshot.py`
  - [ ] Verify screenshot upload works
  - [ ] Document results

### Phase 3: Verification & Summary
- Agent: @devedu
- Status: ⬜ pending
- Steps:
  - [ ] Compile test results
  - [ ] Update session status to complete
  - [ ] Note any issues for follow-up

## Acceptance Criteria
- [ ] Window Controls E2E tests pass
- [ ] Screenshot E2E test verified/created
- [ ] Screenshot Unit tests pass
- [ ] Session 2 marked as complete

## Notes
Reference: `docs/user-journeys.md` - Flows 6 & 8

## Approval
- [ ] User approved
- Approved by:
- Approved at:
