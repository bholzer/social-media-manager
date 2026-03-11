---
phase: 02-account-actions
verified: 2026-03-11T15:20:44Z
status: gaps_found
score: 2/3 must-haves verified
gaps:
  - truth: "User can click Connect Facebook and be redirected to Facebook OAuth"
    status: partial
    reason: "OAuth initiation works end-to-end, but invalid/expired state errors in /facebook/callback raise HTTPException (bare API error page) instead of redirecting to /accounts?error=... — users who arrive with a tampered or timed-out state token see a raw JSON error rather than the accounts page error banner"
    artifacts:
      - path: "src/smm/api/v1/oauth.py"
        issue: "Lines 74-85: state validation failures raise HTTPException(400) instead of returning RedirectResponse to /accounts?error=..."
    missing:
      - "Replace the two HTTPException raises at lines 74-77 and 82-85 of oauth.py with RedirectResponse(url=f'/accounts?error={quote(message)}') to match the pattern used for all other error paths"
---

# Phase 2: Account Actions Verification Report

**Phase Goal:** Users can connect their Facebook account via OAuth and disconnect accounts they no longer want
**Verified:** 2026-03-11T15:20:44Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | User can click "Connect Facebook" and be redirected to Facebook OAuth | PARTIAL | Button exists, handler calls `api.get('/oauth/facebook/connect')` and sets `window.location.href`; backend `/facebook/connect` returns JSON `{url}`; however `/facebook/callback` raises `HTTPException` for invalid/expired state instead of redirecting to the frontend error banner |
| 2 | After OAuth, user returns to accounts page and sees the new account | VERIFIED | `/facebook/callback` redirects to `/accounts/facebook/callback?pages=...` (pages flow) or `/accounts?connected=true` (profile flow); `FacebookOAuthCallbackPage` calls `POST /oauth/facebook/connect-page`, then navigates to `/accounts?connected=true`; `AccountsPage` re-fetches account list on `connected=true` param |
| 3 | User can remove a connected account and it disappears from the list | VERIFIED | `handleDisconnect` calls `api.delete('/social-accounts/{id}')`; backend `DELETE /api/v1/social-accounts/{account_id}` returns 204; `api.delete` handles 204 correctly; state is filtered on success |

**Score:** 2/3 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/smm/api/v1/oauth.py` | `/connect` returns JSON URL; `/callback` redirects to frontend routes | PARTIAL | 192 lines, substantive. `/connect` (lines 47-58) returns `{"url": url}` — correct. `/callback` (lines 61-134) redirects to frontend for token/page errors, but raises `HTTPException(400)` for invalid state (lines 74-77) and expired state (lines 82-85) instead of redirecting. |
| `src/client/src/pages/AccountsPage.tsx` | Connect Facebook button, Disconnect button, query param handling | VERIFIED | 167 lines. Button at line 96-103 calls `handleConnectFacebook` (lines 77-87). `handleDisconnect` (lines 65-75) calls `api.delete`. Query param processing at lines 51-63 handles `connected=true` and `error=`. Both handlers fully wired. |
| `src/client/src/pages/FacebookOAuthCallbackPage.tsx` | Reads query params, shows page cards, calls connect-page API | VERIFIED | 130 lines. Reads `pages`, `token`, `error` params. Renders page cards at lines 92-110. `handleSelectPage` (lines 61-75) calls `api.post('/oauth/facebook/connect-page', ...)` and navigates to `/accounts?connected=true`. Error state rendered at lines 22-37. |
| `src/client/src/router.tsx` | `/accounts/facebook/callback` route inside protected layout | VERIFIED | Line 53: `{ path: 'accounts/facebook/callback', element: <FacebookOAuthCallbackPage /> }` inside the ProtectedRoute/AppLayout child routes. `FacebookOAuthCallbackPage` imported at line 9. |
| `src/client/src/lib/api.ts` | `api.delete()` method exists | VERIFIED | Lines 63-65: `delete: <T>(path: string) => request<T>(path, { method: 'DELETE' })`. 204 handled at lines 41-43 returning `undefined`. |
| `src/smm/api/v1/social_accounts.py` | `DELETE /{account_id}` endpoint scoped to current user | VERIFIED | Lines 68-86: `@router.delete("/{account_id}", status_code=204)`, queries with `SocialAccount.user_id == current_user.id`, deletes and commits. |
| `src/smm/main.py` | oauth router mounted at `/api/v1/oauth` | VERIFIED | Line 28: `app.include_router(oauth.router, prefix="/api/v1/oauth", tags=["oauth"])`. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `AccountsPage.tsx` | `GET /api/v1/oauth/facebook/connect` | `api.get('/oauth/facebook/connect')` in `handleConnectFacebook` | WIRED | Line 81; response `.url` used at line 82 |
| `AccountsPage.tsx` | `DELETE /api/v1/social-accounts/{id}` | `api.delete('/social-accounts/${accountId}')` in `handleDisconnect` | WIRED | Line 70; state filtered on success at line 71 |
| `FacebookOAuthCallbackPage.tsx` | `POST /api/v1/oauth/facebook/connect-page` | `api.post('/oauth/facebook/connect-page', ...)` in `handleSelectPage` | WIRED | Line 65; navigates to `/accounts?connected=true` on success at line 70 |
| `AccountsPage.tsx` | account list refresh | `fetchAccounts()` called when `connected=true` param present | WIRED | Line 57 |
| `/facebook/callback` (backend) | `/accounts?connected=true` | `RedirectResponse` | WIRED | Line 125 (personal profile path) |
| `/facebook/callback` (backend) | `/accounts/facebook/callback?pages=...` | `RedirectResponse` | WIRED | Lines 129-134 |
| `/facebook/callback` (backend) | `/accounts?error=...` | `RedirectResponse` | PARTIAL | Used for token/page errors (lines 97, 104, 112) but NOT for invalid/expired state (lines 74-85 raise `HTTPException` instead) |

### Requirements Coverage

| Requirement | Status | Blocking Issue |
|-------------|--------|----------------|
| ACCT-02: Initiate Facebook OAuth from accounts page | PARTIAL | Button and `/connect` endpoint wired correctly; `/callback` state validation errors produce bare API errors instead of user-facing messages |
| ACCT-03: New account appears after OAuth | SATISFIED | Both personal profile path and page selection path converge on `/accounts?connected=true` which triggers list re-fetch |
| ACCT-04: Remove/disconnect a connected account | SATISFIED | Full chain verified: Disconnect button → `api.delete` → `DELETE /social-accounts/{id}` → 204 → state filter |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/smm/api/v1/oauth.py` | 74-77 | `raise HTTPException(400, "Invalid or expired OAuth state")` in a callback handler that is otherwise a frontend redirect flow | Warning | User sees raw JSON `{"detail": "..."}` instead of the `/accounts?error=` banner when state is invalid or tampered |
| `src/smm/api/v1/oauth.py` | 82-85 | `raise HTTPException(400, "OAuth state expired")` — same as above | Warning | Same as above |

No TODO/FIXME/placeholder patterns found in any modified file. No empty handlers or stub returns.

### Human Verification Required

These items cannot be verified from static analysis alone:

#### 1. Full OAuth round-trip

**Test:** Log in, click "Connect Facebook," complete OAuth on Facebook, select a page if prompted, land back on the accounts page.
**Expected:** Success banner "Facebook account connected successfully!" shown, new account row visible in the list.
**Why human:** Requires live Facebook OAuth credentials and a running backend.

#### 2. Disconnect flow UX

**Test:** Click "Disconnect" on an existing account row, confirm the browser dialog.
**Expected:** Account row disappears immediately without a page reload.
**Why human:** Browser `window.confirm` behavior and DOM mutation must be verified visually.

#### 3. Error banner on OAuth failure

**Test:** Simulate an OAuth error (e.g., deny Facebook permissions), observe the accounts page.
**Expected:** Red error message visible on the accounts page, not a bare API error screen.
**Why human:** Depends on live OAuth flow; the state-validation gap noted above makes this a real risk.

### Gaps Summary

One gap blocks full goal achievement: the `/facebook/callback` endpoint raises bare `HTTPException(400)` responses for invalid/expired OAuth state tokens instead of redirecting to `/accounts?error=...`. Every other error path in the same function correctly redirects to the frontend. This inconsistency means users who encounter a stale state (e.g., waited too long, double-clicked, or had the state tampered) will see a raw JSON error page rather than the error banner in `AccountsPage`. The fix is a two-line change in `src/smm/api/v1/oauth.py`.

All other required pieces are fully implemented, substantive, and correctly wired: the Connect Facebook button, the `FacebookOAuthCallbackPage` page-selection UI, the account list refresh after connection, the Disconnect button, the `DELETE` endpoint, and the `api.delete()` method.

---
_Verified: 2026-03-11T15:20:44Z_
_Verifier: Claude (gsd-verifier)_
