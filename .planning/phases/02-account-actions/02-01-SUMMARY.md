---
phase: 02-account-actions
plan: 01
subsystem: ui
tags: [facebook, oauth, react, fastapi, tailwind]

# Dependency graph
requires:
  - phase: 01-accounts-page
    provides: AccountsPage, social-accounts API, existing OAuth backend endpoints
provides:
  - End-to-end Facebook OAuth connect flow wired through UI
  - FacebookOAuthCallbackPage for page selection after OAuth return
  - Connect Facebook button on AccountsPage with loading state
  - Backend /facebook/connect returning JSON URL instead of redirect
  - Backend /facebook/callback redirecting to frontend routes with data
affects: [post-creation, publish-pipeline]

# Tech tracking
tech-stack:
  added: []
  patterns: [Frontend-initiated OAuth (fetch URL, then navigate), RedirectResponse to frontend routes with URL-encoded query params]

key-files:
  created:
    - src/client/src/pages/FacebookOAuthCallbackPage.tsx
  modified:
    - src/smm/api/v1/oauth.py
    - src/client/src/pages/AccountsPage.tsx
    - src/client/src/router.tsx

key-decisions:
  - "Backend /facebook/connect returns JSON {url} so frontend can call with Bearer token then navigate"
  - "OAuth callback redirects to /accounts/facebook/callback with URL-encoded JSON pages array and token in query params"
  - "Error cases in callback redirect to /accounts?error=... rather than raising HTTPException (better UX)"

patterns-established:
  - "Frontend-initiated OAuth: api.get() for URL, then window.location.href = data.url"
  - "Backend callback passes data to frontend via URL query params (pages as JSON-encoded string)"

# Metrics
duration: 2min
completed: 2026-03-11
---

# Phase 2 Plan 1: Facebook OAuth Connect Flow Summary

**End-to-end Facebook OAuth wired: backend returns JSON auth URL, callback redirects to frontend page-selection UI, AccountsPage shows success banner after connection.**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-11T15:14:05Z
- **Completed:** 2026-03-11T15:16:24Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Backend `GET /facebook/connect` changed from `RedirectResponse` to `{"url": "..."}` JSON so frontend can call it with Authorization header via `api.get()`
- Backend `GET /facebook/callback` now redirects to `/accounts/facebook/callback?pages=...&token=...` (pages) or `/accounts?connected=true` (no pages), with error redirects to `/accounts?error=...`
- New `FacebookOAuthCallbackPage` reads query params, renders clickable page cards, calls `POST /oauth/facebook/connect-page`, then navigates to `/accounts?connected=true`
- `AccountsPage` gains Connect Facebook button, `?connected=true` success banner, `?error=` error display, and automatic account list refresh on connection

## Task Commits

1. **Task 1: Modify backend OAuth endpoints for frontend integration** - `24200b9` (feat)
2. **Task 2: Create FacebookOAuthCallbackPage and wire Connect button** - `626de13` (feat)

## Files Created/Modified

- `src/smm/api/v1/oauth.py` - /connect returns JSON URL; /callback redirects to frontend routes; added json and urllib.parse.quote imports
- `src/client/src/pages/FacebookOAuthCallbackPage.tsx` - New: handles OAuth return, page selection list, connect-page API call, error display
- `src/client/src/pages/AccountsPage.tsx` - Added Connect Facebook button, handleConnectFacebook handler, query param processing for connected/error, success banner
- `src/client/src/router.tsx` - Added `accounts/facebook/callback` route inside protected AppLayout

## Decisions Made

- **JSON URL response pattern**: Changed `/facebook/connect` to return JSON rather than redirect because the browser cannot forward the Authorization header through a 302 redirect. Frontend fetches the URL then sets `window.location.href`.
- **Frontend callback via query params**: Passed pages data and token through URL query parameters (URL-encoded JSON) rather than session storage or a separate API call, keeping the flow stateless.
- **Error UX**: Replaced `HTTPException` raises in the callback handler body with redirects to `/accounts?error=...` so users see a friendly message rather than a bare API error page.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Facebook OAuth connect flow is fully wired end-to-end
- Users can connect Facebook Pages or personal profiles through the UI
- Connected accounts appear in AccountsPage list immediately after OAuth
- Ready for post creation and publishing functionality

---
*Phase: 02-account-actions*
*Completed: 2026-03-11*
