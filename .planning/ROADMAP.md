# Roadmap: Social Media Manager — Account Connection

## Overview

This milestone adds Facebook account connection to the existing React client. The backend OAuth flow and social account endpoints already exist; the work is entirely UI: an accounts page that lists connected accounts with their status, initiates the Facebook OAuth redirect, handles the OAuth callback, and allows disconnecting accounts.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Accounts Page** - Users can view their connected social accounts and their status
- [x] **Phase 2: Account Actions** - Users can connect Facebook and disconnect accounts

## Phase Details

### Phase 1: Accounts Page
**Goal**: Users can see their connected social accounts and their status on a dedicated page
**Depends on**: Nothing (first phase)
**Requirements**: ACCT-01, ACCT-05
**Success Criteria** (what must be TRUE):
  1. User can navigate to the accounts page from within the app
  2. User sees a list of their connected social accounts on the accounts page
  3. Each connected account displays its platform and connection status (connected/expired)
  4. When no accounts are connected, the page shows an appropriate empty state
**Plans**: TBD

Plans:
- [x] 01-01: Build accounts page with API integration and status display

### Phase 2: Account Actions
**Goal**: Users can connect their Facebook account via OAuth and disconnect accounts they no longer want
**Depends on**: Phase 1
**Requirements**: ACCT-02, ACCT-03, ACCT-04
**Success Criteria** (what must be TRUE):
  1. User can click a "Connect Facebook" button on the accounts page and be redirected to Facebook OAuth
  2. After completing Facebook OAuth, the user is returned to the accounts page and sees the new account in their list
  3. User can remove a connected account and it disappears from the list
**Plans**: TBD

Plans:
- [x] 02-01: Facebook OAuth initiation and callback handling
- [x] 02-02: Account disconnect action

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Accounts Page | 1/1 | Complete ✓ | 2026-03-11 |
| 2. Account Actions | 2/2 | Complete ✓ | 2026-03-11 |
