# Cluster Selection Feature - Quick Start Guide

## 🎯 What's New

The TMS Dashboard now supports **cluster-based selection** instead of requiring manual API Base URL entry. Simply select your target cluster from a dropdown, and the application automatically configures the correct API endpoint.

---

## 📍 Where to Find the Cluster Selector

### 1. TMS Customer Set Page
- **Location:** Top section titled "⚙️ Set Customer State / Action"
- **Purpose:** Select cluster before setting customer actions
- **Auto-sets:** The `API Base URL` field in the Set Action configuration

### 2. TMS Customer Status Page  
- **Location:** "Fetch via API" tab under "Data Source Configuration"
- **Purpose:** Select cluster before fetching customer transition states
- **Auto-sets:** The `API Base URL` field with TMS endpoint path

### 3. Application Status Configuration
- **Location:** State detail view (after clicking on a state), under "📊 Application Status Configuration"
- **Purpose:** Select cluster before fetching application status
- **Auto-sets:** The `API Base URL` field for app status queries

---

## 🔗 Available Clusters

| Cluster | Base URL |
|---------|----------|
| **Evian3** | `https://cnx-apigw-evian3.arubadev.cloud.hpe.com` |
| **Brooke** | `https://cnx-apigw-brooke.arubadev.cloud.hpe.com` |
| **AquaV** | `https://cnx-apigw-aquav.arubadev.cloud.hpe.com` |
| **Aqua** | `https://cnx-apigw-aqua.arubadev.cloud.hpe.com` |
| **Jedi** | `https://cnx-apigw-jedi.arubadev.cloud.hpe.com` |

---

## 🚀 How to Use

### Basic Workflow

1. **Select a Cluster**
   ```
   Click on the cluster dropdown and select your target cluster
   Example: "Brooke"
   ```

2. **URL Auto-Population**
   ```
   The API Base URL field automatically updates with the correct endpoint
   Example: https://cnx-apigw-brooke.arubadev.cloud.hpe.com
   ```

3. **Proceed with Your Action**
   ```
   Continue with your workflow (Set Action, Fetch Status, etc.)
   All API requests will use the selected cluster's URL
   ```

### Example: Setting Customer State on Brooke Cluster

```
Step 1: Navigate to "⚙️ TMS Customer Set" tab
Step 2: In the "Cluster" dropdown, select "Brooke"
Step 3: Verify API Base URL shows: https://cnx-apigw-brooke.arubadev.cloud.hpe.com
Step 4: Enter your customer IDs
Step 5: Select an action (e.g., "Set Safe Mode")
Step 6: Click action button
Step 7: API request is sent to Brooke cluster automatically
```

### Example: Fetching Status on Evian3 Cluster

```
Step 1: Navigate to "📊 TMS Customer Status" tab
Step 2: In the "Cluster" dropdown, select "Evian3"
Step 3: Verify API Base URL shows: https://cnx-apigw-evian3.arubadev.cloud.hpe.com/tms/
Step 4: (Optional) Enter transition endpoint path
Step 5: (Optional) Enter bearer token if required
Step 6: Click "🔄 Fetch Transition States"
Step 7: Data is fetched from Evian3 cluster automatically
```

---

## 💾 Persistent Selection

Your cluster selection is **automatically saved** for each page:

- **TMS Customer Set:** Remembers your last selected cluster
- **TMS Customer Status:** Remembers your last selected cluster
- **App Status:** Remembers your last selected cluster

When you return to the dashboard, your previously selected cluster will be pre-selected.

---

## ✨ Key Features

✅ **Automatic URL Derivation**
- No more manual URL entry or typos
- Correct endpoint for each cluster

✅ **Visual Feedback**
- Blue border appears briefly when URL is auto-set
- Clear indication that selection is active

✅ **Persistent Selection**
- Your cluster choice is saved in browser
- Auto-loads on next visit

✅ **Independent Selection**
- Each page (Customer Set, Status, App Status) has its own cluster selection
- You can use different clusters for different features

✅ **Backward Compatible**
- Can still manually edit the URL if needed
- Existing workflow unchanged

---

## 🔧 Technical Details

### How It Works

1. **Cluster Mapping** (`CLUSTER_MAPPING` object)
   - Contains all available clusters and their URLs
   - Defines both base URL and TMS-specific endpoints

2. **Initialization** (`initializeClusterDropdowns()` function)
   - Populates all cluster dropdowns on page load
   - Restores previously selected cluster from localStorage

3. **Selection Handling**
   - On change event, lookup cluster configuration
   - Update corresponding URL field
   - Save selection to localStorage

### LocalStorage Keys

- `selectedCluster` - TMS Customer Set page
- `selectedStatusCluster` - TMS Customer Status page  
- `selectedAppStatusCluster` - App Status configuration

---

## ❓ FAQ

**Q: Can I manually edit the URL after selecting a cluster?**
A: Yes! The URL field is still editable. Select a cluster for convenience, then override if needed.

**Q: What if I need to use multiple clusters?**
A: Each page (Customer Set, Status, App Status) has independent cluster selection. You can use different clusters for different features.

**Q: Will my cluster selection persist after I close the browser?**
A: Yes! Each page remembers your last selected cluster until you clear browser data.

**Q: What if a cluster is offline?**
A: The cluster selection doesn't validate connectivity. If a cluster is unavailable, the API call will fail with a network error.

**Q: Can I add new clusters?**
A: Currently clusters are defined in code. Contact support to add new clusters to the dashboard.

---

## 📊 Supported Operations by Cluster

All clusters support the following TMS operations:

- ✅ Set Customer Action (Safe Mode, Normal Mode, Canary Mode, Standby Mode, Clear Errors)
- ✅ Fetch Transition States
- ✅ Get Application Status
- ✅ Fetch Aggregated Status

---

## 🔐 Security Notes

- URLs are derived client-side from configuration
- Bearer tokens are still required for API authentication
- No sensitive data is stored in localStorage
- All API requests go through server proxy for security

---

## 📝 Version History

- **v1.0** (January 13, 2026): Initial implementation
  - Added cluster selection dropdowns to 3 pages
  - Implemented auto-URL derivation
  - Added localStorage persistence

---

## 📞 Support

If you encounter issues with cluster selection:

1. Check that your cluster is available
2. Verify network connectivity
3. Ensure browser localStorage is enabled
4. Try clearing browser cache and reloading

For technical support, contact your system administrator.

---

**Happy clustering! 🎉**
