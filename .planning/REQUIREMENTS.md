# Requirements: Social Media Manager — Account Connection

**Defined:** 2026-03-11
**Core Value:** Users can connect their Facebook account through the UI so they can publish posts to it

## v1 Requirements

### Account Management

- [ ] **ACCT-01**: User can view a list of their connected social accounts on the accounts page
- [ ] **ACCT-02**: User can initiate Facebook OAuth flow from the accounts page
- [ ] **ACCT-03**: User sees the new Facebook account appear after completing OAuth
- [ ] **ACCT-04**: User can remove/disconnect a connected social account
- [ ] **ACCT-05**: User can see the status (connected/expired) of each connected account

## v2 Requirements

### Multi-Platform

- **PLAT-01**: User can connect Instagram account (via Facebook Business OAuth)
- **PLAT-02**: User can connect Twitter account
- **PLAT-03**: User can connect LinkedIn account

### Account Health

- **HLTH-01**: User receives notification when account token expires
- **HLTH-02**: User can re-authenticate an expired account

## Out of Scope

| Feature | Reason |
|---------|--------|
| Instagram/Twitter/LinkedIn connection | No backend OAuth for Twitter/LinkedIn; Instagram deferred to v2 |
| Token auto-refresh | Future enhancement, manual re-auth sufficient for v1 |
| Account analytics/insights | Not related to connection feature |
| Bulk account management | Single-user app, not needed |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| ACCT-01 | Phase 1 | Pending |
| ACCT-02 | Phase 2 | Pending |
| ACCT-03 | Phase 2 | Pending |
| ACCT-04 | Phase 2 | Pending |
| ACCT-05 | Phase 1 | Pending |

**Coverage:**
- v1 requirements: 5 total
- Mapped to phases: 5
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-11*
*Last updated: 2026-03-11 after roadmap creation*
