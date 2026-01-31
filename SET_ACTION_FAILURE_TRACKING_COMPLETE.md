# Set Action Failure Tracking Enhancement - Complete Implementation

## Overview

Enhanced the Set Action feature to capture and display API response outcomes (success/failure) with detailed status tracking in the User Jobs Audit tab.

**Goal Achieved:** When a user runs Set Action and it fails (HTTP >= 400 or timeout/exception), the same job record is now updated as FAILED with status details, which are displayed in the User Jobs Audit with color-coded badges.

---

## Changes Summary

### 1. Database Schema Extensions

**File:** `src/jobs.py` - `initialize_jobs_database()` function

**New Columns Added:**
```sql
-- Added to jobs table:
http_status INTEGER          -- HTTP status code from API response (e.g., 401, 408, 500)
error_message TEXT           -- Short error description (e.g., "Request timeout after 30s")
updated_at TEXT              -- Timestamp when job was last updated
```

**Schema Migration:**
- Automatic schema migration on app startup via `ALTER TABLE` commands
- Safely handles existing databases (columns that already exist are skipped)
- Logs migration progress

**Implementation:**
```python
# In initialize_jobs_database():
try:
    cursor.execute('PRAGMA table_info(jobs)')
    columns = {row[1] for row in cursor.fetchall()}
    
    if 'http_status' not in columns:
        cursor.execute('ALTER TABLE jobs ADD COLUMN http_status INTEGER')
    if 'error_message' not in columns:
        cursor.execute('ALTER TABLE jobs ADD COLUMN error_message TEXT')
    if 'updated_at' not in columns:
        cursor.execute('ALTER TABLE jobs ADD COLUMN updated_at TEXT')
except Exception as e:
    print(f"[JOBS] WARNING: Schema migration error: {str(e)}")
```

---

### 2. Backend Changes

#### A. New `update_job()` Function

**File:** `src/jobs.py`

```python
def update_job(job_id, status, http_status=None, error_message=None, response_summary=None):
    """
    Update an existing job with status and optional error details
    
    Args:
        job_id (str): Job ID to update
        status (str): New status (SUCCESS, FAILED, IN_PROGRESS)
        http_status (int): Optional HTTP status code
        error_message (str): Optional error message
        response_summary (str): Optional updated response summary
    
    Returns:
        bool: True if successful, False otherwise
    """
```

**Key Features:**
- Dynamically builds UPDATE query based on provided parameters
- Updates `updated_at` timestamp automatically
- Handles NULL values for optional fields
- Returns boolean success status

#### B. Modified `create_job()` Function

**Changes:**
- Added `status` parameter (default: `'IN_PROGRESS'`)
- Changed default status from `'success'` to `'IN_PROGRESS'` for tracking
- Now stores `updated_at` on creation

```python
def create_job(user_id, action_code, action_name, cids, cluster_url=None, 
               batch_id=None, request_payload=None, response_summary=None, status='IN_PROGRESS'):
```

#### C. Enhanced `/proxy_fetch` Endpoint

**File:** `app.py`

**Refactored Flow:**

```
1. REQUEST RECEIVED
   ├─ Extract action_type and customer_ids from request

2. CREATE JOB IMMEDIATELY (before API call)
   ├─ Status: IN_PROGRESS
   ├─ Return: job_id for tracking
   └─ Store: request_payload, cluster_url, etc.

3. EXECUTE API CALL
   ├─ POST to upstream API (30s timeout)
   ├─ Handle different content types
   └─ Capture HTTP response

4. HANDLE RESULT
   ├─ SUCCESS (HTTP 2xx)
   │  ├─ Parse response JSON
   │  ├─ Check API success field
   │  ├─ UPDATE job: status=SUCCESS, http_status=<code>
   │  └─ Return: response with job_id
   │
   ├─ FAILURE (HTTP >= 400)
   │  ├─ Capture error details
   │  ├─ UPDATE job: status=FAILED, http_status=<code>, error_message=<msg>
   │  └─ Return: error response with job_id
   │
   └─ EXCEPTION (timeout/network)
      ├─ Capture exception message
      ├─ UPDATE job: status=FAILED, http_status=NULL, error_message=<exception>
      └─ Return: error response with job_id

5. SAME JOB RECORD (no duplicates)
   └─ Job created once, updated based on result
```

**Status Values:**
- `IN_PROGRESS` - Job created, API call in progress
- `SUCCESS` - API call returned HTTP 2xx and success=true
- `FAILED` - API error, timeout, or exception

**Key Improvements:**
- One job creation per request (no duplicates)
- Atomic update: job result status determined by single request
- HTTP status code stored for debugging
- Error message included in response and stored in DB
- Job ID always returned (even on failure) so frontend can display it

---

### 3. Frontend Changes

#### A. Updated Table Schema

**File:** `templates/index.html`

**Table Headers:** Added Status column
```html
<th style="padding: 12px; text-align: center; font-weight: 600; color: #333;">Status</th>
```

**Updated colspan:** Changed from `4` to `5` columns

#### B. Enhanced `loadUserJobsAudit()` Function

**New Features:**

1. **Color-Coded Status Badges**
   - `SUCCESS` → Green badge (#4caf50)
   - `FAILED` → Red badge (#dc3545)
   - `IN_PROGRESS` → Blue badge (#2196f3)
   - Unknown → Gray badge (#999)

2. **Tooltip Support**
   - Hover over red FAILED badge to see error details
   - Format: `"HTTP 401 - Unauthorized"`
   - Shows both HTTP status code and error message

3. **Dynamic Badge Rendering**
   ```javascript
   function getStatusBadge(status, httpStatus, errorMessage) {
       // Returns HTML with appropriate color and tooltip
       // Badge text: "SUCCESS", "FAILED", "IN_PROGRESS"
   }
   ```

**Response Mapping:**
- API endpoint returns: `status`, `http_status`, `error_message`
- Frontend maps to badges with color coding
- Tooltip shows HTTP status + error message when FAILED

---

## Flow Example: Failed Set Action

### User Action
```
User clicks "Set Action" → Trans-Begin, 2 customers
```

### Backend Processing
```
[SET_ACTION] Starting: user=admin, action=Trans-Begin, cid_count=2
[SET_ACTION] Creating job: action_code=1, action_name=Trans-Begin, cid_count=2
[SET_ACTION] Job created with job_id=abc123-..., status=IN_PROGRESS

(Execute API call to external cluster)
API Response: HTTP 401 - "Unauthorized"

[SET_ACTION] FAILED: HTTP 401
[SET_ACTION] Job abc123-... marked as FAILED
```

### Database Update
```sql
UPDATE jobs 
SET status='FAILED', 
    http_status=401, 
    error_message='API returned status 401: Unauthorized',
    updated_at='2026-01-28T18:25:00...'
WHERE job_id='abc123-...';
```

### Frontend Display
```
User Jobs Audit Table:
┌─────────────────────────────────────────────────────────────────────┐
│ Job ID         │ Action      │ Customers │ Status      │ Timestamp  │
├─────────────────────────────────────────────────────────────────────┤
│ abc123-...     │ Trans-Begin │ 2         │ FAILED (🔴) │ 18:25 PM   │
│                │             │           │             │            │
│ Tooltip on hover: "HTTP 401 - API returned status 401: ..."        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Files Modified

| File | Changes | Impact |
|------|---------|--------|
| `src/jobs.py` | Added schema migration, `update_job()` function, modified `create_job()` and `get_user_jobs()` | Backend job tracking |
| `app.py` | Imported `update_job`, refactored `/proxy_fetch` endpoint to create job first, then update with result | Status tracking in requests |
| `templates/index.html` | Added Status column to User Jobs Audit table, enhanced `loadUserJobsAudit()` with status badge rendering | Frontend display |

---

## Acceptance Criteria ✅

| Criterion | Status | Implementation |
|-----------|--------|-----------------|
| If Set Action returns 401/408/504/etc, same job row updated as FAILED | ✅ | `update_job()` updates existing job with FAILED status |
| User Jobs Audit shows job_id in red and/or status badge | ✅ | Red badge (#dc3545) displayed for FAILED status |
| Successful jobs remain normal/green | ✅ | Green badge (#4caf50) displayed for SUCCESS status |
| No changes to 30s timeout fix | ✅ | Timeout value unchanged, only status tracking added |
| Job ID shows tooltip with error details on FAILED | ✅ | Hover tooltip shows "HTTP xxx - error message" |

---

## Status Values & Meanings

| Status | Color | Meaning | Example |
|--------|-------|---------|---------|
| `SUCCESS` | 🟢 Green | API call succeeded (HTTP 2xx + success=true) | "Cluster accepted request" |
| `FAILED` | 🔴 Red | API error, timeout, or network issue | "HTTP 401 - Unauthorized" |
| `IN_PROGRESS` | 🔵 Blue | Job created, awaiting API response | Job waiting for cluster |

---

## Logging Output

When a Set Action runs, you'll see:

**Success Case:**
```
[SET_ACTION] Starting: user=admin, action=Trans-Begin, cid_count=2
[SET_ACTION] Creating job: action_code=1, action_name=Trans-Begin, cid_count=2
[SET_ACTION] Job created with job_id=7d71c7ad-914b-459a..., status=IN_PROGRESS
[SET_ACTION] Job 7d71c7ad-... updated: status=SUCCESS, http_status=200
```

**Failure Case:**
```
[SET_ACTION] Starting: user=admin, action=Trans-Begin, cid_count=2
[SET_ACTION] Creating job: action_code=1, action_name=Trans-Begin, cid_count=2
[SET_ACTION] Job created with job_id=7d71c7ad-914b-459a..., status=IN_PROGRESS
[SET_ACTION] FAILED: HTTP 401, API returned status 401: Unauthorized
[SET_ACTION] Job 7d71c7ad-... marked as FAILED
```

**Timeout Case:**
```
[SET_ACTION] Starting: user=admin, action=Trans-Begin, cid_count=2
[SET_ACTION] Creating job: action_code=1, action_name=Trans-Begin, cid_count=2
[SET_ACTION] Job created with job_id=7d71c7ad-914b-459a..., status=IN_PROGRESS
[SET_ACTION] TIMEOUT: user=admin, action=Trans-Begin
[SET_ACTION] Job 7d71c7ad-... marked as FAILED (timeout)
```

---

## Database Query Examples

**View all jobs with their status:**
```sql
SELECT job_id, user_id, action_name, status, http_status, error_message, created_at, updated_at
FROM jobs
ORDER BY created_at DESC
LIMIT 20;
```

**Find all failed jobs:**
```sql
SELECT job_id, action_name, http_status, error_message, created_at
FROM jobs
WHERE status = 'FAILED'
ORDER BY created_at DESC;
```

**Find jobs by HTTP status:**
```sql
SELECT job_id, action_name, error_message, created_at
FROM jobs
WHERE http_status = 401
ORDER BY created_at DESC;
```

---

## Testing Scenarios

### Test 1: Successful Set Action
1. Go to TMS Customer Set tab
2. Select action (e.g., "Trans-Begin")
3. Enter 1-2 customer IDs
4. Enter valid API token
5. Click Set Action
6. Check User Jobs Audit → Should show **GREEN SUCCESS badge**

### Test 2: Failed Set Action (Invalid Token)
1. Go to TMS Customer Set tab
2. Select action
3. Enter customer IDs
4. Enter **WRONG/INVALID** API token
5. Click Set Action
6. Check User Jobs Audit → Should show **RED FAILED badge**
7. Hover over badge → Should show "HTTP 401 - ..." error

### Test 3: Timeout Scenario
1. Go to TMS Customer Set tab
2. Select action
3. Enter customer IDs
4. Enter API token pointing to **unresponsive server**
5. Click Set Action
6. Wait 30+ seconds
7. Check User Jobs Audit → Should show **RED FAILED badge**
8. Hover over badge → Should show "Request timeout after 30s"

### Test 4: API Rejection (API Success=False)
1. Go to TMS Customer Set tab
2. Select action
3. Enter customer IDs
4. Click Set Action to valid API, but API returns success=false
5. Check User Jobs Audit → Should show **RED FAILED badge**
6. Hover → Should show HTTP 200 + error message from API

---

## No Functional Changes

✅ **Preserved:**
- 30-second timeout behavior (unchanged)
- Job creation happens once per request (fixed in previous enhancement)
- API payload format (unchanged)
- Response format to frontend (job_id added to responses)
- User experience (silent success, clear error display)

✅ **Added:**
- Job status tracking (IN_PROGRESS → SUCCESS/FAILED)
- HTTP status code storage
- Error message storage
- Status badges in audit table
- Error tooltips on hover

---

## Production Deployment Checklist

- [x] Schema migration is automatic and safe
- [x] No breaking changes to API responses
- [x] Backward compatible (handles missing columns gracefully)
- [x] All error paths log and update job status
- [x] Job ID always returned (even on failure)
- [x] Frontend displays status with helpful tooltips
- [x] 30-second timeout preserved
- [x] No duplicate job creation

**Ready for production:** ✅ YES

---

## Conclusion

The Set Action enhancement now provides complete visibility into job execution:
- **Creation:** Job immediately marked IN_PROGRESS
- **Execution:** Request sent to upstream API
- **Completion:** Job updated with SUCCESS or FAILED status
- **Display:** User Jobs Audit shows status with color-coded badges and error details

This enables users to quickly identify failed actions and understand why they failed (HTTP status + error message), making troubleshooting and debugging much easier.
