---
phase: 01-accounts-page
plan: 01
subsystem: ui
tags: [react, typescript, tailwind, social-accounts, api-integration]

# Dependency graph
requires: []
provides:
  - AccountsPage component that fetches and displays connected social accounts
  - Token expiry status derivation (connected vs expired)
  - Empty state UI when no accounts are connected
affects:
  - future phases involving account management or OAuth connection flow

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "useEffect + api.get pattern for data fetching in page components"
    - "Derive display status from API data at render time (not stored)"

key-files:
  created: []
  modified:
    - src/client/src/pages/AccountsPage.tsx

key-decisions:
  - "null token_expires_at treated as connected (long-lived token, not expired)"
  - "Import style @/lib/api matching existing page conventions (RegisterPage)"

patterns-established:
  - "Page-level fetch: useEffect with api.get, three state vars (data/loading/error)"
  - "Status badge: green bg-green-100/text-green-700, red bg-red-100/text-red-700"

# Metrics
duration: 1min
completed: 2026-03-11
---

# Phase 1 Plan 01: Accounts Page Summary

**AccountsPage React component that fetches /api/v1/social_accounts/ and renders per-account connected/expired status badges derived from token_expires_at**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-11T14:44:24Z
- **Completed:** 2026-03-11T14:44:54Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- AccountsPage fetches connected social accounts from backend API on mount
- Status correctly derived: null token = connected, future expiry = connected, past expiry = expired
- Four render states: loading, error, empty (dashed border), and account list
- Each account card shows platform name (capitalized), platform_user_id, and colored status badge

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement AccountsPage with API integration and status display** - `44953eb` (feat)

**Plan metadata:** (committed below)

## Files Created/Modified
- `src/client/src/pages/AccountsPage.tsx` - Complete accounts list page with status display, replacing stub

## Decisions Made
- `null` for `token_expires_at` means a long-lived token that does not expire — treated as connected, not expired
- Used `@/lib/api` import alias (matching RegisterPage.tsx convention, not relative path)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- AccountsPage is ready; users can view connected accounts and their status
- Next: OAuth connection flow UI to allow users to actually connect Facebook accounts
- No blockers

---
*Phase: 01-accounts-page*
*Completed: 2026-03-11*
