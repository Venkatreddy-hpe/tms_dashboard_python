# TMS Dashboard - Multiple CID Input Methods Quick Reference

## What's New?

The **Prod Customer Data** section now supports three ways to provide Customer IDs:
1. **API Fetch** (existing)
2. **CSV Upload** (new)
3. **Manual Entry** (new)

## Which Method Should I Use?

| Method | Best For | Requirements |
|--------|----------|--------------|
| **API** | Automated, large datasets | Data Source URL + Bearer Token |
| **CSV** | Batch imports from files | .csv file with one CID per row |
| **Manual** | Quick testing, small lists | Copy-paste or type CIDs |

## Step-by-Step Usage

### Method 1: API (No Changes - Works as Before)
```
1. Enter Data Source URL
2. Enter Bearer Token
3. Select Cluster and Device Selection
4. Click "Run"
```

### Method 2: CSV Upload
```
1. Prepare .csv file:
   - One customer ID per row
   - Optional header row (auto-skipped)
   - Examples: cust_id, customer_id, id

2. Click file input → Select .csv file
3. Select Cluster and Device Selection  
4. Click "Run"
```

**CSV Example File**:
```
cust_id
ACME-001
ACME-002
ACME-003
```

### Method 3: Manual Entry
```
1. Click text area under "Manual Entry"
2. Paste or type customer IDs
   - One per line, OR
   - Comma-separated on one line
3. Select Cluster and Device Selection
4. Click "Run"
```

**Manual Entry Examples**:

Option A - Line separated:
```
ACME-001
ACME-002
ACME-003
```

Option B - Comma separated:
```
ACME-001, ACME-002, ACME-003
```

## Important Rules

### Priority Order
If you provide multiple methods, the system uses them in this order:
1. **API** (highest priority)
2. **CSV** (if no API)
3. **Manual Entry** (if no API or CSV)

⚠️ Example: If you fill in all three, only the API will be used.

### What Gets Normalized
The system automatically:
- ✓ Removes whitespace (leading/trailing)
- ✓ Removes duplicate IDs
- ✓ Filters out empty lines
- ✓ Skips header rows (cust_id, customer_id, id)

### Validation
Before ingestion, the system checks:
- ✓ Cluster is selected
- ✓ Device Selection is selected
- ✓ At least one CID source is provided
- ✓ At least one valid CID exists after processing

## Data Storage

All three methods store data identically:
- Stored by: (Cluster, Device Selection) combination
- Overwrites previous data for same cluster/device
- Can be used immediately for batch generation
- No changes to existing workflows

## Results Display

After successful ingestion, you'll see:
```
AP-APAC / AOS10 Large → Total: 1,234 customers
```

If you stored previous data, click **"Check Stored"** to see what's currently saved.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Please provide Customer IDs..." | Select at least one input method (API, CSV, or Manual) |
| "No valid customer IDs found" | Check your input - ensure at least one valid CID exists |
| "Cluster is required" | Select a cluster from the dropdown |
| "Device Selection is required" | Select a device type from the dropdown |
| CSV not importing | Check file has one CID per row; remove special characters |
| Manual entry not working | Ensure each CID is on a new line or separated by commas |

## FAQ

**Q: Can I mix CSV and manual entry?**
A: No - choose one method per run. If you need both, run twice.

**Q: What happens to old data?**
A: New data overwrites old data for the same cluster/device combination.

**Q: Are the CIDs case-sensitive?**
A: They are preserved as-is but duplicates are detected exactly.

**Q: Can I export the stored CIDs?**
A: Not yet - feature coming soon. Contact admin for custom exports.

**Q: How many CIDs can I upload?**
A: System tested with thousands. No hard limit, but very large files may take time.

## Need Help?

- Check the helper text under "Customer ID Input Options"
- Review the examples above
- Contact your system administrator for custom integrations

---
**Last Updated**: January 27, 2026
