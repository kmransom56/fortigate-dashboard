# 🚀 Quick Start Guide - Network Device Management

## For Your Coworkers (No Technical Knowledge Required!)

### Step 1: Get Docker Desktop
1. Go to https://www.docker.com/products/docker-desktop
2. Download Docker Desktop for your operating system
3. Install it and start it up
4. You should see a whale 🐳 icon in your system tray

### Step 2: Get the Code
1. Download this repository (ask your IT team for the ZIP file, or clone it)
2. Extract it to a folder like `Desktop/network-device-management`

### Step 3: One-Click Start! 

**Windows Users:**
- Double-click `ONE-CLICK-START.bat`
- Wait for setup (takes 2-3 minutes first time)
- Your browser will open automatically to the dashboard

**Mac/Linux Users:**
- Open Terminal in the project folder
- Type: `./one-click-start.sh`
- Wait for setup (takes 2-3 minutes first time)
- Your browser will open automatically to the dashboard

### Step 4: You're Done! 🎉

You should now see:
- **Dashboard**: http://localhost:12000 (your main interface)
- **API Docs**: http://localhost:8000/docs (for developers)

## What You'll See

### Main Dashboard Features:
- 📊 **Total Device Count**: Shows all managed network devices
- 🏢 **Brand Breakdown**: BWW, ARBYS, SONIC locations
- ✅ **Health Status**: Green = good, Red = needs attention
- 🔄 **Auto-Refresh**: Updates every 30 seconds

### Navigation:
- **Dashboard**: Overview of all devices
- **Brands**: Detailed view per restaurant brand
- **Devices**: Individual device management
- **Reports**: Export data and generate reports

## Stopping the System

**Windows**: Double-click `STOP-DOCKER.bat`
**Mac/Linux**: Press `Ctrl+C` in the terminal, or run `docker compose down`

## Troubleshooting

### "Nothing happens when I click the .bat file"
- Make sure Docker Desktop is running (look for the whale icon)
- Right-click the .bat file and "Run as Administrator"

### "Port already in use" error
- Close any other applications using ports 8000 or 12000
- Or restart your computer and try again

### "Can't access http://localhost:12000"
- Wait 3-4 minutes for full startup
- Check that Docker Desktop shows green containers
- Try refreshing your browser

### "Docker is not installed"
- Download and install Docker Desktop from the official website
- Restart your computer after installation
- Make sure Docker Desktop is running before starting

## Getting Help

1. **First**: Try stopping (`STOP-DOCKER.bat`) and starting again (`ONE-CLICK-START.bat`)
2. **Still issues?**: Take a screenshot of any error messages
3. **Contact**: Your IT team with the screenshot

## Data and Security

- ✅ **All data stays on your computer** - nothing is sent to external servers
- ✅ **Passwords are encrypted** in the database
- ✅ **Network credentials** are stored securely in configuration files
- ✅ **Auto-backup** of important data every night

## Daily Use

1. **Morning**: Start with `ONE-CLICK-START.bat`
2. **Monitor**: Check dashboard at http://localhost:12000
3. **Evening**: Stop with `STOP-DOCKER.bat` (or leave running)

**That's it!** The system is designed to be as simple as possible while providing powerful network monitoring capabilities.

---

*Need help? Contact your system administrator with this guide and any error messages.*