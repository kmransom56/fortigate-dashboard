# Network MCP Server - Development Guide

## 🔧 **Issue Resolution Summary**
**Problem:** Missing `http-proxy-middleware` dependency causing Node.js server crashes
**Solution:** Created simplified proxy server with no external dependencies

## 📁 **Project Structure**
```
network-device-mcp-server/
├── server_noc_simple.js      # Original server (needs npm install)
├── server_noc_fixed.js       # Fixed server (no external deps) ✅
├── rest_api_server.py         # Python Flask backend
├── package.json               # Updated with dependencies
├── start-fixed-servers.bat    # Easy startup ✅
├── test-server-fix.bat        # Connectivity tests ✅
├── web/                       # Frontend assets
├── src/                       # MCP server source
└── requirements.txt           # Python dependencies
```

## 🚀 **Quick Start Commands**

### Start Servers (Easy Way)
```bash
# Windows: Double-click this file
start-fixed-servers.bat

# Manual way:
# Terminal 1:
python rest_api_server.py

# Terminal 2:  
node server_noc_fixed.js
```

### Test Everything
```bash
# Windows: Double-click this file
test-server-fix.bat

# Manual API test:
curl http://localhost:5001/api/brands
curl http://localhost:5001/health
```

## 🌐 **Access Points**
- **Main Interface:** http://localhost:5001
- **API Backend:** http://localhost:5000
- **Health Check:** http://localhost:5001/health
- **API Docs:** http://localhost:5000/api

## 🔍 **Common Issues & Fixes**

### Issue: "Module not found: http-proxy-middleware"
**Fix:** Use `server_noc_fixed.js` instead of `server_noc_simple.js`

### Issue: "Backend service unavailable"
**Fix:** Start Python server first: `python rest_api_server.py`

### Issue: Port already in use
**Fix:** Kill existing processes:
```powershell
# Kill processes on ports
netstat -ano | findstr :5000
netstat -ano | findstr :5001
taskkill /PID <process_id> /F
```

## 🎯 **Development Workflow**

### For Code Changes:
1. Edit Python code → Restart `rest_api_server.py`
2. Edit Node.js code → Restart `server_noc_fixed.js`
3. Edit web files → Just refresh browser

### For New Dependencies:
1. Python: Add to `requirements.txt` → `pip install -r requirements.txt`
2. Node.js: Add to `package.json` → `npm install`

### For Testing:
1. Run `test-server-fix.bat` for connectivity
2. Use browser dev tools for frontend debugging
3. Check terminal outputs for backend errors

## 📋 **Backup & Restore**

### Before Changes:
```bash
# Backup working version
git add . && git commit -m "Working version before changes"
```

### If Something Breaks:
```bash
# Quick restore
git checkout HEAD~1
# OR use the backup files:
# network-device-mcp-server-backup.zip
```

## 🏆 **Production Checklist**
- ✅ Both servers start without errors
- ✅ API endpoints respond correctly  
- ✅ Web interface loads completely
- ✅ Voice controls work (if browser supports)
- ✅ Database connections established
- ✅ FortiManager integration active

## 📞 **Need Help?**
1. Check server logs in terminal windows
2. Run `test-server-fix.bat` for diagnostics
3. Verify all environment variables in `.env`
4. Test individual API endpoints manually

**🎉 Your voice-enabled AI network management platform is production-ready!**