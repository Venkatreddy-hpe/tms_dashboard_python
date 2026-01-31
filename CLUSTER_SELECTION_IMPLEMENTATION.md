# Cluster-Based Selection Enhancement - Implementation Summary

**Date:** January 13, 2026  
**Status:** ✅ Complete

## Overview

Successfully enhanced the TMS Dashboard to support cluster-based selection instead of requiring manual API Base URL entry. Users can now select their target cluster from a dropdown, and the application automatically derives and configures the appropriate API Base URL.

---

## Changes Made

### 1. Cluster Configuration Mapping
**Location:** [index.html](index.html#L2035-L2065)

Created a comprehensive `CLUSTER_MAPPING` object containing all supported clusters:

```javascript
const CLUSTER_MAPPING = {
    'Evian3': {
        name: 'Evian3',
        baseUrl: 'https://cnx-apigw-evian3.arubadev.cloud.hpe.com',
        tmsUrl: 'https://cnx-apigw-evian3.arubadev.cloud.hpe.com/tms/'
    },
    'Brooke': {
        name: 'Brooke',
        baseUrl: 'https://cnx-apigw-brooke.arubadev.cloud.hpe.com',
        tmsUrl: 'https://cnx-apigw-brooke.arubadev.cloud.hpe.com/tms/'
    },
    'AquaV': {
        name: 'AquaV',
        baseUrl: 'https://cnx-apigw-aquav.arubadev.cloud.hpe.com',
        tmsUrl: 'https://cnx-apigw-aquav.arubadev.cloud.hpe.com/tms/'
    },
    'Aqua': {
        name: 'Aqua',
        baseUrl: 'https://cnx-apigw-aqua.arubadev.cloud.hpe.com',
        tmsUrl: 'https://cnx-apigw-aqua.arubadev.cloud.hpe.com/tms/'
    },
    'Jedi': {
        name: 'Jedi',
        baseUrl: 'https://cnx-apigw-jedi.arubadev.cloud.hpe.com',
        tmsUrl: 'https://cnx-apigw-jedi.arubadev.cloud.hpe.com/tms/'
    }
};
```

### 2. Cluster Initialization Function
**Location:** [index.html](index.html#L2067-L2191)

Implemented `initializeClusterDropdowns()` function that:
- Populates all three cluster dropdowns (Customer Set, Status, App Status)
- Loads previously selected cluster from localStorage
- Handles cluster selection change events
- Auto-derives and updates the corresponding API Base URL field
- Persists cluster selection for future sessions

**Key Features:**
- ✅ Auto-population of dropdown options
- ✅ LocalStorage persistence
- ✅ Visual feedback (blue border highlight) when URL is set
- ✅ Automatic 2-second border highlight fade

### 3. UI Updates

#### 3.1 TMS Customer Set Page
**Location:** [index.html](index.html#L1048-L1062)

Added cluster dropdown above the Customer IDs field:
```html
<div class="form-group">
    <label for="customerClusterSelect">Cluster</label>
    <select id="customerClusterSelect" style="width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 1em;"></select>
    <p class="hint-text">Select the target cluster. API Base URL will be automatically set.</p>
</div>
```

**Behavior:**
- Selecting a cluster auto-sets the API Base URL field (`setActionApiBase`)
- Uses cluster's `baseUrl` property

#### 3.2 TMS Customer Status Page
**Location:** [index.html](index.html#L1091-L1118)

Added cluster dropdown to the API Mode tab:
```html
<div class="form-group">
    <label>Cluster</label>
    <select id="statusClusterSelect" style="width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 1em;"></select>
    <p class="hint-text">Select the target cluster. API Base URL will be automatically set.</p>
</div>
```

**Behavior:**
- Selecting a cluster auto-sets the API Base URL field (`apiBaseUrl`)
- Uses cluster's `tmsUrl` property (includes `/tms/` path)

#### 3.3 Application Status Configuration
**Location:** [index.html](index.html#L1218-L1241)

Added cluster dropdown to the Application Status Configuration section:
```html
<div class="form-group" style="flex: 1; margin: 0; margin-right: 15px;">
    <label style="display: block; margin-bottom: 5px; font-weight: 500; color: #333; font-size: 0.9em;">Cluster</label>
    <select id="appStatusClusterSelect" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 8px; font-size: 0.95em;"></select>
    <p class="hint-text" style="margin: 5px 0 0 0; font-size: 0.85em;">Select cluster for auto URL</p>
</div>
```

**Behavior:**
- Selecting a cluster auto-sets the API Base URL field (`appStatusApiUrl`)
- Uses cluster's `baseUrl` property

### 4. JavaScript Initialization
**Location:** [index.html](index.html#L2192-L2207)

Added initialization call in DOMContentLoaded event:
```javascript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize cluster dropdowns
    initializeClusterDropdowns();
    // ... rest of initialization
});
```

---

## User Experience

### Before Enhancement
- Users had to manually enter API Base URLs
- URLs were prone to typos
- No clear indication which cluster was being used
- Had to remember URL format for each cluster

### After Enhancement
1. **User selects cluster from dropdown**
   - Clear list of available clusters (Evian3, Brooke, AquaV, Aqua, Jedi)
   - No need to remember URLs

2. **Application automatically sets API Base URL**
   - URL field auto-populates with correct endpoint
   - Visual feedback with blue highlight

3. **Selection persisted for next session**
   - Previously selected cluster is automatically loaded
   - Improves efficiency for users working with single cluster

4. **Same cluster selection across all pages**
   - LocalStorage keys: `selectedCluster`, `selectedStatusCluster`, `selectedAppStatusCluster`
   - Users can have different clusters per feature if needed

---

## Cluster Configuration Details

| Cluster | Base URL | TMS URL |
|---------|----------|---------|
| **Evian3** | https://cnx-apigw-evian3.arubadev.cloud.hpe.com | https://cnx-apigw-evian3.arubadev.cloud.hpe.com/tms/ |
| **Brooke** | https://cnx-apigw-brooke.arubadev.cloud.hpe.com | https://cnx-apigw-brooke.arubadev.cloud.hpe.com/tms/ |
| **AquaV** | https://cnx-apigw-aquav.arubadev.cloud.hpe.com | https://cnx-apigw-aquav.arubadev.cloud.hpe.com/tms/ |
| **Aqua** | https://cnx-apigw-aqua.arubadev.cloud.hpe.com | https://cnx-apigw-aqua.arubadev.cloud.hpe.com/tms/ |
| **Jedi** | https://cnx-apigw-jedi.arubadev.cloud.hpe.com | https://cnx-apigw-jedi.arubadev.cloud.hpe.com/tms/ |

---

## Implementation Details

### Cluster Mapping Usage

**Customer Set Page:**
- Uses `CLUSTER_MAPPING[clusterName].baseUrl`
- Example: `https://cnx-apigw-evian3.arubadev.cloud.hpe.com`

**Customer Status Page:**
- Uses `CLUSTER_MAPPING[clusterName].tmsUrl`
- Example: `https://cnx-apigw-evian3.arubadev.cloud.hpe.com/tms/`

**App Status Configuration:**
- Uses `CLUSTER_MAPPING[clusterName].baseUrl`
- Example: `https://cnx-apigw-evian3.arubadev.cloud.hpe.com`

### LocalStorage Keys

The application persists cluster selections:
- `selectedCluster` - Cluster for Customer Set page
- `selectedStatusCluster` - Cluster for Customer Status page
- `selectedAppStatusCluster` - Cluster for App Status section

### Event Handling

Each dropdown has a `change` event listener that:
1. Retrieves the selected cluster
2. Validates it exists in CLUSTER_MAPPING
3. Gets the appropriate URL (baseUrl or tmsUrl)
4. Updates the corresponding input field
5. Applies visual feedback (blue border)
6. Persists selection to localStorage

---

## Testing

### Manual Testing Steps

1. **Load the dashboard**
   - Navigate to http://localhost:8080
   - All three cluster dropdowns should be populated with 5 options each

2. **Test TMS Customer Set**
   - Select "Evian3" from cluster dropdown
   - Verify API Base URL field shows: `https://cnx-apigw-evian3.arubadev.cloud.hpe.com`
   - Select "Brooke" from cluster dropdown
   - Verify API Base URL field shows: `https://cnx-apigw-brooke.arubadev.cloud.hpe.com`

3. **Test TMS Customer Status**
   - Select "AquaV" from cluster dropdown
   - Verify API Base URL field shows: `https://cnx-apigw-aquav.arubadev.cloud.hpe.com/tms/`
   - Select "Aqua" from cluster dropdown
   - Verify API Base URL field shows: `https://cnx-apigw-aqua.arubadev.cloud.hpe.com/tms/`

4. **Test App Status**
   - Navigate to a state detail view (click on "Tran-Begin" etc)
   - Select "Jedi" from cluster dropdown
   - Verify API Base URL field shows: `https://cnx-apigw-jedi.arubadev.cloud.hpe.com`

5. **Test Persistence**
   - Select a cluster on TMS Customer Set page
   - Refresh the browser
   - Verify the same cluster is still selected

6. **Test API Requests**
   - Select a cluster
   - Execute a Set Action or Status fetch
   - Monitor network requests to verify correct cluster URL is used

---

## Files Modified

- **[index.html](index.html)** - Complete cluster mapping implementation
  - Lines 1048-1062: Customer Set cluster dropdown UI
  - Lines 1091-1118: Status page cluster dropdown UI
  - Lines 1218-1241: App Status cluster dropdown UI
  - Lines 2035-2191: JavaScript cluster configuration and initialization

---

## Backward Compatibility

✅ **Fully backward compatible**
- Manual URL entry is still supported (users can override auto-set URLs)
- Existing API requests continue to work
- No breaking changes to existing functionality

---

## Future Enhancements (Optional)

1. **Add cluster configuration API endpoint**
   - Allow clusters to be managed server-side
   - Support dynamic cluster addition/removal

2. **Cluster-specific features**
   - Display cluster health status
   - Show cluster-specific documentation links

3. **Multi-cluster operations**
   - Simultaneously apply actions across multiple clusters
   - Cluster comparison views

4. **Cluster presets**
   - Save favorite cluster combinations
   - Quick-switch between commonly used clusters

---

## Summary

The cluster-based selection enhancement has been successfully implemented across all three major features of the TMS Dashboard:

1. ✅ TMS Customer Set page
2. ✅ TMS Customer Status page
3. ✅ Application Status Configuration

Users can now easily select their target cluster from a dropdown instead of manually entering API Base URLs. The application automatically derives the correct URL based on the selected cluster, improving user experience and reducing errors.

**Status:** Ready for deployment
