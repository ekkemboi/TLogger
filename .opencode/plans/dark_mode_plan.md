# TradeLogger Dark Mode Implementation Plan
# Created: 2026-03-31
# Based on: docs/ui/tradelogger_ui_light.pen (Light Mode Design)

## Overview
Implement dark mode using Tailwind CSS with the light mode design as the main/default theme. The light design from Pencil will become the primary UI, with dark mode as an alternative using Tailwind's `dark:` variant.

## Current State
- Current base.html has hardcoded dark theme colors
- Light design exists in tradelogger_ui_light.pen
- Uses Tailwind CDN with inline config

## Session Structure (6 Sessions)

---

### Session 1: Tailwind CSS Dark Mode Setup
**Goal**: Configure Tailwind for dark mode with CSS variables

**Tasks**:
- [x] 1.1 Analyze light design color variables from .pen file
- [x] 1.2 Update Tailwind config to use CSS variables for both themes
- [x] 1.3 Define CSS custom properties for light mode (bg-primary, bg-secondary, etc.)
- [x] 1.4 Define dark mode color palette mapping
- [x] 1.5 Add darkMode: 'class' strategy in Tailwind config
- [x] 1.6 Create base theme toggle JavaScript

**Files to Modify**:
- web/templates/base.html (Tailwind config section)

**Deliverable**: Working Tailwind dark mode with CSS variables

---

### Session 2: Navigation Component
**Goal**: Implement navigation matching light design

**Tasks**:
- [x] 2.1 Extract navigation structure from .pen (lines 69-334)
- [x] 2.2 Update nav styling: $bg-secondary background, $border-default border
- [x] 2.3 Implement theme toggle button (sun/moon icons)
- [x] 2.4 Style nav links with hover/active states
- [x] 2.5 Add account switcher styling

**Design Specs** (from .pen):
- Nav height: 60px
- Logo: ellipse icon ($accent-primary) + "TRADELOGGER" text
- Nav links gap: 32px
- Active link: $accent-primary background with white text
- Theme toggle: 36x36px, $bg-surface, 8px radius

**Deliverable**: Navigation matching light design with theme toggle

---

### Session 3: Dashboard Metrics Cards
**Goal**: Implement dashboard page with metric cards

**Tasks**:
- [x] 3.1 Extract dashboard structure from .pen (lines 336-1023)
- [x] 3.2 Page header styling (title + subtitle)
- [x] 3.3 Metric cards row 1 (TOTAL P&L, WIN RATE, TOTAL TRADES, PROFIT FACTOR)
- [x] 3.4 Metric cards row 2 (AVG WIN, AVG LOSS, BEST TRADE, WORST TRADE)
- [x] 3.5 Card styling: $bg-surface, 12px radius, $border-default stroke

**Design Specs**:
- Metrics gap: 16px
- Card padding: 24px
- Label: 11px, uppercase, letter-spacing: 1
- Value: 32px (row 1), 28px (row 2)

**Deliverable**: Dashboard metrics matching light design

---

### Session 4: Charts & Stats Sections
**Goal**: Implement charts area and stats section

**Tasks**:
- [x] 4.1 Equity curve chart section (placeholder for Chart.js integration)
- [x] 4.2 P&L bar chart section
- [x] 4.3 Symbol pie chart (donut)
- [x] 4.4 Recent activity list
- [x] 4.5 Apply proper gap, padding, colors from design

**Design Specs**:
- Charts section height: 220px
- Stats section height: 140px
- Pie chart: 120x120px, inner radius 0.6
- Recent trade rows: 8px radius, $bg-primary fill

**Deliverable**: Charts and stats matching light design

---

### Session 5: Trades Page Implementation
**Goal**: Implement trades list page

**Tasks**:
- [x] 5.1 Extract trades page from .pen (lines 1026-1512+)
- [x] 5.2 Stats bar (FILTERED, FILTERED P&L, WIN RATE, AVG P&L)
- [x] 5.3 Filter controls (date range, symbol, etc.)
- [x] 5.4 Trade table with all columns
- [x] 5.5 Pagination component
- [x] 5.6 Apply proper styling throughout

**Design Specs**:
- Table header: 11px uppercase labels
- Row alternation: $bg-surface / $bg-primary
- Direction badges: green for LONG, red for SHORT
- Pagination: 32x32px buttons

**Deliverable**: Fully styled trades page

---

### Session 6: Remaining Pages & Polish
**Goal**: Complete favorites and accounts pages, polish

**Tasks**:
- [x] 6.1 Favorites page styling
- [x] 6.2 Accounts page styling
- [x] 6.3 Responsive design adjustments
- [x] 6.4 Theme persistence (localStorage)
- [x] 6.5 System preference detection (prefers-color-scheme)
- [x] 6.6 Test both light and dark modes

**Deliverable**: Complete implementation with all pages styled

---

## Color Mapping (Light Mode from .pen)

| Variable     | Light Value   | Dark Value (to create) |
|--------------|---------------|------------------------|
| $bg-primary  | #FFFFFF       | #18181B (current)      |
| $bg-secondary| #F4F4F5      | #0F0F10               |
| $bg-surface  | #FAFAFA      | #141415               |
| $text-primary| #18181B      | #FAFAFA               |
| $text-secondary| #71717A    | #71717A (keep)        |
| $accent-primary| #FACC15    | #FACC15 (keep)        |
| $success     | #22C55E      | #22C55E (keep)        |
| $error       | #EF4444      | #EF4444 (keep)        |
| $border-default| #E4E4E7    | #27272A               |

## Technical Approach

### CSS Variables with Tailwind
```css
:root {
  --bg-primary: #FFFFFF;
  --bg-secondary: #F4F4F5;
  --bg-surface: #FAFAFA;
  --text-primary: #18181B;
  --text-secondary: #71717A;
  --accent-primary: #FACC15;
  --accent-primary-hover: #E5B800;
  --success: #22C55E;
  --error: #EF4444;
  --border-default: #E4E4E7;
}

.dark {
  --bg-primary: #18181B;
  --bg-secondary: #0F0F10;
  --bg-surface: #141415;
  --text-primary: #FAFAFA;
  --text-secondary: #71717A;
  --accent-primary: #FACC15;
  --accent-primary-hover: #E5B800;
  --success: #22C55E;
  --error: #EF4444;
  --border-default: #27272A;
}
```

### Tailwind Config
```javascript
tailwind.config = {
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'bg-primary': 'var(--bg-primary)',
        // ... etc
      }
    }
  }
}
```

### Theme Toggle JavaScript
- Check localStorage for saved preference
- Check system preference (prefers-color-scheme)
- Toggle 'dark' class on HTML element
- Save preference to localStorage

---

## Notes
- Light mode is the DEFAULT (based on user request)
- Dark mode via Tailwind dark: variant
- Theme toggle button in nav (sun icon for dark mode, moon for light)
- Persist preference in localStorage
- Consider system preference as fallback

## Dependencies
- Tailwind CSS (via CDN - already in use)
- No additional packages needed
- Chart.js (already in use)

## Blockers
- None identified

---

## Session Continuation Notes

### To resume after any session:
1. Read this file: `.opencode/plans/dark_mode_plan.md`
2. Check current session status
3. Continue from where you left off
4. Update session progress in this file

### Session Progress Tracking
- [x] Session 1: Complete (Tailwind CSS Dark Mode Setup)
- [x] Session 2: Complete (Navigation Component)
- [x] Session 3: Complete (Dashboard Metrics Cards)
- [x] Session 4: Complete (Charts & Stats Sections)
- [x] Session 5: Complete (Trades Page Implementation)
- [x] Session 6: Complete (Remaining Pages & Polish)
