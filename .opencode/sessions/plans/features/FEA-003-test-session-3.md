# Testing Plan: Desktop Widget - Session 3
ID: FEA-003
Status: draft
Branch: feature/test-session-3
Created: 2026-04-05
Complexity: medium

## Summary
Test Logout Flow and Settings Menu - create missing tests.

## Context
Third session in series of testing sessions for TradeLogger user journeys. Session 3 covers two flows with NO existing tests - Logout and Settings Menu.

## Flows Covered

### Flow 1: Logout Flow
- Clear stored tokens from main process
- UI switches to Login View

### Flow 2: Settings Menu
- Always on Top toggle (Electron API)
- Dark Mode toggle (localStorage)

## Requirements
- [ ] Create E2E test for Logout Flow
- [ ] Create Unit test for Theme toggle
- [ ] Create Unit test for Always on Top
- [ ] Run all new tests and verify pass
- [ ] Document test results

## Implementation Plan

### Phase 1: Logout Flow - Test Creation
- Agent: @qa-tester
- Status: ⬜ pending
- Steps:
  - [ ] Analyze logout flow in `desktop/renderer/auth.js`
  - [ ] Create E2E test: logout clears tokens, shows login view
  - [ ] Add to `tests/e2e/test_widget.py`
  - [ ] Run test and verify pass

### Phase 2: Settings Menu - Test Creation
- Agent: @qa-tester
- Status: ⬜ pending
- Steps:
  - [ ] Analyze settings in `desktop/renderer/widget.js`
  - [ ] Create Unit test: Theme toggle updates body dataset
  - [ ] Create Unit test: Always on top persists to localStorage
  - [ ] Add to `tests/test_settings.py` (new file)
  - [ ] Run tests and verify pass

### Phase 3: Verification & Summary
- Agent: @devedu
- Status: ⬜ pending
- Steps:
  - [ ] Compile test results
  - [ ] Update session status to complete
  - [ ] Note any issues for follow-up

## Acceptance Criteria
- [ ] Logout E2E test created and passing
- [ ] Settings Theme Unit test created and passing
- [ ] Settings Always on Top Unit test created and passing
- [ ] Session 3 marked as complete

## Notes
Reference: `docs/user-journeys.md` - Flows 2 & 3

## Approval
- [ ] User approved
- Approved by:
- Approved at:
