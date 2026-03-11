# Phase 1: Accounts Page - Research

**Researched:** 2026-03-11
**Domain:** React frontend — data fetching, status display, authenticated API integration
**Confidence:** HIGH

## Summary

Phase 1 requires completing the `AccountsPage` component so it fetches social accounts from the backend API and displays them with their status (connected/expired). The backend API is already fully implemented — `GET /api/v1/social_accounts/` returns a list of `SocialAccountResponse` objects scoped to the authenticated user. The frontend routing, layout, and auth infrastructure are all in place; the page stub already exists at `src/client/src/pages/AccountsPage.tsx`.

The work is entirely frontend. The pattern for the page is straightforward: fetch the accounts list on mount using the existing `api.get()` client, derive a "connected/expired" status from `token_expires_at`, and render the list with an empty state. No new backend endpoints, no new routes, no new libraries are needed.

The existing pages (LoginPage, DashboardPage) establish the conventions: functional components, local `useState` for loading/error/data, Tailwind CSS for styling, `api.get<T>()` for authenticated requests. Matching these patterns exactly is the right approach.

**Primary recommendation:** Complete `AccountsPage.tsx` using `useEffect` + `useState` to fetch from `GET /api/v1/social_accounts/`, compute status from `token_expires_at`, and render with Tailwind CSS matching the app's existing style.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React | 19.2.0 | UI rendering | Already in project |
| TypeScript | 5.9.3 | Type safety | Already in project |
| Tailwind CSS | 4.2.1 | Styling | Already in project |
| React Router | 7.13.1 | Navigation (already wired) | Already in project |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `api.ts` (internal) | — | Authenticated fetch wrapper | All API calls in this project |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `useEffect` + `useState` | React Query / SWR | React Query is better at caching/refetch, but the project has no data-fetching library and adding one for a single page is overkill. Match the existing pattern. |

**Installation:** No new packages needed.

## Architecture Patterns

### Recommended Project Structure

No structural changes needed. The file already exists:

```
src/client/src/
├── lib/
│   ├── api.ts            # Existing API client — use api.get<T>()
│   └── auth.ts           # Existing auth helpers
├── pages/
│   └── AccountsPage.tsx  # Target file — currently a stub
└── layouts/
    └── AppLayout.tsx     # Already wraps AccountsPage via <Outlet />
```

A `lib/socialAccounts.ts` module could be added to hold the API call and TypeScript types, following the pattern of `lib/auth.ts`. This keeps the page component thin and types reusable across future phases.

### Pattern 1: Data Fetching with useEffect + useState

**What:** Local state for loading, error, and data; fetch on mount in `useEffect`; display loading/error states before rendering content.

**When to use:** This is the project's established pattern. No shared data-fetching abstraction exists yet.

**Example (matching project conventions):**
```typescript
// src/client/src/pages/AccountsPage.tsx
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

interface SocialAccount {
  id: string;
  platform: string;
  platform_user_id: string;
  token_expires_at: string | null;
}

export default function AccountsPage() {
  const [accounts, setAccounts] = useState<SocialAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get<SocialAccount[]>('/social_accounts/')
      .then(setAccounts)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load accounts'))
      .finally(() => setLoading(false));
  }, []);

  // render...
}
```

### Pattern 2: Status Derivation from token_expires_at

**What:** The API returns `token_expires_at: string | null`. "Connected" means the token either has no expiry or expires in the future. "Expired" means `token_expires_at` is in the past.

**Example:**
```typescript
function getAccountStatus(tokenExpiresAt: string | null): 'connected' | 'expired' {
  if (!tokenExpiresAt) return 'connected'; // No expiry = long-lived token
  return new Date(tokenExpiresAt) > new Date() ? 'connected' : 'expired';
}
```

### Pattern 3: Empty State

**What:** When `accounts.length === 0` (and not loading/error), render a descriptive empty state rather than an empty list.

**Example:**
```tsx
{accounts.length === 0 && (
  <div className="rounded-lg border border-dashed border-gray-300 p-8 text-center text-gray-500">
    <p className="font-medium">No connected accounts</p>
    <p className="mt-1 text-sm">Connect a social media account to start publishing.</p>
  </div>
)}
```

### Anti-Patterns to Avoid

- **Fetching without loading state:** Always show a loading indicator while fetching — the API round-trip can take 200-500ms on localhost.
- **Treating null token_expires_at as expired:** A null expiry means the token is indefinite (Facebook long-lived page tokens often have no expiry). Null = connected.
- **Deriving status on every render without memoization:** For a small list this is fine. Don't add `useMemo` prematurely.
- **Accessing tokens in the component:** Never read `localStorage` directly in a page — use `api.ts` which handles the Authorization header.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Authenticated HTTP requests | Custom fetch wrapper | `api.get<T>()` from `lib/api.ts` | Already handles Bearer token, error parsing, 204 handling |
| Routing | Manual window.location | React Router (already wired) | `/accounts` route already exists in `router.tsx` |
| Navigation | — | `NavLink` in AppLayout (already done) | Sidebar already has an Accounts link |

**Key insight:** The entire infrastructure (routing, API client, auth, layout) is already built and wired. The only missing piece is the page body.

## Common Pitfalls

### Pitfall 1: Empty accounts on first login (correct behavior, not a bug)

**What goes wrong:** Developer sees empty list, thinks fetch is broken. It's working — there are no accounts yet.
**Why it happens:** New test users have zero social accounts.
**How to avoid:** Implement the empty state first; it makes testing easier and confirms the fetch succeeded.
**Warning signs:** `accounts.length === 0` after loading with no error is the happy path for a new user.

### Pitfall 2: Status logic treats null expiry as expired

**What goes wrong:** All Facebook page tokens (which often have no expiry set) show as "expired" even when valid.
**Why it happens:** `!token_expires_at` is falsy, so a naive `new Date(null) < new Date()` check fails.
**How to avoid:** Explicitly check: `if (!tokenExpiresAt) return 'connected'` before comparing dates.
**Warning signs:** All accounts show "Expired" even for freshly-connected accounts.

### Pitfall 3: Race condition on fast unmount

**What goes wrong:** `setAccounts(data)` called after component unmounts (navigating away quickly), causes React "can't perform state update on unmounted component" warning.
**Why it happens:** `useEffect` cleanup is not cancelling the in-flight fetch.
**How to avoid:** Use an `AbortController` in the `useEffect` cleanup, or simply accept the warning (React 18+ handles this gracefully and doesn't cause memory leaks).
**Warning signs:** Console warning about state update on unmounted component.

### Pitfall 4: TypeScript type mismatch with API response

**What goes wrong:** `SocialAccountResponse` from the backend includes `user_id` and `platform_user_id`, but the frontend interface omits fields or uses wrong types.
**Why it happens:** Manually writing the interface without cross-referencing the Pydantic schema.
**How to avoid:** Map the `SocialAccountResponse` Pydantic schema exactly:
```
id: uuid.UUID → string
user_id: uuid.UUID → string (may not be needed in UI)
platform: Platform → 'facebook' | 'instagram' | 'twitter' | 'linkedin'
platform_user_id: str → string
token_expires_at: datetime | None → string | null
```

## Code Examples

Verified patterns from the codebase:

### API Client Usage (from lib/api.ts)
```typescript
// GET with typed response
const accounts = await api.get<SocialAccount[]>('/social_accounts/');
```

### Tailwind Card Pattern (matching LoginPage style)
```tsx
<div className="rounded-lg bg-white p-4 shadow">
  <div className="flex items-center justify-between">
    <div>
      <p className="font-medium capitalize">{account.platform}</p>
      <p className="text-sm text-gray-500">{account.platform_user_id}</p>
    </div>
    <span className={`rounded-full px-2 py-1 text-xs font-medium ${
      status === 'connected'
        ? 'bg-green-100 text-green-700'
        : 'bg-red-100 text-red-700'
    }`}>
      {status === 'connected' ? 'Connected' : 'Expired'}
    </span>
  </div>
</div>
```

### Backend API Contract (from src/smm/api/v1/social_accounts.py)
```
GET /api/v1/social_accounts/
Authorization: Bearer {token}
Response: SocialAccountResponse[]
  - id: UUID
  - user_id: UUID
  - platform: "facebook" | "instagram" | "twitter" | "linkedin"
  - platform_user_id: string
  - token_expires_at: ISO datetime string | null
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Class components with lifecycle methods | Functional components with hooks | React 16.8 (2019) | Use `useEffect` + `useState`, never class components |
| `componentDidMount` fetch | `useEffect(() => {...}, [])` | React 16.8 | Idiomatic pattern for this codebase |
| Manual fetch with headers | `api.get<T>()` wrapper | Already present in this project | Always use the wrapper, never raw `fetch` in pages |

**No deprecated patterns present in this phase.**

## Open Questions

1. **Platform label display**
   - What we know: `platform` value is lowercase (`"facebook"`, `"instagram"`, etc.)
   - What's unclear: Should "facebook" display as "Facebook" or with a logo icon?
   - Recommendation: Use `capitalize` CSS class or `.charAt(0).toUpperCase()`. No platform icons needed for Phase 1 — text is sufficient for ACCT-01/ACCT-05.

2. **Loading skeleton vs spinner**
   - What we know: No loading pattern is established in the app (only `LoginPage` uses a button loading state)
   - What's unclear: Whether to show a spinner, skeleton cards, or just "Loading..." text
   - Recommendation: Simple text ("Loading accounts...") is sufficient for Phase 1. Skeletons are an enhancement.

3. **Token expiry display**
   - What we know: ACCT-05 requires "connected/expired" status, nothing more
   - What's unclear: Whether to show the actual expiry date/time alongside the status badge
   - Recommendation: Show status badge only (connected/expired). Showing expiry timestamp is an enhancement for a future phase.

## Sources

### Primary (HIGH confidence)
- Direct codebase reading: `src/smm/api/v1/social_accounts.py` — confirms `GET /api/v1/social_accounts/` endpoint exists, returns list of accounts scoped to current user
- Direct codebase reading: `src/smm/schemas/social_account.py` — confirms exact response shape including `token_expires_at: datetime | None`
- Direct codebase reading: `src/client/src/lib/api.ts` — confirms `api.get<T>(path)` pattern
- Direct codebase reading: `src/client/src/router.tsx` — confirms `/accounts` route is already registered pointing to `AccountsPage`
- Direct codebase reading: `src/client/src/layouts/AppLayout.tsx` — confirms "Accounts" nav link exists in sidebar
- Direct codebase reading: `src/client/src/pages/AccountsPage.tsx` — confirms stub exists (7 lines), ready to be completed

### Secondary (MEDIUM confidence)
- N/A — all findings verified directly from source files

### Tertiary (LOW confidence)
- N/A

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — verified from package.json and existing code
- Architecture: HIGH — read all relevant files directly
- Pitfalls: MEDIUM — derived from code analysis and React/TypeScript common patterns; not all verified empirically

**Research date:** 2026-03-11
**Valid until:** 2026-06-11 (stable stack, 90 days reasonable)
