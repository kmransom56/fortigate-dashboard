from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

from app.api import fortigate  # your existing fortigate routes
from app.services.fortigate_service import (
    get_interfaces,
    get_cloud_status,
)  # to get interfaces and cloud status for dashboard
from app.services.fortiswitch_service import (
    get_fortiswitches,
)  # to get FortiSwitch information


# Helper to aggregate device details for dashboard
def get_all_device_details():
    switches_data = get_fortiswitches()
    # If switches_data is a dict, extract the list
    if isinstance(switches_data, dict) and "switches" in switches_data:
        switches = switches_data["switches"]
    else:
        switches = switches_data
    devices = []
    for switch in switches:
        if not isinstance(switch, dict):
            continue  # skip if not a dict (e.g., string or other type)
        for port in switch.get("ports", []):
            for dev in port.get("connected_devices", []):
                # Add switch and port context to device
                dev_copy = dev.copy()
                dev_copy["switch_serial"] = switch.get("serial")
                dev_copy["switch_name"] = switch.get("name")
                dev_copy["port_name"] = port.get("name")
                # If icon_path not present, try to enrich from DB
                if not dev_copy.get("icon_path"):
                    from app.utils.icon_db import get_icon

                    icon_info = get_icon(manufacturer=dev_copy.get("manufacturer"))
                    if not icon_info:
                        icon_info = get_icon(device_type=dev_copy.get("device_type"))
                    if icon_info:
                        dev_copy["icon_path"] = icon_info["icon_path"]
                        dev_copy["icon_title"] = icon_info["title"]
                devices.append(dev_copy)
    return devices


app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="app/templates")

# Include Fortigate router
app.include_router(fortigate.router)


# 🏠 Route for Home "/"
@app.get("/", response_class=HTMLResponse)
async def read_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# 📊 Route for Dashboard "/dashboard"
@app.get("/dashboard", response_class=HTMLResponse)
async def show_dashboard(request: Request):
    interfaces = get_interfaces()
    device_details = get_all_device_details()
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "interfaces": interfaces,
            "device_details": device_details,
        },
    )


# API endpoint for cloud status
@app.get("/api/cloud_status")
async def api_cloud_status():
    status = get_cloud_status()
    return {"status": status}


# 🔄 Route for FortiSwitch Dashboard "/switches"
@app.get("/switches", response_class=HTMLResponse)
async def switches_page(request: Request):
    switches = get_fortiswitches()  # Pulls live data
    return templates.TemplateResponse(
        "switches.html", {"request": request, "switches": switches}
    )


# 🌐 Route for Network Topology "/topology"
@app.get("/topology", response_class=HTMLResponse)
async def topology_page(request: Request):
    return templates.TemplateResponse("topology.html", {"request": request})


# 📡 API endpoint for topology data
@app.get("/api/topology_data")
async def api_topology_data():
    """
    Returns real network topology data for the Security Fabric-style visualization
    """
    from app.services.fortigate_service import get_interfaces
    
    # Get real data from your existing services
    interfaces = get_interfaces()
    switches_data = get_fortiswitches()
    device_details = get_all_device_details()  # This has enriched manufacturer data!
    
    # Transform data into topology format
    topology_data = {
        "devices": [],
        "connections": []
    }
    
    # Add FortiGate device
    topology_data["devices"].append({
        "id": "fortigate_main",
        "type": "fortigate",
        "name": "FortiGate-Main",
        "ip": "192.168.0.254",
        "status": "online",
        "risk": "low",
        "position": {"x": 400, "y": 100},
        "details": {
            "model": "FortiGate",
            "interfaces": len(interfaces) if interfaces else 0,
            "status": "Active"
        }
    })
    
    # Process FortiSwitch data
    if isinstance(switches_data, dict) and "switches" in switches_data:
        switches = switches_data["switches"]
    else:
        switches = switches_data if switches_data else []
    
    switch_y = 300
    for i, switch in enumerate(switches):
        if isinstance(switch, dict):
            switch_id = f"switch_{i}"
            
            # Determine switch status and risk
            switch_status = "online" if switch.get("status") == "Authorized" else "warning"
            switch_risk = "low" if switch.get("status") == "Authorized" else "medium"
            
            topology_data["devices"].append({
                "id": switch_id,
                "type": "fortiswitch",
                "name": switch.get("serial", f"FortiSwitch-{i}"),  # Use serial as name for clarity
                "ip": switch.get("mgmt_ip", "N/A"),
                "status": switch_status,
                "risk": switch_risk,
                "position": {"x": 400, "y": switch_y},
                "details": {
                    "serial": switch.get("serial", "Unknown"),
                    "model": switch.get("model", "FortiSwitch"),
                    "ports": len(switch.get("ports", [])),
                    "status": switch.get("status", "Unknown"),
                    "connectedDevices": len([d for d in device_details if d.get("switch_serial") == switch.get("serial")])
                }
            })
            
            # Add connection from FortiGate to FortiSwitch
            topology_data["connections"].append({
                "from": "fortigate_main",
                "to": switch_id
            })
            
            switch_y += 200
    
    # Now use the enriched device_details for connected devices
    device_x_start = 150
    device_y = 450
    device_spacing = 120
    device_count = 0
    
    for device in device_details:
        if not device:
            continue
            
        device_id = f"device_{device_count}"
        
        # Get enriched device information
        manufacturer = device.get("manufacturer", "Unknown Manufacturer")
        device_name = device.get("hostname") or manufacturer or "Unknown Device"
        
        # Determine device type based on manufacturer or other clues
        device_type = "endpoint"
        if "server" in device_name.lower():
            device_type = "server"
        elif manufacturer in ["Microsoft Corporation", "Apple Inc."]:
            device_type = "endpoint"
        elif "router" in device_name.lower() or "gateway" in device_name.lower():
            device_type = "server"
        
        # Determine risk level based on manufacturer identification
        risk_level = "low"
        if manufacturer == "Unknown Manufacturer" or not manufacturer:
            risk_level = "high"  # Unknown devices are risky
        elif not device.get("hostname"):
            risk_level = "medium"  # No hostname but known manufacturer
        
        # Create a cleaner device name
        if manufacturer and manufacturer != "Unknown Manufacturer":
            if device.get("hostname"):
                display_name = device.get("hostname")
            else:
                # Use manufacturer for display if no hostname
                display_name = manufacturer.replace(" Corporation", "").replace(" Inc.", "").replace(" Inc", "")
        else:
            display_name = f"Device {device.get('mac', '')[-8:]}" if device.get('mac') else "Unknown Device"
        
        # Ensure name isn't too long
        if len(display_name) > 15:
            display_name = display_name[:12] + "..."
        
        topology_data["devices"].append({
            "id": device_id,
            "type": device_type,
            "name": display_name,
            "ip": device.get("ip", "N/A"),
            "mac": device.get("mac", "N/A"),
            "status": "online",
            "risk": risk_level,
            "position": {
                "x": device_x_start + (device_count * device_spacing),
                "y": device_y
            },
            "details": {
                "manufacturer": manufacturer,
                "port": device.get("port_name", "Unknown"),
                "switch": device.get("switch_name", "Unknown"),
                "lastSeen": "Active",
                "mac": device.get("mac", "N/A"),
                "hostname": device.get("hostname", "N/A"),
                "iconPath": device.get("icon_path", ""),
                "iconTitle": device.get("icon_title", "")
            }
        })
        
        # Connect device to its switch
        switch_serial = device.get("switch_serial")
        if switch_serial:
            # Find the switch this device is connected to
            for j, switch in enumerate(switches):
                if isinstance(switch, dict) and switch.get("serial") == switch_serial:
                    switch_id = f"switch_{j}"
                    topology_data["connections"].append({
                        "from": switch_id,
                        "to": device_id
                    })
                    break
        
        device_count += 1
    
    return topology_data
