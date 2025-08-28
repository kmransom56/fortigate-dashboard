from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import os
from app.services import eraser_service
from app.utils.icon_db import seed_default_icons
from fastapi.middleware.cors import CORSMiddleware

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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
from pathlib import Path
STATIC_DIR = str((Path(__file__).parent / "static").resolve())
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Set up templates
templates = Jinja2Templates(directory="app/templates")

# Include Fortigate router
app.include_router(fortigate.router)


# Seed icons at startup
seed_default_icons()

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

# 🌐 Route for 3D Network Topology "/topology-3d"
@app.get("/topology-3d", response_class=HTMLResponse)
async def topology_3d_page(request: Request):
    return templates.TemplateResponse("topology_3d.html", {"request": request})


# 📡 API endpoint for topology data

@app.get("/api/topology_data")
async def api_topology_data():
    """
    Returns real network topology data for the Security Fabric-style visualization
    """
    import logging
    logger = logging.getLogger("api_topology_data")
    logger.info("START /api/topology_data endpoint")

    if os.getenv("MOCK_TOPOLOGY", "false").lower() == "true":
        return {
            "devices": [
                {"id": "fortigate_main", "type": "fortigate", "name": "FortiGate-Main", "ip": "192.168.0.254", "status": "online", "risk": "low", "position": {"x": 0, "y": 0, "z": 0}},
                {"id": "switch_1", "type": "fortiswitch", "name": "FSW-1", "ip": "192.168.0.253", "status": "online", "risk": "low", "position": {"x": 60, "y": 10, "z": -20}},
                {"id": "device_1", "type": "endpoint", "name": "Office-PC", "ip": "192.168.0.10", "status": "online", "risk": "medium", "position": {"x": 120, "y": -20, "z": 40}},
                {"id": "server_1", "type": "server", "name": "App-Server", "ip": "192.168.0.20", "status": "online", "risk": "low", "position": {"x": -80, "y": 30, "z": 50}}
            ],
            "connections": [
                {"from": "fortigate_main", "to": "switch_1"},
                {"from": "switch_1", "to": "device_1"},
                {"from": "fortigate_main", "to": "server_1"}
            ]
        }

    from app.services.fortigate_service import get_interfaces

    # Fetch data with aggressive timeouts to avoid UI hanging
    from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

    interfaces = {}
    switches_data = []
    device_details = []

    try:
        with ThreadPoolExecutor(max_workers=3) as executor:
            fut_if = executor.submit(get_interfaces)
            fut_sw = executor.submit(get_fortiswitches)
            fut_dev = executor.submit(get_all_device_details)

            try:
                interfaces = fut_if.result(timeout=4)
            except FuturesTimeout:
                logger.warning("get_interfaces() timed out; continuing with 0 interfaces")
            except Exception as e:
                logger.warning(f"get_interfaces() failed: {e}")

            try:
                switches_data = fut_sw.result(timeout=5)
            except FuturesTimeout:
                logger.warning("get_fortiswitches() timed out; continuing with no switches")
            except Exception as e:
                logger.warning(f"get_fortiswitches() failed: {e}")

            try:
                device_details = fut_dev.result(timeout=5)
            except FuturesTimeout:
                logger.warning("get_all_device_details() timed out; continuing with 0 devices")
            except Exception as e:
                logger.warning(f"get_all_device_details() failed: {e}")

        logger.info(
            f"Fetched for topology -> interfaces: {len(interfaces) if interfaces else 0}, "
            f"switches: {len(switches_data['switches']) if isinstance(switches_data, dict) and 'switches' in switches_data else len(switches_data) if switches_data else 0}, "
            f"devices: {len(device_details) if device_details else 0}"
        )
    except Exception as e:
        logger.warning(f"Concurrent fetch failed unexpectedly: {e}")
        # Fall back to sequential but non-blocking defaults
        interfaces = interfaces or {}
        switches_data = switches_data or []
        device_details = device_details or []

    # Transform data into topology format
    topology_data = {
        "devices": [],
        "connections": []
    }
    
    # Add FortiGate device
    fortigate_name = os.getenv("FORTIGATE_NAME", "FortiGate-Main")
    topology_data["devices"].append({
        "id": "fortigate_main",
        "type": "fortigate",
        "name": fortigate_name,
        "ip": "192.168.0.254",
        "status": "online",
        "risk": "low",
        "position": {"x": 400, "y": 100},
        "details": {
            "model": "FortiGate",
            "interfaces": len(interfaces) if interfaces else 0,
            "status": "Active",
            "iconPath": "/static/icons/fortinet/png/fortigate.png"
        }
    })
    
    # Process FortiSwitch data
    if isinstance(switches_data, dict) and "switches" in switches_data:
        switches = switches_data["switches"]
    else:
        switches = switches_data if switches_data else []
    
    # Lay out switches horizontally under FortiGate, and endpoints below their switch
    switch_y = 280
    switch_x_start = 120
    switch_spacing = 220
    for i, switch in enumerate(switches):
        if isinstance(switch, dict):
            switch_id = f"switch_{i}"
            
            # Determine switch status and risk
            switch_status = "online" if switch.get("status") == "Authorized" else "warning"
            switch_risk = "low" if switch.get("status") == "Authorized" else "medium"
            
            topology_data["devices"].append({
                "id": switch_id,
                "type": "fortiswitch",
                "name": switch.get("serial", f"FortiSwitch-{i}"),
                "ip": switch.get("mgmt_ip", "N/A"),
                "status": switch_status,
                "risk": switch_risk,
                "position": {"x": switch_x_start + i * switch_spacing, "y": switch_y},
                "details": {
                    "serial": switch.get("serial", "Unknown"),
                    "model": switch.get("model", "FortiSwitch"),
                    "ports": len(switch.get("ports", [])),
                    "status": switch.get("status", "Unknown"),
                    "connectedDevices": len([d for d in device_details if d.get("switch_serial") == switch.get("serial")]),
                    "iconPath": "/static/icons/fortinet/png/fortiswitch.png"
                }
            })
            
            # Add connection from FortiGate to FortiSwitch
            topology_data["connections"].append({
                "from": "fortigate_main",
                "to": switch_id
            })
            
            switch_y += 200
    
    # Now use the enriched device_details for connected devices
    device_row_y = 420
    device_spacing = 110
    device_count = 0
    
    for device in device_details:
        if not device:
            continue
            
        device_id = f"device_{device_count}"
        
        # Get enriched device information
        manufacturer = device.get("manufacturer", "Unknown Manufacturer")
        device_name = (
            device.get("hostname")
            or device.get("device_name")
            or manufacturer
            or "Unknown Device"
        )
        
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
        
        # Priority for icon resolution: binding by serial/mac/manufacturer -> manufacturer icon -> device_type icon
        icon_path = device.get("icon_path") or ""
        icon_title = device.get("icon_title") or ""
        if not icon_path:
            try:
                from app.utils.icon_db import get_icon as _get_icon, get_icon_binding as _get_binding
                binding = _get_binding(
                    manufacturer=manufacturer,
                    serial=device.get("switch_serial"),
                    mac=device.get("mac") or device.get("device_mac"),
                    device_type=device_type,
                )
                if binding and binding.get("icon_path"):
                    icon_path = binding.get("icon_path")
                    icon_title = binding.get("title") or icon_title
                elif manufacturer:
                    icon_info = _get_icon(manufacturer=manufacturer)
                    if icon_info:
                        icon_path = icon_info.get("icon_path") or icon_path
                        icon_title = icon_info.get("title") or icon_title
                if not icon_path:
                    icon_info = _get_icon(device_type=device_type)
                    if icon_info:
                        icon_path = icon_info.get("icon_path") or icon_path
                        icon_title = icon_info.get("title") or icon_title
            except Exception:
                pass

        topology_data["devices"].append({
            "id": device_id,
            "type": device_type,
            "name": display_name,
            "ip": device.get("ip") or device.get("device_ip", "N/A"),
            "mac": device.get("mac") or device.get("device_mac", "N/A"),
            "status": "online",
            "risk": risk_level,
            "position": {"x": 0, "y": 0},  # temp; we compute below
            "details": {
                "manufacturer": manufacturer,
                "port": device.get("port_name", "Unknown"),
                "switch": device.get("switch_name", "Unknown"),
                "lastSeen": "Active",
                "mac": device.get("mac") or device.get("device_mac", "N/A"),
                "hostname": device.get("hostname") or device.get("device_name", "N/A"),
                "iconPath": icon_path or ("/static/icons/fortinet/png/server_cloud.png" if device_type == "server" else "/static/icons/fortinet/png/endpoint_laptop.png"),
                "iconTitle": icon_title
            }
        })
        
        # Connect device to its switch
        switch_serial = device.get("switch_serial")
        if switch_serial:
            # Find the switch this device is connected to
            for j, switch in enumerate(switches):
                if isinstance(switch, dict) and switch.get("serial") == switch_serial:
                    switch_id = f"switch_{j}"
                    # place endpoint under its switch horizontally
                    sx = switch_x_start + j * switch_spacing
                    # Count how many devices already placed under this switch to offset horizontally
                    under = [d for d in topology_data["devices"] if d["id"].startswith("device_") and any(c for c in topology_data["connections"] if c["to"] == d["id"] and c["from"] == switch_id)]
                    dx = sx - (len(under) * (device_spacing/2)) + (len(under) * device_spacing)
                    # Update device position (last appended)
                    topology_data["devices"][-1]["position"] = {"x": dx, "y": device_row_y}
                    topology_data["connections"].append({
                        "from": switch_id,
                        "to": device_id
                    })
                    break
        
        device_count += 1
    
        logger.info(
            f"END /api/topology_data - returning topology data: devices={len(topology_data.get('devices', []))}, "
            f"connections={len(topology_data.get('connections', []))}"
        )
    return topology_data

@app.post("/api/eraser/export")
async def eraser_export(payload: dict):
    if not eraser_service.is_enabled():
        raise HTTPException(status_code=501, detail="Eraser AI integration not enabled")
    return eraser_service.export_topology(payload)

@app.get("/api/eraser/status")
async def eraser_status():
    return {"enabled": eraser_service.is_enabled()}
