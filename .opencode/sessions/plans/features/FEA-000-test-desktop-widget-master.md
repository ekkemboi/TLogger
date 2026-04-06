# Testing Plan: Desktop Widget User Journeys
ID: FEA-000
Status: draft
Branch: feature/test-desktop-widget
Created: 2026-04-05
Complexity: large

## Summary
Comprehensive testing plan for all 9 Desktop Widget user journeys. Each flow will have E2E and Unit tests verified/created to ensure complete test coverage.

## Context
Based on `docs/user-journeys.md`, we need to test all Desktop Widget user flows. This is the first phase of a larger testing effort that will later cover Web Dashboard flows.

## Testing Strategy
- **Per Flow Order**: E2E test first → Unit test second → Verify pass
- **Session Size**: 2-3 flows per session
- **Priority**: Existing tests first → Missing tests creation

## Session Breakdown

| Session | Flows | Test Focus | Status |
|---------|-------|-------------|--------|
| **1** | Login + Add Trade (Basic) | Existing tests ✅ | ✅ Complete |
| **2** | Window Controls + Screenshot | Verify existing | Ready |
| **3** | Logout + Settings Menu | Create missing | Ready |
| **4** | Partial Exits + View All | Create missing | Ready |
| **5** | Auto-Save + Final Review | Complete gaps | Ready |

## Flows Covered (9 Total)

### Session 1
- [FEA-001] Flow 1: Login Flow
- [FEA-001] Flow 4: Add Trade (Basic)

### Session 2
- [FEA-002] Flow 8: Window Controls
- [FEA-002] Flow 6: Add Trade with Screenshot

### Session 3
- [FEA-003] Flow 2: Logout Flow
- [FEA-003] Flow 3: Settings Menu

### Session 4
- [FEA-004] Flow 5: Add Trade with Partial Exits
- [FEA-004] Flow 7: View All Trades

### Session 5
- [FEA-005] Flow 9: Auto-Save Preferences
- [FEA-005] Final Review

## Requirements
- [x] Complete Session 1 - Login + Add Trade (Basic)
- [ ] Complete Session 2 - Window Controls + Screenshot
- [ ] Complete Session 3 - Logout + Settings Menu
- [ ] Complete Session 4 - Partial Exits + View All
- [ ] Complete Session 5 - Auto-Save + Final Review
- [ ] Update `docs/user-journeys.md` with test results

## Acceptance Criteria
- [ ] All 9 Desktop Widget flows have E2E tests
- [ ] All 9 Desktop Widget flows have Unit tests
- [ ] All tests passing
- [ ] Test coverage documented

## Notes
Reference: `docs/user-journeys.md`

## Approval
- [ ] User approved
- Approved by:
- Approved at:
