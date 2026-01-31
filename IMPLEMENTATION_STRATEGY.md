# TMS Dashboard Enhancement - Implementation Strategy

**Date:** January 10, 2026  
**Baseline Commit:** 28efac5  
**Status:** Ready for Implementation

---

## Overview

This document outlines the implementation strategy for the four major enhancements to the TMS Dashboard:

1. **Authentication & Access Control** (Feature Branch: `feature/auth`)
2. **Audit & Action Tracking** (Feature Branch: `feature/audit`)
3. **UI Enhancements – Action Visibility** (Feature Branch: `feature/ui-enhancements`)
4. **Performance Load Testing** (Feature Branch: `feature/load-testing`)

All changes are tracked in git with feature branches for safe reversion.

---

## Git Branching Strategy

```
master (production)
├── feature/auth (authentication & session management)
├── feature/audit (audit trail and logging)
├── feature/ui-enhancements (clickable customer IDs, action history)
├── feature/load-testing (performance benchmarks)
└── develop (integration branch - merge all features here first)
```

### Reversion Strategy

Each feature branch can be independently reverted:

```bash
# Revert a specific feature
git revert <feature-branch-commit>

# Or merge back to master and revert the merge commit
git revert -m 1 <merge-commit-hash>

# Return to baseline (if needed)
git reset --hard 28efac5
```

---

## Phase 1: Authentication & Access Control

### Objective
- Implement login page with 5 predefined user credentials
- Session management for authenticated users
- Protect all dashboard routes

### Files to Create/Modify

| File | Type | Purpose |
|------|------|---------|
| `templates/login.html` | New | Login form UI |
| `static/login.css` | New | Login page styling |
| `src/auth.py` | New | Authentication logic |
| `src/session.py` | New | Session management |
| `app.py` | Modify | Add login routes, session middleware |
| `requirements.txt` | Modify | Add Flask-Session dependency |

### User Credentials (Hardcoded for MVP)

```python
USERS = {
    "admin": "password123",
    "user1": "user1pass",
    "user2": "user2pass",
    "analyst": "analyst123",
    "manager": "manager123"
}
```

### Key Implementation Points

1. **Session Storage:** File-based sessions in `/tmp/flask_sessions/`
2. **Login Route:** `POST /api/login` (returns session token)
3. **Protected Routes:** All routes except `/login`, `/health`, `/static/*`
4. **Session Timeout:** 30 minutes idle timeout
5. **CORS:** Update to accept session cookies

### Files Modified in This Phase

- `app.py`: Add login route, session middleware, route protection
- `requirements.txt`: Add Flask-Session

### Files Created in This Phase

- `templates/login.html`
- `static/login.css`
- `src/auth.py`
- `src/session.py`

**Estimated Lines of Code:** ~500 lines  
**Commit Message:** `FEATURE: User authentication with login page and session management`

---

## Phase 2: Audit & Action Tracking

### Objective
- Log all user actions (Trans-Begin, PE-Enable, T-Enable, PE-Finalize)
- Persist audit data in SQLite database
- Track user, action type, timestamp, affected customers, IP address

### Files to Create/Modify

| File | Type | Purpose |
|------|------|---------|
| `src/audit.py` | New | Audit logging logic |
| `src/audit_db.py` | New | SQLite database schema and queries |
| `app.py` | Modify | Integrate audit logging into action endpoints |
| `templates/index.html` | Modify | Display audit trail in customer details |

### Database Schema

```sql
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    action_type TEXT NOT NULL,
    customer_ids TEXT,  -- JSON array or comma-separated
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    ip_address TEXT,
    status TEXT,  -- 'success', 'failure'
    error_message TEXT,
    duration_ms INTEGER
);

CREATE INDEX idx_user_timestamp ON audit_log(user_id, timestamp);
CREATE INDEX idx_action_type ON audit_log(action_type);
CREATE INDEX idx_timestamp ON audit_log(timestamp);
```

### Key Implementation Points

1. **Audit Logging:** Automatic on Trans-Begin, PE-Enable, T-Enable, PE-Finalize
2. **Data Retention:** Keep all records (plan for archival at 1M+ records)
3. **Query Performance:** Indexed by user, action type, and timestamp
4. **Concurrency:** SQLite handles up to 50K operations safely
5. **API Endpoint:** `GET /api/audit/trail?customer_id=<id>&limit=50`

### Files Created in This Phase

- `src/audit.py`
- `src/audit_db.py`

### Files Modified in This Phase

- `app.py`: Add audit logging calls, new audit query endpoint

**Estimated Lines of Code:** ~400 lines  
**Commit Message:** `FEATURE: Comprehensive audit trail for all user actions`

---

## Phase 3: UI Enhancements – Action Visibility

### Objective
- Make Customer IDs clickable in Trans-Begin customer list
- Display modal with action history for selected customer
- Show who triggered the action and timestamp

### Files to Create/Modify

| File | Type | Purpose |
|------|------|---------|
| `templates/index.html` | Modify | Add clickable customer IDs, modal for action history |
| `static/index.css` | Modify | Styling for clickable elements and modals |
| `app.py` | Modify | New endpoint for customer action history |

### Key Implementation Points

1. **Clickable Customer ID:** Convert to `<a>` or `<button>` with `data-customer-id`
2. **Modal Dialog:** Display last 20 actions for the customer
3. **Information Displayed:**
   - User who triggered action
   - Action type (Trans-Begin, PE-Enable, etc.)
   - Exact timestamp
   - Success/failure status
4. **API Endpoint:** `GET /api/audit/customer/<customer_id>?limit=20`

### Files Modified in This Phase

- `templates/index.html`
- `static/index.css` (create if not exists)
- `app.py`

**Estimated Lines of Code:** ~300 lines  
**Commit Message:** `FEATURE: Interactive action history for customers with user attribution`

---

## Phase 4: Load Testing & Benchmarking

### Objective
- Create load testing scripts to simulate 50K customers
- Measure performance under various loads
- Document optimization recommendations

### Files to Create

| File | Purpose |
|------|---------|
| `tests/load_test.py` | Locust load testing script |
| `tests/benchmark.py` | Performance benchmarking with pytest-benchmark |
| `LOAD_TEST_RESULTS.md` | Results and recommendations |

### Load Test Scenarios

1. **Baseline:** 10 customers, 10 concurrent users
2. **Light Load:** 100 customers, 50 concurrent users
3. **Medium Load:** 1K customers, 100 concurrent users
4. **Heavy Load:** 10K customers, 500 concurrent users
5. **Stress Test:** 50K customers, 1000 concurrent actions

### Key Metrics Captured

- Response time (p50, p95, p99)
- CPU usage
- Memory usage
- Error rate
- Throughput (requests/second)

**Estimated Lines of Code:** ~500 lines  
**Commit Message:** `TEST: Performance load testing suite for 50K customer capacity validation`

---

## Phase 5: Integration & Testing

### Objective
- Merge all feature branches into develop
- End-to-end testing of all features together
- Performance validation with all enhancements enabled

### Testing Checklist

- [ ] Authentication flow (login, session, logout)
- [ ] Protected routes (403 if not authenticated)
- [ ] Audit logging (creation, querying)
- [ ] UI interactions (clickable customer IDs, modals)
- [ ] Performance (still <1 second for 50K customers)
- [ ] Database integrity (audit logs)
- [ ] Session cleanup (old sessions removed)
- [ ] CORS with session cookies

### Quality Gates

- ✅ All tests passing
- ✅ Performance within baseline ±10%
- ✅ No database corruption
- ✅ Memory leaks checked
- ✅ Security review completed

**Commit Message:** `MERGE: Integrate authentication, audit, and UI enhancements`

---

## Implementation Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| Phase 1: Authentication | 2-3 days | Scheduled |
| Phase 2: Audit Logging | 2-3 days | Scheduled |
| Phase 3: UI Enhancements | 1-2 days | Scheduled |
| Phase 4: Load Testing | 2-3 days | Scheduled |
| Phase 5: Integration | 1-2 days | Scheduled |
| **Total** | **~10 days** | **Ready to Start** |

---

## Rollback Procedures

### Quick Rollback to Baseline
```bash
# Return to initial state (before any enhancements)
cd /home/pdanekula/tms_dashboard_python
git reset --hard 28efac5
git clean -fd
```

### Selective Feature Rollback
```bash
# Remove just authentication
git revert <auth-feature-commit-hash>

# Remove just audit logging
git revert <audit-feature-commit-hash>

# Remove just UI enhancements
git revert <ui-feature-commit-hash>
```

### Revert Last N Commits
```bash
# Revert last 3 commits (but keep them in history)
git revert HEAD~2..HEAD

# Revert last 3 commits (hard reset - dangerous, loses history)
git reset --hard HEAD~3
```

---

## Monitoring & Metrics

### During Implementation
- Git commit count (should increase by ~20-30)
- Branch count (should have 4-5 feature branches)
- Code coverage (aim for >80% on new code)
- Performance baseline drift (should be <5%)

### After Implementation
- Audit log growth rate (records per day)
- Authentication success rate (>99%)
- Session timeout efficiency
- API response times with audit logging enabled

---

## Risk Mitigation

| Risk | Mitigation Strategy |
|------|-------------------|
| Performance degradation | Load test each phase, revert if >10% slower |
| Database locks | SQLite handles <50K ops; migrate to PostgreSQL if needed |
| Session storage issues | Use file-based sessions, monitor disk space |
| Audit log explosion | Implement log rotation at 1M records |
| Authentication bypass | Code review, SQL injection prevention |
| Concurrent write conflicts | SQLite WAL mode enabled by default in Python 3.10+ |

---

## Sign-Off

**Prepared by:** TMS Development Team  
**Date:** January 10, 2026  
**Status:** ✅ **Ready for Implementation**

**Dependencies Met:**
- ✅ System capacity validated (50K customers supported)
- ✅ Git repository initialized with baseline commit
- ✅ Feature branch strategy documented
- ✅ Rollback procedures documented
- ✅ Risk assessment completed

**Approval to Proceed:** YES - Begin implementation of Phase 1 (Authentication)

---

## Next Steps

1. Create `feature/auth` branch: `git checkout -b feature/auth`
2. Implement authentication (Phase 1)
3. Test locally
4. Create pull request for review
5. Proceed to Phase 2 after Phase 1 completion
