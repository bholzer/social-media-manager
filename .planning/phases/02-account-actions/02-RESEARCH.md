# Phase 2: Account Actions - Research

**Researched:** 2026-03-11
**Domain:** Facebook OAuth flow integration in React + FastAPI; account disconnect UX
**Confidence:** HIGH (all findings verified directly from existing codebase)

## Summary

This phase is almost entirely frontend work. The backend is fully implemented: `GET /api/v1/oauth/facebook/connect` initiates the OAuth redirect, `GET /api/v1/oauth/facebook/callback` exchanges the code and returns either pages or a profile connection, `POST /api/v1/oauth/facebook/connect-page` connects a specific page, and `DELETE /api/v1/social-accounts/{account_id}` disconnects an account. No backend changes are required.

The main frontend challenge is the OAuth redirect-and-return flow. The backend's `/facebook/connect` endpoint issues a `302 RedirectResponse` directly to Facebook — the browser must navigate to this URL (not a `fetch` call). After OAuth completes, Facebook redirects back to the backend callback URL, which processes the code and either connects a profile (no pages case) or returns a JSON payload listing the user's Facebook Pages. The frontend needs a new `/accounts/facebook/callback` route that handles the return from the backend after the callback has been processed and redirects appropriately.

Wait — re-reading the backend carefully: the callback URL Facebook uses is `{base_url}/api/v1/oauth/facebook/callback`. This is a backend endpoint, not a frontend route. After processing, the backend currently returns JSON (either a connection confirmation or a pages list). This means the callback response lands in the backend, not the React client. The planner needs to decide how to close this loop: either (a) the backend redirects to a frontend URL after success/failure, or (b) the client opens a popup window and polls/receives a message.

The current backend does NOT redirect to the frontend after the callback — it returns JSON. This is the key gap to address.

**Primary recommendation:** The simplest approach is to modify the backend callback to redirect to a frontend page (`/accounts/oauth/facebook?pages=...&token=...` or `/accounts/oauth/facebook?success=true`) after processing, or use a dedicated frontend "OAuthCallback" route that the backend redirects to with query params.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React Router v7 | Already installed | New frontend routes for OAuth callback page | Project standard |
| Tailwind CSS 4 | Already installed | Styling consistent with existing pages | Project standard |
| Native fetch (via `api.ts`) | N/A | DELETE call for disconnect | Project standard |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `useSearchParams` (React Router) | Already installed | Read `?pages=...` or `?success=true` query params on callback page | OAuth return URL needs to pass data to frontend |
| `useNavigate` (React Router) | Already installed | Redirect after page selection or success | Already used in LoginPage |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Backend redirect to frontend | Popup window + `postMessage` | Popup approach avoids page navigation but adds complexity; redirect is simpler and consistent with server-side OAuth flows |
| Backend redirect to frontend | Backend returns JSON, frontend polls | Polling requires a session identifier; more complex |

**Installation:** No new packages needed.

## Architecture Patterns

### Recommended Project Structure

New files needed:
```
src/client/src/pages/
└── FacebookOAuthCallbackPage.tsx   # Handles OAuth return, page selection, success/error
```

Modifications needed:
```
src/client/src/router.tsx           # Add route for /accounts/facebook/callback
src/client/src/pages/AccountsPage.tsx  # Add "Connect Facebook" button + disconnect button
src/smm/api/v1/oauth.py             # Modify callback to redirect to frontend (or leave as-is if using popup)
```

### Pattern 1: OAuth Initiation via Navigation

The backend's `/api/v1/oauth/facebook/connect` returns a `302 RedirectResponse` to Facebook. The frontend cannot call this via `fetch` (CORS + redirect won't work as expected). The correct approach is to navigate the browser to the backend URL directly.

**What:** Use `window.location.href = '/api/v1/oauth/facebook/connect'` (not `api.get()`) to initiate the OAuth flow. The browser follows the redirect chain automatically.

**When to use:** Any time a server-side redirect is required for OAuth initiation.

**Example:**
```typescript
// In AccountsPage.tsx - Connect Facebook button handler
function handleConnectFacebook() {
  window.location.href = '/api/v1/oauth/facebook/connect';
}
```

Note: The JWT token cannot be sent as a header when using `window.location.href`. The backend's `/facebook/connect` endpoint uses `get_current_user` (Bearer token dependency). This means the redirect approach will fail authentication — the backend won't have the token.

**Resolution:** The `GET /api/v1/oauth/facebook/connect` endpoint requires an `Authorization: Bearer` header, but browser navigation cannot set custom headers. Options:
1. Change `/facebook/connect` to accept the token as a query parameter (short-lived, not ideal for security)
2. Open the connect URL in a popup window where the React app can set headers via `fetch` and receive a redirect URL back — but this is complex
3. Have the frontend call `api.get('/oauth/facebook/connect')` which will follow the redirect but since fetch doesn't follow cross-origin redirects with CORS, the final redirect to Facebook needs to be returned as a URL for the frontend to navigate to
4. Change the endpoint to return the Facebook authorization URL as JSON (not redirect), and have the frontend navigate to that URL

**Recommended approach:** Change `GET /api/v1/oauth/facebook/connect` to return `{"url": "<facebook-oauth-url>"}` as JSON instead of issuing a 302 redirect. The frontend calls `api.get('/oauth/facebook/connect')`, gets the URL, and navigates to it via `window.location.href`. This is clean, avoids auth header issues, and keeps the JWT flow working.

### Pattern 2: OAuth Callback Return

The Facebook OAuth callback URL is `{base_url}/api/v1/oauth/facebook/callback` (backend endpoint). After processing, the backend currently returns JSON. The React client never sees this response because the full-page navigation went to Facebook and came back to the backend URL.

**Resolution:** Modify the backend callback to redirect to a frontend route after processing:
- Success with pages: `302` to `/accounts/facebook/callback?pages=<encoded>&token=<user_token>`
- Success with profile (no pages): `302` to `/accounts?connected=true`
- Error: `302` to `/accounts?error=<message>`

The frontend route `/accounts/facebook/callback` reads the query params, shows a page-selection UI if pages are present, or handles the success/error states.

### Pattern 3: Page Selection UI

When a user has Facebook Pages, the callback returns a list of pages. The `FacebookOAuthCallbackPage` reads these from query params, displays a selection UI, and calls `POST /api/v1/oauth/facebook/connect-page` with the chosen page.

```typescript
// FacebookOAuthCallbackPage.tsx pattern
const [searchParams] = useSearchParams();
const pagesJson = searchParams.get('pages');
const token = searchParams.get('token');
const pages = pagesJson ? JSON.parse(decodeURIComponent(pagesJson)) : null;

// If no pages param, check for success/error
```

**Security note:** Passing `oauth_user_token` in query params is not ideal for security but acceptable for development; the token is short-lived as a query param value in a redirect flow. For production, the backend should store the token server-side keyed by session ID and return only the session key.

### Pattern 4: Account Disconnect

The `DELETE /api/v1/social-accounts/{account_id}` endpoint already exists and returns 204. The frontend calls `api.delete()` and removes the account from local state.

```typescript
// In AccountsPage.tsx
async function handleDisconnect(accountId: string) {
  await api.delete(`/social-accounts/${accountId}`);
  setAccounts(accounts.filter(a => a.id !== accountId));
}
```

### Anti-Patterns to Avoid

- **Using `api.get()` to call a redirect endpoint:** `fetch` doesn't handle full-page OAuth redirects. Use `window.location.href` after getting the URL.
- **Passing tokens in localStorage across OAuth redirects:** The JWT in localStorage is accessible before and after the OAuth redirect — it doesn't need to be passed explicitly.
- **Calling `api.get('/oauth/facebook/connect')` and expecting it to work:** If the endpoint returns a redirect, `fetch` will follow it but CORS will block the Facebook response. Must get a URL and navigate, not fetch.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| OAuth state parameter | Custom CSRF token | Already in backend (`generate_state()`, `_oauth_states` dict) | Already implemented |
| Token exchange | Custom HTTP calls | Already in `facebook_oauth.py` service | Already implemented |
| Auth header on backend requests | Pass token in URL | Return Facebook URL as JSON, navigate client-side | Keeps JWT in Authorization header |

**Key insight:** The entire OAuth server-side flow already exists. The frontend only needs to initiate navigation and handle the return.

## Common Pitfalls

### Pitfall 1: Authorization Header Not Sent on Browser Navigation

**What goes wrong:** `window.location.href = '/api/v1/oauth/facebook/connect'` navigates the browser but doesn't include the `Authorization: Bearer` header. The backend returns 401.

**Why it happens:** Browser navigation (anchors, location.href, redirects) never sends custom headers. Only `fetch`/`XMLHttpRequest` can send custom headers.

**How to avoid:** Change the `/facebook/connect` endpoint to return a JSON `{"url": "..."}` response. The React client calls it via `api.get()` (which sends the Bearer token), receives the Facebook OAuth URL, and then does `window.location.href = url`.

**Warning signs:** 401 response when clicking "Connect Facebook".

### Pitfall 2: Query Parameter Token Exposure

**What goes wrong:** Passing `oauth_user_token` in the redirect URL query string exposes it in browser history, server logs, and referrer headers.

**Why it happens:** The backend needs to pass the user token back to the frontend for the page-selection step, but the redirect URL is visible.

**How to avoid:** Either (a) accept this risk for v1/development (the token is a Facebook user token, not a platform JWT), or (b) have the backend store the token server-side keyed to a session and pass only the session key. The in-memory `_oauth_states` dict already exists in `oauth.py` — it can be repurposed to store tokens post-callback.

**Warning signs:** Token visible in browser address bar after OAuth return.

### Pitfall 3: React Router Not Handling the Callback URL

**What goes wrong:** The backend redirects to `/accounts/facebook/callback` but this route doesn't exist in `router.tsx`, so the app shows a 404 or falls through to the default route.

**Why it happens:** Forgetting to add the new route to the router.

**How to avoid:** Add the route to `router.tsx` before testing the OAuth flow. The route should be inside the protected `ProtectedRoute` wrapper since the user must be logged in.

**Warning signs:** Blank page or redirect to login after OAuth callback.

### Pitfall 4: Fetch Following Redirects to Facebook

**What goes wrong:** `api.get('/oauth/facebook/connect')` (if endpoint returns 302 to Facebook) tries to follow the redirect, hits CORS issues with Facebook's domain.

**Why it happens:** `fetch` follows redirects by default, but cross-origin redirects may be blocked by CORS.

**How to avoid:** Change the endpoint to return a JSON URL, not a redirect. Frontend gets the URL and navigates.

**Warning signs:** CORS errors in browser console when clicking Connect.

### Pitfall 5: Disconnect Without Confirmation

**What goes wrong:** User accidentally clicks disconnect, account is immediately removed.

**Why it happens:** No confirmation step in the UI.

**How to avoid:** Add a confirmation dialog (window.confirm or inline confirmation state) before calling the delete endpoint. Simple `window.confirm` is acceptable for v1.

## Code Examples

Verified patterns from existing codebase:

### Connect Facebook Button (after endpoint change)
```typescript
// Source: api.ts pattern + oauth.py
async function handleConnectFacebook() {
  try {
    const { url } = await api.get<{ url: string }>('/oauth/facebook/connect');
    window.location.href = url;
  } catch (err) {
    setError(err instanceof Error ? err.message : 'Failed to initiate Facebook connection');
  }
}
```

### Disconnect Account
```typescript
// Source: api.ts delete method, social_accounts.py DELETE endpoint
async function handleDisconnect(accountId: string) {
  if (!window.confirm('Are you sure you want to disconnect this account?')) return;
  try {
    await api.delete(`/social-accounts/${accountId}`);
    setAccounts(prev => prev.filter(a => a.id !== accountId));
  } catch (err) {
    setError(err instanceof Error ? err.message : 'Failed to disconnect account');
  }
}
```

### OAuthCallbackPage reading query params
```typescript
// Source: React Router v7 useSearchParams (existing in project)
import { useSearchParams, useNavigate } from 'react-router';

export default function FacebookOAuthCallbackPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const pagesParam = searchParams.get('pages');
  const token = searchParams.get('token');
  const error = searchParams.get('error');

  // If error, show error and link back to /accounts
  // If no pages param (profile connected), navigate to /accounts?connected=true
  // If pages param, show page selection UI
}
```

### Backend connect endpoint change (minimal)
```python
# In src/smm/api/v1/oauth.py - change return type
@router.get("/facebook/connect")
async def facebook_connect(
    current_user: User = Depends(get_current_user),
):
    """Return Facebook authorization URL."""
    state = generate_state()
    _oauth_states[state] = {
        "user_id": str(current_user.id),
        "created_at": datetime.datetime.now(datetime.UTC),
    }
    url = build_authorize_url(state)
    return {"url": url}  # Changed from RedirectResponse
```

### Backend callback redirect to frontend
```python
# In src/smm/api/v1/oauth.py - callback redirects to frontend
from urllib.parse import urlencode, quote

# In facebook_callback, replace final returns with:
# If pages:
frontend_url = f"/accounts/facebook/callback?pages={quote(pages_json)}&token={quote(long_tokens.access_token)}"
return RedirectResponse(url=frontend_url)

# If profile connected (no pages):
return RedirectResponse(url="/accounts?connected=true")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Backend returns JSON from OAuth callback | Backend redirects to frontend route | This phase | Required for browser-based OAuth flows |
| Backend initiates redirect to Facebook | Backend returns URL, client navigates | This phase | Fixes auth header issue |

## Open Questions

1. **Token in query params security**
   - What we know: Facebook user token passed in redirect URL query param for page selection
   - What's unclear: Whether this is acceptable risk for v1 development
   - Recommendation: Accept for v1; note as tech debt; the token is a Facebook access token, not the app JWT

2. **In-memory OAuth state store**
   - What we know: `_oauth_states` is a plain dict in the oauth.py module (not Redis/DB)
   - What's unclear: Whether this will cause issues in multi-process deployments
   - Recommendation: Fine for v1 single-process development; already documented in code as "For production, use Redis or DB"

3. **Account name/display**
   - What we know: `SocialAccount` model and `SocialAccountResponse` schema store only `platform_user_id` (the Facebook page ID), not a human-readable name. The `AccountsPage` currently displays `platform_user_id` as the account identifier.
   - What's unclear: Whether the plan should add a `display_name` field to the model/schema/response so users see "My Business Page" instead of "1234567890"
   - Recommendation: Adding a `display_name` column to `SocialAccount` and updating the schema would require a migration and backend change. For v1, displaying `platform_user_id` is functional. Planner should decide whether to include this as a task or defer it.

## Sources

### Primary (HIGH confidence)
- `/Users/brennanholzer/projects/personal/social-media-manager/src/smm/api/v1/oauth.py` — Full OAuth endpoint implementation
- `/Users/brennanholzer/projects/personal/social-media-manager/src/smm/api/v1/social_accounts.py` — DELETE endpoint confirmed
- `/Users/brennanholzer/projects/personal/social-media-manager/src/client/src/pages/AccountsPage.tsx` — Phase 1 output
- `/Users/brennanholzer/projects/personal/social-media-manager/src/client/src/lib/api.ts` — api.get/post/delete methods
- `/Users/brennanholzer/projects/personal/social-media-manager/src/client/src/router.tsx` — Route structure
- `/Users/brennanholzer/projects/personal/social-media-manager/src/smm/services/facebook_oauth.py` — OAuth service implementation

### Secondary (MEDIUM confidence)
- Standard OAuth 2.0 browser flow patterns (window.location.href for initiation, redirect for return)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new libraries needed; all tools already in use
- Architecture: HIGH — backend fully read; gaps clearly identified from code inspection
- Pitfalls: HIGH — pitfalls derived from direct code analysis (auth header issue, redirect vs fetch issue)

**Research date:** 2026-03-11
**Valid until:** 2026-04-10 (30 days; stable codebase)
