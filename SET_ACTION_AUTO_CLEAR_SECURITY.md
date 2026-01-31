# Set Action Notification Auto-Clear & Token Security

## Overview

The TMS Dashboard now implements automatic clearing of Set Action notifications and Bearer tokens to balance **user experience** with **security best practices**.

## Current Implementation

### Auto-Clear Behavior

#### 1. **Same Tab Stay (30 seconds)**
When a user triggers a Set Action and remains on the TMS Customer Set tab:
- ✅ Success/error message displayed immediately
- ⏱️ Message stays visible for **30 seconds** (user can read details, copy payload)
- 🔄 After 30 seconds: Message automatically hidden
- 🔐 Bearer token field automatically cleared

#### 2. **Tab Switch (Immediate)**
When a user leaves the TMS Customer Set tab (switches to Status, Audit, etc.):
- ✅ Message immediately hidden
- 🔐 Bearer token field immediately cleared
- ⏱️ Auto-clear timeout cancelled

### Why 30 Seconds?

| Duration | Reasoning | Use Case |
|----------|-----------|----------|
| **5 seconds** | ❌ Too short | Users don't have time to read error messages or copy details |
| **10 seconds** | ⚠️ Marginal | Better but still tight for complex error messages |
| **30 seconds** | ✅ Optimal | Enough time to understand message, copy payload, but not too long |
| **60+ seconds** | ⚠️ Too long | Bearer token remains exposed in UI for extended time |

## Security Considerations

### Why Clear Token Immediately on Tab Switch?

**Security Risk:**
- Bearer tokens are sensitive credentials
- If user steps away, token remains visible in password field
- Another person could access token and perform unauthorized actions
- Browser history/accessibility features could cache the token

**Solution:**
- When user leaves tab, token is **immediately cleared**
- This ensures token is never exposed longer than necessary
- Prevents accidental token leakage if user forgets to clear

### Why 30 Seconds Auto-Clear?

**User Experience:**
- Users need time to review error messages and take action
- Complex authorization errors need full error text visible
- Users might need to copy request payload for debugging

**Security Balance:**
- 30 seconds is long enough for legitimate use
- Not so long that stale tokens accumulate
- Consistent with session timeout practices (15 minutes)

## Code Implementation

### Notification Display
```javascript
function showSetActionSuccess(message) {
    // ... display message ...
    
    // Clear previous timeout if exists
    if (setActionTimeoutId) {
        clearTimeout(setActionTimeoutId);
    }
    
    // Auto-clear after 30 seconds
    setActionTimeoutId = setTimeout(() => {
        clearSetActionNotifications();
    }, 30000);  // 30 seconds
}
```

### Tab Switching
```javascript
function switchTab(tab) {
    // Clear when switching away from Set Action tab
    if (tab !== 'set') {
        clearSetActionNotifications();  // Immediate clear
    }
    
    // ... update UI ...
}
```

### Clearing Function
```javascript
function clearSetActionNotifications() {
    // Hide success message
    document.getElementById('setActionResponse').style.display = 'none';
    
    // Hide error message
    document.getElementById('setActionError').style.display = 'none';
    
    // Clear token field (security)
    document.getElementById('setActionToken').value = '';
    
    // Cancel timeout
    if (setActionTimeoutId) {
        clearTimeout(setActionTimeoutId);
        setActionTimeoutId = null;
    }
}
```

## Best Practices Explained

### 1. **Sensitive Data Lifecycle**
```
Token Entered → Used for Request → Message Shown (30 sec) → Auto-cleared
      ↑                                                           
      └─────────── Immediately cleared on tab switch ──────────┘
```

### 2. **User Control**
Even though auto-clear is enabled, users can:
- ✅ **Manually close** message by clicking the ✕ button
- ✅ **Copy payload** before auto-clear happens
- ✅ **Re-enter token** if they need to retry

### 3. **Timeout Cancellation**
If user gets multiple responses:
```javascript
// Previous timeout cancelled before new one starts
if (setActionTimeoutId) {
    clearTimeout(setActionTimeoutId);  // Cancel old
}
// New timeout set
setActionTimeoutId = setTimeout(...);  // Start new
```

## Testing the Feature

### Test 1: Auto-Clear After 30 Seconds
```
1. Go to TMS Customer Set tab
2. Enter all details
3. Click "Set Action" → "Yes, Proceed"
4. Observe success/error message
5. Wait 30 seconds...
6. Message automatically disappears
7. Token field is empty
```

**Expected:** After 30 seconds, notification hidden and token cleared.

### Test 2: Clear on Tab Switch
```
1. Go to TMS Customer Set tab
2. Click "Set Action" → "Yes, Proceed"
3. Message appears with token field visible
4. Switch to "TMS Customer Status" tab
5. Return to "TMS Customer Set" tab
6. Check notification and token field
```

**Expected:** When switching tabs, notification hidden and token cleared immediately.

### Test 3: Multiple Requests
```
1. Go to TMS Customer Set tab
2. Request 1: Click "Set Action" → observe message at t=0s
3. Request 2: At t=10s, click "Set Action" again
4. Previous timeout should be cancelled
5. New 30-second timer starts from new request
```

**Expected:** Only latest 30-second timer active, previous one cancelled.

### Test 4: Manual Close
```
1. Go to TMS Customer Set tab
2. Click "Set Action" → "Yes, Proceed"
3. Click ✕ button on notification
4. Message immediately hidden (before 30 sec)
```

**Expected:** Manual close works immediately, no need to wait 30 seconds.

## Configuration

### Changing the Timeout Duration

If you want to modify the 30-second timeout:

**File:** `templates/index.html`

**Find:** Line with `30000` (milliseconds)

**Change:**
```javascript
// Currently 30 seconds
setActionTimeoutId = setTimeout(() => {
    clearSetActionNotifications();
}, 30000);  // Change this number
```

**Common values:**
- `15000` = 15 seconds (shorter, more secure)
- `30000` = 30 seconds (current, balanced)
- `60000` = 60 seconds (longer, more time to read)

## Comparison: Alternative Approaches

### Option A: Immediate Clear (Current Implementation's Extreme)
**Pros:** Maximum security, no stale tokens
**Cons:** Users can't read messages, copy payloads
**When to use:** Highly sensitive military/government systems

### Option B: No Auto-Clear
**Pros:** Users have all time to read/copy
**Cons:** Token remains visible indefinitely, security risk
**When to use:** Demo/development environments only

### Option C: 30-Second Auto-Clear + Immediate Tab Switch Clear (RECOMMENDED ✅)
**Pros:** 
- Balanced security and UX
- Users get 30 seconds to read/copy
- Token auto-cleared on tab switch
- Token auto-cleared after 30 seconds

**Cons:** Slightly more complex code
**When to use:** Production TMS dashboard ✅

### Option D: Very Long Timeout (5+ minutes)
**Pros:** Plenty of time for users
**Cons:** Token exposed for too long, security risk
**When to use:** Not recommended

## Related Changes

- [Set Action Audit Logging](SET_ACTION_AUDIT_LOGGING.md) - Full audit trail of all Set Action attempts
- [Set Action Error Handling](../SET_ACTION_AUDIT_LOGGING.md#error-handling) - Detailed error messages

## Future Enhancements

1. **Configurable timeout:** Admin panel to adjust per-user preferences
2. **Toast notifications:** Brief auto-hide popups instead of persistent messages
3. **Copy button:** Auto-add "Copy to Clipboard" button for payloads
4. **Session lock:** Lock inputs during processing to prevent double-submission
5. **Token masking:** Show token as `••••••••` instead of full value
