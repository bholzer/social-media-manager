---
phase: 02-account-actions
plan: 02
subsystem: ui
tags: [react, tailwind, social-accounts, delete, confirmation]

# Dependency graph
requires:
  - phase: 02-account-actions/02-01
    provides: AccountsPage with connected accounts list and Connect Facebook button
provides:
  - Disconnect button on each connected account in AccountsPage
  - Browser confirmation dialog before disconnecting
  - Optimistic account removal from UI state after DELETE API call
  - Error display to user on failed disconnect
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns: [window.confirm for simple destructive action confirmation, optimistic state removal via setAccounts filter]

key-files:
  created: []
  modified:
    - src/client/src/pages/AccountsPage.tsx

key-decisions:
  - "Use window.confirm instead of custom modal (sufficient for v1, no added complexity)"
  - "Optimistic removal: remove from state immediately on successful DELETE response (no re-fetch needed)"

patterns-established:
  - "Destructive action pattern: window.confirm → api.delete → filter state → catch error to setError"

# Metrics
duration: 1min
completed: 2026-03-11
---

# Phase 2 Plan 2: Disconnect Account Summary

**Disconnect button with window.confirm dialog added to each account row; DELETE /social-accounts/{id} called on confirmation with optimistic state removal.**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-11T15:18:21Z
- **Completed:** 2026-03-11T15:19:30Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Added `handleDisconnect(accountId)` that shows a browser confirmation dialog before calling `DELETE /api/v1/social-accounts/{id}`
- Removes the account from local React state immediately on successful delete (no page reload)
- Shows error message to user if the DELETE call fails
- Disconnect button styled as subtle text link (`text-red-600 hover:text-red-800 hover:underline`) to avoid visual clutter alongside the status badge
- Status badge and Disconnect button wrapped in a flex container with gap for clean alignment

## Task Commits

1. **Task 1: Add disconnect button with confirmation to AccountsPage** - `4f2097e` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `src/client/src/pages/AccountsPage.tsx` - Added handleDisconnect function, Disconnect button in flex container next to status badge

## Decisions Made

- **window.confirm over custom modal**: V1 simplicity; avoids adding modal state, portal, or dialog component for a single destructive action.
- **Optimistic removal**: Filter account from state after a successful DELETE response rather than re-fetching the list, giving instant feedback.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Account management is feature-complete: users can connect Facebook accounts and disconnect any account
- No known blockers for post creation or publishing phases
- AccountsPage is stable and requires no further changes for current scope

---
*Phase: 02-account-actions*
*Completed: 2026-03-11*
