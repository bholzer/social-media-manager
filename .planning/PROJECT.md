# Social Media Manager — Account Connection

## What This Is

A social media management app that lets users schedule and publish posts to multiple social platforms. The backend (FastAPI + SQLAlchemy + Dramatiq) and React client already exist with authentication, post creation/scheduling, and a Facebook/Instagram publishing pipeline. This milestone adds the ability for users to connect their Facebook accounts from the UI.

## Core Value

Users can connect their Facebook account through the UI so they can publish posts to it.

## Requirements

### Validated

- ✓ User registration and JWT authentication — existing
- ✓ Post creation with multi-target scheduling — existing
- ✓ Facebook OAuth backend flow (code exchange, long-lived tokens, page tokens) — existing
- ✓ Scheduled post publishing via APScheduler + Dramatiq pipeline — existing
- ✓ Platform adapter pattern (Facebook, Instagram) — existing
- ✓ React client with auth pages, routing, Tailwind CSS — existing

### Active

- [ ] User can view their connected social accounts on the accounts page
- [ ] User can initiate Facebook OAuth from the accounts page
- [ ] User can complete Facebook OAuth and see the new account appear
- [ ] User can disconnect/remove a connected social account

### Out of Scope

- Instagram account connection — deferred, shares Facebook OAuth but needs additional UI/logic
- Twitter OAuth — no backend implementation yet
- LinkedIn OAuth — no backend implementation yet
- Account token refresh/re-authentication — future enhancement
- Account health monitoring — future enhancement

## Context

- Backend already has `/api/v1/oauth/facebook/*` endpoints for OAuth code exchange and token storage
- Backend has `/api/v1/social-accounts` endpoints for listing/managing accounts
- SocialAccount model supports Facebook, Instagram, Twitter, LinkedIn via Platform enum
- React client uses React Router v7, Tailwind CSS 4, and stores JWT in localStorage
- Client has an auth utility at `src/client/src/lib/auth.ts` for API calls
- No state management library — React local state only

## Constraints

- **Tech stack**: Must use existing FastAPI backend and React/Vite/Tailwind frontend
- **Auth**: Facebook OAuth flow already implemented on backend — UI must integrate with existing endpoints
- **Platform**: Facebook only for this milestone

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Facebook only for v1 account connection | Backend OAuth already exists; other platforms need new backend work | — Pending |
| Use existing backend OAuth endpoints | No backend changes needed if endpoints are sufficient | — Pending |

---
*Last updated: 2026-03-11 after initialization*
