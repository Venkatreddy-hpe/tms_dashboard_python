# Set Action Status Tracking - Quick Test Guide

## TL;DR

The Set Action feature now tracks job execution status:
- 🟢 **SUCCESS** (green) - API accepted the request
- 🔴 **FAILED** (red) - API rejected, timeout, or network error
- 🔵 **IN_PROGRESS** (blue) - Job created, waiting for response

Status badges appear in the **User Jobs Audit** tab with error details on hover.

---

## Quick Setup

1. **App is running:**
   ```bash
   ps aux | grep "python3 app.py" | grep -v grep
   ```

2. **Check logs for successful schema migration:**
   ```bash
   tail -20 /home/pdanekula/tms_dashboard_python/app.log
   ```
   Should see:
   ```
   [JOBS] Added http_status column to jobs table
   [JOBS] Added error_message column to jobs table
   [JOBS] Added updated_at column to jobs table
   [JOBS] Database initialized successfully
   ```

---

## Test Scenario 1: Successful Action ✅

**Setup:**
- Valid API credentials
- Valid customer ID

**Steps:**
1. Navigate to: **TMS Customer Set** tab
2. Select Action: `Trans-Begin`
3. Enter Token: Use a **VALID** token
4. Enter Customer IDs: Any valid customer ID
5. Click: **Set Action** button
6. Switch to: **User Jobs Audit** tab

**Expected Result:**
- New job appears with **GREEN SUCCESS badge**
- No error details (or hover shows HTTP 200)

---

## Test Scenario 2: Failed Action (Invalid Token) ❌

**Setup:**
- Invalid/wrong API token
- Valid customer ID

**Steps:**
1. Navigate to: **TMS Customer Set** tab
2. Select Action: `Trans-Begin`
3. Enter Token: Use an **INVALID** token (e.g., "wrong-token-123")
4. Enter Customer IDs: Any valid customer ID
5. Click: **Set Action** button
6. Wait a few seconds for request to fail
7. Switch to: **User Jobs Audit** tab

**Expected Result:**
- New job appears with **RED FAILED badge**
- Hover over badge → shows: `"HTTP 401 - API returned status 401: Unauthorized"`

---

## Test Scenario 3: Request Timeout ⏱️

**Setup:**
- API Base URL pointing to non-existent or very slow server
- Valid customer ID

**Steps:**
1. Navigate to: **TMS Customer Set** tab
2. Update API Base URL to: `https://httpbin.org/delay/40` (or any slow endpoint)
3. Select Action: `Trans-Begin`
4. Enter Token: Any token
5. Enter Customer IDs: Any valid customer ID
6. Click: **Set Action** button
7. Wait 30+ seconds for timeout
8. Switch to: **User Jobs Audit** tab

**Expected Result:**
- New job appears with **RED FAILED badge**
- Hover over badge → shows: `"Request timeout after 30s"`

---

## Manual Database Query (Optional)

To verify job status in database:

```bash
sqlite3 /home/pdanekula/tms_dashboard_python/jobs.db << EOF
SELECT 
    job_id,
    action_name,
    status,
    http_status,
    error_message,
    created_at
FROM jobs
ORDER BY created_at DESC
LIMIT 10;
EOF
```

**Sample Output:**
```
abc123-def456|Trans-Begin|SUCCESS|200|
def456-ghi789|Trans-Begin|FAILED|401|API returned status 401: Unauthorized
ghi789-jkl012|Trans-Begin|FAILED||Request timeout after 30s
```

---

## Logs to Monitor

While testing, watch the Flask logs:

```bash
tail -f /home/pdanekula/tms_dashboard_python/app.log | grep SET_ACTION
```

You'll see:

**Success:**
```
[SET_ACTION] Starting: user=admin, action=Trans-Begin, cid_count=2
[SET_ACTION] Creating job: action_code=1, action_name=Trans-Begin, cid_count=2
[SET_ACTION] Job created with job_id=abc123-..., status=IN_PROGRESS
[SET_ACTION] Job abc123-... updated: status=SUCCESS, http_status=200
```

**Failure:**
```
[SET_ACTION] Starting: user=admin, action=Trans-Begin, cid_count=2
[SET_ACTION] Creating job: action_code=1, action_name=Trans-Begin, cid_count=2
[SET_ACTION] Job created with job_id=def456-..., status=IN_PROGRESS
[SET_ACTION] FAILED: HTTP 401, API returned status 401: Unauthorized
[SET_ACTION] Job def456-... marked as FAILED
```

---

## UI Elements to Check

### User Jobs Audit Table
```
┌──────────────────────────────────────────────────────────────────┐
│ Job ID           │ Action      │ Customers │ Status     │ Time    │
├──────────────────────────────────────────────────────────────────┤
│ abc123-def456... │ Trans-Begin │ 2         │ SUCCESS ✓  │ 18:30   │
│ def456-ghi789... │ Trans-Begin │ 1         │ FAILED ✗   │ 18:29   │
│ ghi789-jkl012... │ Trans-Begin │ 3         │ FAILED ✗   │ 18:28   │
└──────────────────────────────────────────────────────────────────┘
                    ↑ Color coded
                    GREEN = Success
                    RED = Failed
```

### Status Badges
- **GREEN** (#4caf50): `SUCCESS` - API accepted
- **RED** (#dc3545): `FAILED` - Error occurred
- **BLUE** (#2196f3): `IN_PROGRESS` - Still executing
- **GRAY** (#999): Unknown status

### Hover Tooltip
Hover over RED badge to see:
```
HTTP 401 - API returned status 401: Unauthorized
HTTP 408 - Request timeout after 30s
HTTP 500 - Connection refused
```

---

## Success Criteria

✅ New job appears in User Jobs Audit within seconds
✅ Status badge is colored correctly (green/red/blue)
✅ Successful jobs show GREEN badge
✅ Failed jobs show RED badge with error on hover
✅ Timeout errors show "Request timeout after 30s"
✅ No duplicate jobs created per action
✅ Job ID is displayed and clickable
✅ Flask logs show job creation and update

---

## Troubleshooting

**Q: No new jobs appearing in User Jobs Audit**
- Check if Set Action completed (success message shown?)
- Check Flask logs for [SET_ACTION] messages
- Try refreshing the page or clicking "Refresh" button

**Q: Badge color is wrong**
- Reload page to refresh data from API
- Check Flask logs to see actual status in database
- Verify API token is correct/invalid (depends on scenario)

**Q: Hover tooltip not showing**
- Check browser DevTools Console for JavaScript errors
- Verify error_message field is populated in database
- Try different browser if issue persists

**Q: Job status stuck as IN_PROGRESS**
- Indicates job was created but result never updated
- Check Flask logs for exceptions during update
- May indicate database lock or connection issue

---

## Expected Behavior Summary

| Scenario | Status | Badge Color | Tooltip | Log Message |
|----------|--------|-------------|---------|-------------|
| Valid token, valid API | SUCCESS | 🟢 Green | (none) | "Job...updated: status=SUCCESS, http_status=200" |
| Invalid token | FAILED | 🔴 Red | "HTTP 401 - Unauthorized" | "FAILED: HTTP 401..." |
| Network timeout | FAILED | 🔴 Red | "Request timeout after 30s" | "TIMEOUT: user=..." |
| API rejects request | FAILED | 🔴 Red | "HTTP 400/500 - ..." | "FAILED: HTTP..." |
| Job in progress | IN_PROGRESS | 🔵 Blue | (none) | "Job created...status=IN_PROGRESS" |

---

## Clean Up Test Data (Optional)

If you want to start fresh after testing:

```bash
sqlite3 /home/pdanekula/tms_dashboard_python/jobs.db << EOF
DELETE FROM job_customers;
DELETE FROM jobs;
EOF
```

Then restart app:
```bash
pkill -f "python3 app.py"
cd /home/pdanekula/tms_dashboard_python && python3 app.py > app.log 2>&1 &
```

---

**Ready to test!** 🚀

Start with Test Scenario 1 (successful action) to verify basic functionality, then try the failure scenarios.
