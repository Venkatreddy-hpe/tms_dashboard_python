# TMS Dashboard - Tabbed Interface Update

## 🎉 Changes Implemented

### UI Structure
- **Tabbed Interface** with two main tabs at the top:
  - **Tab 1: TMS Customer Set** (⚙️) - NEW
  - **Tab 2: TMS Customer Status** (📊) - Existing pages moved here

### Tab 1: TMS Customer Set
**Purpose:** Set/update customer states via the `/set/action` API

**Features:**
- 🎯 **Action Selector** - Dropdown to choose action:
  - Tran-Begin
  - PE-Enable
  - T-Enable
  - PE-Finalize
  
- 🔐 **Bearer Token Input** - Required authorization token

- 📋 **Customer ID Input** - Flexible input format:
  - One ID per line
  - OR comma-separated on single line
  - Automatically parsed and validated

- 🚀 **Set Action Button** - Executes the API request

- ✅ **Success Response** - Shows:
  - Confirmation message
  - Action executed
  - Number of customer IDs
  - Request payload
  - Timestamp

- ❌ **Error Handling** - Shows:
  - Clear error messages
  - Problem description
  - Easy to dismiss/clear

- 🧹 **Clear Form Button** - Reset all fields

### Tab 2: TMS Customer Status
**Purpose:** View and monitor customer states and application status

**Includes:** All existing functionality:
- Dashboard with KPI tiles
- Customer transition states
- Trans-Begin state details
- Application status aggregation
- Pie charts with drill-down
- Search and filtering

### Backend Changes

**API Proxy Endpoint Updates** (`/api/proxy/fetch`):
- Now supports **POST requests** in addition to GET
- Handles both:
  - **GET requests** - Fetch customer states/app status
  - **POST requests** - Set customer actions
  
**Request Format:**
```json
{
  "url": "https://cnx-apigw-evian3.arubadev.cloud.hpe.com/tms/v1/set/action",
  "token": "your_bearer_token",
  "isPost": true,
  "postData": {
    "action": "Tran-Begin",
    "cids": ["id1", "id2", "id3"]
  }
}
```

**Response Format:**
```json
{
  "status": "success",
  "data": { ... }
}
```

### Supported Actions

**Actions for /set/action API:**
- `Tran-Begin` - Initiate transition
- `PE-Enable` - PE Enable state
- `T-Enable` - T Enable state
- `PE-Finalize` - PE Finalize state

### Customer ID Input Formats

**Both formats are supported:**

Format 1 - Line separated:
```
e106b3d0fb0111efb2cdda09530d43d0
948ef156c19511f08f342664b3b9825e
f1f2690afb0111efa54c0208abd2502c
```

Format 2 - Comma separated:
```
e106b3d0fb0111efb2cdda09530d43d0, 948ef156c19511f08f342664b3b9825e, f1f2690afb0111efa54c0208abd2502c
```

### UI Consistency
- ✅ Same HPE green branding (#01A982, #00856A)
- ✅ Consistent button styling and spacing
- ✅ Matching card design and shadows
- ✅ Uniform form inputs and labels
- ✅ Same responsive layout
- ✅ Smooth transitions between tabs

### Error Handling
- ✅ Input validation with helpful messages
- ✅ Network error handling
- ✅ API error responses displayed clearly
- ✅ Token validation before requests
- ✅ Field highlighting on errors

### Next Steps
Once you confirm this tabbed structure works as expected, we can add:
- Multi-select customer picker
- Bulk upload CSV/Excel support
- Request history/logging
- Retry mechanism
- Scheduled actions
- Action templates/presets
- Any other enhancements you need

---

## 🚀 How to Use

### Start the App
```bash
cd /home/pdanekula/tms_dashboard_python
./start_screen.sh
```

### Access the Dashboard
- **Local:** http://localhost:8080
- **Network:** http://10.9.91.22:8080

### Using Tab 1: TMS Customer Set
1. Select an action from dropdown
2. Enter your Bearer token
3. Paste customer IDs (line or comma-separated)
4. Click "Set Action"
5. View response/error message

### Using Tab 2: TMS Customer Status
- Use existing dashboard features as normal
- All previous functionality preserved

---

## ✅ Testing

**Test the Set Action:**
```bash
# Example POST request to test
curl -X POST http://10.9.91.22:8080/api/proxy/fetch \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://cnx-apigw-evian3.arubadev.cloud.hpe.com/tms/v1/set/action",
    "token": "your_token_here",
    "isPost": true,
    "postData": {
      "action": "Tran-Begin",
      "cids": ["test_cid_1", "test_cid_2"]
    }
  }'
```

---

**Version:** 2.0  
**Date:** January 9, 2026  
**Features:** Tabbed interface with customer set/status management
