---
phase: 01-accounts-page
verified: 2026-03-11T14:46:34Z
status: gaps_found
score: 4/5 must-haves verified
gaps:
  - truth: "User can navigate to the accounts page and see a list of their connected social accounts"
    status: failed
    reason: "AccountsPage calls /api/v1/social_accounts/ (underscore) but the backend router is mounted at /api/v1/social-accounts (hyphen). The API call will 404 at runtime, so the accounts list can never load."
    artifacts:
      - path: "src/client/src/pages/AccountsPage.tsx"
        issue: "Line 28: api.get<SocialAccount[]>('/social_accounts/') uses underscore path"
      - path: "src/smm/main.py"
        issue: "Line 25: router mounted at prefix='/api/v1/social-accounts' (hyphen)"
    missing:
      - "Align the path — either change AccountsPage.tsx to call '/social-accounts/' or change main.py prefix to '/api/v1/social_accounts'"
---

# Phase 1: Accounts Page Verification Report

**Phase Goal:** Users can see their connected social accounts and their status on a dedicated page
**Verified:** 2026-03-11T14:46:34Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #   | Truth                                                                                        | Status     | Evidence                                                                                                        |
| --- | -------------------------------------------------------------------------------------------- | ---------- | --------------------------------------------------------------------------------------------------------------- |
| 1   | User can navigate to the accounts page and see a list of their connected social accounts     | FAILED     | Component calls `/social_accounts/` (underscore) but backend is mounted at `/social-accounts` (hyphen); 404 at runtime |
| 2   | Each connected account displays its platform name and connection status (connected/expired)  | VERIFIED   | Account cards render `account.platform` (capitalized) and status badge derived from `getAccountStatus`          |
| 3   | When no accounts are connected, the page shows an empty state message                        | VERIFIED   | `accounts.length === 0` branch renders dashed-border box with "No connected accounts" heading                   |
| 4   | An account with null or future token_expires_at shows as Connected                           | VERIFIED   | `getAccountStatus`: null → 'connected'; `new Date(tokenExpiresAt) > new Date()` → 'connected'                   |
| 5   | An account with past token_expires_at shows as Expired                                       | VERIFIED   | `getAccountStatus` falls through to return 'expired' when date is in the past                                   |

**Score:** 4/5 truths verified (truth 1 fails due to URL mismatch blocking the fetch)

### Required Artifacts

| Artifact                                      | Expected                            | Status    | Details                                             |
| --------------------------------------------- | ----------------------------------- | --------- | --------------------------------------------------- |
| `src/client/src/pages/AccountsPage.tsx`       | Accounts list with status display   | VERIFIED  | 93 lines, substantive, exported default, no stubs   |
| `src/smm/api/v1/social_accounts.py`           | GET /social_accounts/ endpoint      | VERIFIED  | `list_social_accounts` queries DB, returns accounts |
| `src/client/src/router.tsx`                   | Route for /accounts                 | VERIFIED  | `{ path: 'accounts', element: <AccountsPage /> }`   |
| `src/client/src/layouts/AppLayout.tsx`        | Nav link to /accounts               | VERIFIED  | `{ to: '/accounts', label: 'Accounts' }` in navItems|

### Key Link Verification

| From                            | To                          | Via                     | Status      | Details                                                                                      |
| ------------------------------- | --------------------------- | ----------------------- | ----------- | -------------------------------------------------------------------------------------------- |
| `AccountsPage.tsx`              | `/api/v1/social_accounts/`  | `api.get` in useEffect  | NOT_WIRED   | Frontend uses `/social_accounts/` (underscore); backend prefix is `/social-accounts` (hyphen)|
| `router.tsx`                    | `AccountsPage`              | import + route element  | WIRED       | Imported and assigned to path 'accounts' under ProtectedRoute                                |
| `AppLayout.tsx`                 | `/accounts`                 | NavLink                 | WIRED       | Nav item renders NavLink to '/accounts'                                                      |
| `social_accounts.py` (backend)  | database                    | SQLAlchemy select       | WIRED       | `session.execute(select(SocialAccount).where(...))` result returned directly                 |

### Requirements Coverage

| Requirement | Status  | Blocking Issue                                                              |
| ----------- | ------- | --------------------------------------------------------------------------- |
| ACCT-01     | BLOCKED | URL mismatch causes 404; accounts list never loads from API                 |
| ACCT-05     | BLOCKED | Status badge logic is correct in code but unreachable without ACCT-01 data  |

### Anti-Patterns Found

| File                                  | Line | Pattern      | Severity | Impact                          |
| ------------------------------------- | ---- | ------------ | -------- | ------------------------------- |
| `src/client/src/pages/AccountsPage.tsx` | 28 | Wrong API path | Blocker  | All API calls 404 at runtime   |

### Gaps Summary

There is one gap blocking the phase goal. The AccountsPage component is fully implemented — it has substantive logic, correct status derivation, all four render states (loading, error, empty, list), and is properly wired into the router and navigation.

However, the API call on line 28 uses `/social_accounts/` with an underscore, while the backend router in `src/smm/main.py` mounts the same resource at the prefix `/api/v1/social-accounts` with a hyphen. At runtime every fetch returns a 404, the error state fires, and no accounts are ever displayed. The fix is a one-line change: either update AccountsPage.tsx line 28 to `/social-accounts/`, or update main.py line 25 to use `/api/v1/social_accounts`.

---

_Verified: 2026-03-11T14:46:34Z_
_Verifier: Claude (gsd-verifier)_
