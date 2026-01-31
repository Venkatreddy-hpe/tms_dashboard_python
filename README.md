# TMS Dashboard - Python Flask Application

A lightweight web dashboard for monitoring TMS (Transition Management System) customer states and application statuses with HPE branding.

## 🚀 Quick Start

### Start the Application
```bash
cd /home/pdanekula/tms_dashboard_python
python3 app.py
```

The server will start on port **8080** and be accessible from:
- **Local:** `http://localhost:8080`
- **Network:** `http://10.9.91.22:8080` (your IP address)

### Stop the Application
Press `Ctrl + C` in the terminal where the app is running.

---

## ✅ Check If App Is Running

### Method 1: Check Process
```bash
ps aux | grep "python3.*app.py" | grep -v grep
```
- ✅ **Expected:** Shows a running Python process
- ❌ **If empty:** App is not running

### Method 2: Check Port
```bash
netstat -tuln | grep 8080
```
- ✅ **Expected:** Shows port 8080 in LISTEN state
- ❌ **If empty:** App is not running or port is blocked

### Method 3: Test with curl
```bash
curl http://localhost:8080/health
```
- ✅ **Expected:** `{"status":"healthy","service":"TMS Dashboard"}`
- ❌ **If error:** App is not running or not responding

### Method 4: Test in Browser
Open: `http://localhost:8080`
- ✅ **Expected:** Dashboard loads successfully
- ❌ **If error:** See troubleshooting section below

---

## 🔧 Troubleshooting - Page Not Accessible

### 1. Check if server is running
```bash
ps aux | grep "python3.*app.py" | grep -v grep
```
**Solution:** If not running, start with `python3 app.py`

### 2. Check firewall (accessing from another machine)
```bash
# Check firewall status
sudo ufw status

# Allow port 8080 if blocked
sudo ufw allow 8080/tcp
```

### 3. Verify your IP address
```bash
# Get your current IP
hostname -I | awk '{print $1}'
```
**Solution:** Use the correct IP address in the URL

### 4. Check if port 8080 is already in use
```bash
sudo lsof -i :8080
```
**Solution:** Kill the process using port 8080:
```bash
# Find PID from above command, then:
kill -9 <PID>
```
Or change port in app.py (line ~131):
```python
port = int(os.environ.get('PORT', 8081))
```

### 5. Network connectivity test
```bash
# From another machine, ping the server
ping 10.9.91.22

# Check if port is reachable
telnet 10.9.91.22 8080
```
**Solution:** Ensure machines are on the same network

### 6. Check server logs
Look at the terminal where `python3 app.py` is running for error messages.

**Common errors:**
- `Address already in use` → Port 8080 is taken
- `Permission denied` → Use a port > 1024 or run with sudo
- `Module not found` → Install missing dependencies

---

## ✨ Features

### Dashboard View
- View all customer transition states
- Filter by state (tran-begin, pe-enable, e-enable, etc.)
- Search by Customer ID
- Sort columns (Customer ID, State, Action Code)
- Real-time data from HPE API
- Color-coded status badges

### Trans-Begin State Details
- Detailed customer list for Trans-Begin state
- Application status aggregation across customers
- Interactive pie charts (green=passed, red=failed)
- Drill-down to see which customers passed/failed per app
- Search and filter functionality
- Scrollable tables with sticky headers

### Aggregated App Status
- View app status across multiple customers
- Visual representation with Chart.js pie charts
- Click charts to see detailed customer lists
- Status categories: Ready, Failure, Transiting, Inapplicable, Unknown

---

## 📋 Requirements

### Python Dependencies
```bash
pip3 install flask flask-cors requests
```

Or install from requirements file:
```bash
pip3 install -r requirements.txt
```

### System Requirements
- Python 3.6+
- Network connectivity for API calls
- Port 8080 available

---

## 🔑 API Configuration

### Required Tokens
The dashboard needs Bearer tokens to access HPE APIs:

1. **Main API Token** - For transition state data
   - Endpoint: `https://cnx-apigw-evian3.arubadev.cloud.hpe.com/tms/v1/get/action?cid=ALL`
   
2. **App Status Token** - For application status data
   - Endpoint: `https://cnx-apigw-evian3.arubadev.cloud.hpe.com/tms/v1/get/appstatus?app=ALL&cid=`

### How to Use Tokens
1. Open the dashboard in browser
2. Enter your Bearer token in the respective input fields
3. Tokens are stored in browser's localStorage
4. Click "Load Data" or "View APP Status" to fetch data

---

## 🌐 Network Access

### Local Access (Same Machine)
```
http://localhost:8080
```

### Network Access (From Other Machines)
```
http://10.9.91.22:8080
```

**Requirements:**
- Server configured with `host='0.0.0.0'` ✅ (already done)
- Port 8080 open in firewall
- Machines on same network or VPN

---

## 📁 Project Structure

```
tms_dashboard_python/
├── app.py                 # Flask backend server
├── requirements.txt       # Python dependencies
├── README.md             # This documentation
├── start_screen.sh        # Helper script to start app in screen
├── stop_screen.sh         # Helper script to stop screen session
└── templates/
    └── index.html        # Dashboard frontend (HTML/CSS/JS)
```

---

## 🐛 Common Issues

### Issue: "Token expired or invalid"
**Solution:** Enter a new valid Bearer token in the input field

### Issue: "CORS error" in browser console
**Solution:** The app includes Flask-CORS for cross-origin support

### Issue: Empty data or "Loading..." forever
**Solutions:**
1. Check Bearer token is valid and entered correctly
2. Verify API endpoints are accessible
3. Check browser console for errors (F12)
4. Verify network connectivity to HPE APIs
5. Check server terminal for proxy errors

### Issue: Can't access from another machine
**Solutions:**
1. Verify server is running with `0.0.0.0` (already configured ✅)
2. Check firewall allows port 8080: `sudo ufw allow 8080/tcp`
3. Ensure machines are on same network
4. Test connectivity: `ping 10.9.91.22`
5. Test port: `telnet 10.9.91.22 8080`

### Issue: Screen session not starting
**Solutions:**
1. Check if screen is installed: `which screen`
2. Install if needed: `sudo apt-get install screen`
3. Check if session already exists: `screen -ls`
4. Kill existing session if needed: `screen -X -S tms_dashboard quit`

### Issue: Lost connection to screen session
**Solution:** Just reattach with `screen -r tms_dashboard`

---

## 🔒 Security Notes

### Current Setup (Development/Internal Network)
- ⚠️ No authentication - anyone with network access can view data
- ⚠️ Tokens stored in browser localStorage
- ✅ Suitable for internal/trusted networks only

### For Production Use
Consider adding:
- User authentication (login/password)
- HTTPS/SSL certificates
- Token encryption
- Rate limiting
- IP whitelisting
- Audit logging

---

## 🛠 Maintenance

### Backup Current Version
```bash
# Create timestamped backup
cp -r /home/pdanekula/tms_dashboard_python \
      /home/pdanekula/tms_dashboard_python_backup_$(date +%Y%m%d_%H%M%S)
```

### Update Dependencies
```bash
pip3 install --upgrade flask flask-cors requests
```

### Run in Background with Logs
```bash
# Start in background
nohup python3 app.py > server.log 2>&1 &

# View logs
tail -f server.log

# Stop background server
pkill -f "python3 app.py"
```

### Run with Screen (Recommended for Background)

Screen allows you to run the app in a detached terminal session that persists even after logout.

#### Using Helper Scripts (Easy Way)

**Start the app in screen:**
```bash
cd /home/pdanekula/tms_dashboard_python
./start_screen.sh
```

**Stop the app:**
```bash
cd /home/pdanekula/tms_dashboard_python
./stop_screen.sh
```

#### Manual Screen Commands

**Start screen session:**
```bash
screen -S tms_dashboard
cd /home/pdanekula/tms_dashboard_python
python3 app.py
# Press Ctrl+A then D to detach
```

**View running sessions:**
```bash
screen -ls
```

**Attach to existing session (view logs):**
```bash
screen -r tms_dashboard
# Press Ctrl+A then D to detach again
```

**Kill screen session:**
```bash
screen -X -S tms_dashboard quit
```

#### Screen Benefits
- ✅ App continues running after logout/disconnect
- ✅ Can attach anytime to view live logs
- ✅ Easy to manage with provided scripts
- ✅ No log file needed - see output in real-time
- ✅ Simple start/stop with helper scripts

#### Screen Quick Tips
- **Detach shortcut:** `Ctrl+A` then `D`
- **Check if running:** `screen -ls` or `curl http://localhost:8080/health`
- **Survives SSH disconnect:** Yes ✅
- **Auto-restart on crash:** No (use systemd for that)

---

## 🎯 Quick Reference

| Action | Command |
|--------|---------|
| Start server (foreground) | `python3 app.py` |
| Start server (screen) | `./start_screen.sh` |
| Stop server (foreground) | `Ctrl + C` |
| Stop server (screen) | `./stop_screen.sh` |
| View screen session | `screen -r tms_dashboard` |
| Detach from screen | `Ctrl+A` then `D` |
| Check if running | `ps aux \| grep "python3.*app.py"` or `screen -ls` |
| Check port | `netstat -tuln \| grep 8080` |
| Get IP address | `hostname -I \| awk '{print $1}'` |
| Test health | `curl http://localhost:8080/health` |
| Allow firewall | `sudo ufw allow 8080/tcp` |
| View background logs | `tail -f server.log` (nohup) or `screen -r tms_dashboard` |

---

## 📞 Helpful Commands

**Check Python version:**
```bash
python3 --version
```

**Check installed packages:**
```bash
pip3 list | grep -E "flask|requests|cors"
```

**Monitor port in real-time:**
```bash
watch -n 2 'netstat -tuln | grep 8080'
```

**Test API health:**
```bash
# Local
curl http://localhost:8080/health

# Network (from another machine)
curl http://10.9.91.22:8080/health
```

---

## 📡 API Endpoints

### Client-facing
- `GET /` - Dashboard UI
- `GET /api/transition/state` - Get demo transition data
- `GET /api/appstatus/<customer_id>` - Get app status for customer
- `GET /health` - Health check

### Internal
- `POST /api/proxy/fetch` - Proxy external API requests (avoids CORS)

---

## 📝 Recent Updates

### January 2026
- ✅ HPE green branding applied throughout
- ✅ Enhanced Trans-Begin page with improved visual consistency
- ✅ Added token validation before API calls
- ✅ Improved app status configuration section with labels
- ✅ Added customer drill-down with enhanced styling
- ✅ Implemented column sorting functionality
- ✅ Added search and filter capabilities
- ✅ Network access configuration (`0.0.0.0`) for team sharing
- ✅ Comprehensive README documentation

---

**Version:** 1.0  
**Last Updated:** January 9, 2026  
**Port:** 8080  
**Host:** 0.0.0.0 (accepts connections from any IP on the network)  
**Access:** `http://10.9.91.22:8080`

