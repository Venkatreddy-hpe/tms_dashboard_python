# Set Action Audit Logging Feature

## Overview
When users trigger Set Action operations (Trans-Begin, PE-Enable, T-Enable, PE-Finalize) via the TMS Customer Set tab, the system now automatically creates audit records for each customer affected. These audit records are immediately visible in the Action History modal on the TMS Customer Status page.

## How It Works

### 1. User Triggers Set Action
- User navigates to **TMS Customer Set** tab
- Enters API Base URL, selects action, provides Bearer token, and adds customer IDs
- Clicks **"Set Action"** button
- Confirmation modal appears
- Clicks **"Yes, Proceed"**

### 2. API Request Made
- Frontend sends POST request to `/proxy_fetch` endpoint with:
  ```json
  {
    "url": "https://api-endpoint/tms/v1/set/action",
    "token": "bearer_token_here",
    "isPost": true,
    "postData": {
      "action": "Trans-Begin",
      "cids": ["customer-id-1", "customer-id-2"]
    }
  }
  ```

### 3. Proxy Endpoint Processes Request
- `/proxy_fetch` route extracts action type and customer IDs from `postData`
- Makes HTTP request to external API with provided Bearer token
- Receives response from API

### 4. Audit Record Created
- **For Successful API Responses (HTTP 200/201):**
  - Checks if API response contains `success: true`
  - If yes: Creates audit record with `status: 'success'`
  - If no (API says `success: false`): Creates audit record with `status: 'failure'` and error message

- **For Failed Requests:**
  - Timeout: Records with error message "Request timeout"
  - Connection Error: Records with error message from exception
  - HTTP Error: Records with error message from API response

### 5. Audit Record Structure
Each Set Action creates one audit record with:
```python
{
    "user_id": "admin",           # Username who triggered action
    "action_type": "Trans-Begin", # Action type
    "customer_ids": "[\"cid1\", \"cid2\"]",  # JSON array of affected customers
    "timestamp": "2026-01-12 10:38:31",     # When action was triggered
    "ip_address": "192.168.1.100",          # Source IP address
    "status": "success",                    # 'success' or 'failure'
    "error_message": null                   # Error details if failed
}
```

### 6. User Views Action History
- User navigates to **TMS Customer Status** page
- Clicks on a Customer ID (e.g., 0f0f3d4eefdd11f08a296edcca163eca)
- **Action History** modal opens
- Shows all actions triggered for that customer, including:
  - ✅ Set Action operations (Trans-Begin, PE-Enable, etc.)
  - 👤 User who triggered the action
  - 📅 Timestamp when action was triggered
  - ❌ Error details if action failed

## Database Schema

**Table:** `audit_log`

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| user_id | TEXT | Username who performed action |
| action_type | TEXT | Type: Trans-Begin, PE-Enable, T-Enable, PE-Finalize |
| customer_ids | TEXT | JSON array of affected customer IDs |
| timestamp | DATETIME | When action was performed |
| ip_address | TEXT | Source IP address |
| status | TEXT | 'success' or 'failure' |
| error_message | TEXT | Error details if failed |
| duration_ms | INTEGER | How long the request took |

**Indexes:**
- `idx_customer_search`: On `customer_ids` for fast lookups
- `idx_action_type`: On `action_type` for filtering
- `idx_user_timestamp`: On `user_id, timestamp` for user history
- `idx_timestamp`: On `timestamp` for recent records

## Code Implementation

### Backend Changes (app.py)

**proxy_fetch() Route:**
```python
@app.route('/proxy_fetch', methods=['POST'])
@require_auth
def proxy_fetch():
    # Extract action and customer IDs
    if post_data and isinstance(post_data, dict):
        action_type = post_data.get('action')
        customer_ids = post_data.get('cids')
    
    # ... make API request ...
    
    # Log successful actions
    if response.status_code in [200, 201]:
        api_success = json_data.get('success', True)
        if api_success:
            log_user_action(
                user_id=user_id,
                action_type=action_type,
                customer_ids=customer_ids,
                ip_address=get_client_ip(request),
                status='success'
            )
        else:
            # Log API failures
            log_user_action(
                user_id=user_id,
                action_type=action_type,
                customer_ids=customer_ids,
                ip_address=get_client_ip(request),
                status='failure',
                error_message=json_data.get('message')
            )
    
    # Also logs timeout, connection, and HTTP errors
```

### Frontend Changes (templates/index.html)

**Set Action confirmation modal:**
- Stores action, customer IDs, and token in `window._pendingSetAction`
- On "Yes, Proceed": Calls `/proxy_fetch` with complete request data
- Unwraps proxy response to check actual API `success` field
- Shows error or success message to user

## Testing the Feature

### Manual Testing Steps

1. **Trigger Set Action:**
   ```
   1. Go to TMS Customer Set tab
   2. Enter API URL: https://your-api-endpoint
   3. Select Action: Trans-Begin
   4. Enter Bearer Token: your_token_here
   5. Add Customer ID: 649362220c0a11ee81ed1aef39a71869
   6. Click "Set Action" → Click "Yes, Proceed"
   ```

2. **Check Audit Record Created:**
   ```bash
   python3 -c "
   import sqlite3
   conn = sqlite3.connect('audit.db')
   cursor = conn.cursor()
   cursor.execute('SELECT * FROM audit_log WHERE customer_ids LIKE ?', ('%649362220c0a11ee81ed1aef39a71869%',))
   print(cursor.fetchall())
   conn.close()
   "
   ```

3. **View in Action History Modal:**
   - Go to TMS Customer Status
   - Click the customer ID (649362220c0a11ee81ed1aef39a71869)
   - Action History modal should show the Set Action record

### Expected Results

✅ **Success Case (API returns success: true):**
- Audit record created with `status: 'success'`
- Action History modal shows: ✅ [Trans-Begin] triggered by admin at 10:38:31 AM

❌ **Failure Case (API returns success: false):**
- Audit record created with `status: 'failure'` and error message
- Action History modal shows: ❌ [Trans-Begin] FAILED - Authorization check failed...

⚠️ **Error Case (Network/Timeout):**
- Audit record created with error message
- Dashboard shows error popup to user

## Troubleshooting

### Audit records not appearing in Action History

**Possible causes:**

1. **Customer ID mismatch:**
   - Customer ID in Set Action form must exactly match the ID you're searching for
   - Ensure no extra spaces or case differences

2. **Action type not supported:**
   - Valid actions: Trans-Begin, PE-Enable, T-Enable, PE-Finalize
   - Check spelling in frontend code if adding new actions

3. **Database not initialized:**
   - Run: `python3 app.py` once to initialize audit.db
   - Check audit_log table exists: `sqlite3 audit.db ".tables"`

4. **User session issue:**
   - User must be logged in for `user_id` to be captured
   - Check `session.get('user_id')` is populated

### Server logs show "Extracted customer IDs: None"

**Fix:**
- Ensure frontend sends `postData.cids` as array: `["id1", "id2"]`
- Check Set Action button properly constructs payload before clicking Proceed

## Related Files

- **Frontend:** `/templates/index.html` (lines 1030-1700 for Set Action)
- **Backend Routes:** `/app.py` (proxy_fetch at line 177)
- **Audit Module:** `/src/audit.py` (logging functions)
- **Database:** `/src/audit_db.py` (database operations)
- **Database File:** `/audit.db` (SQLite database)

## Future Enhancements

1. **Bulk export:** Download audit records as CSV/Excel
2. **Advanced filtering:** Filter by date range, action type, status
3. **Audit reports:** Generate summary reports of Set Action usage
4. **Retention policy:** Auto-delete records older than X days
5. **Real-time alerts:** Notify admins of failed Set Action attempts
