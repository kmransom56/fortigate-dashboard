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
from app.services.hybrid_topology_service import get_hybrid_topology_service
from app.services.redis_session_manager import get_redis_session_manager, cleanup_expired_sessions
from app.services.fortigate_redis_session import get_fortigate_redis_session_manager
from app.services.restaurant_device_service import get_restaurant_device_service


def get_device_icon_fallback(manufacturer, device_type):
    """Simple fallback icon mapping when database lookup fails"""
    icon_mapping = {
        # Manufacturer-specific icons
        "Apple Inc.": ("icons/apple.svg", "Apple Device"),
        "Microsoft Corporation": ("icons/microsoft.svg", "Microsoft Device"),
        "Dell Inc.": ("icons/nd/laptop.svg", "Dell Device"),
        "ASUSTek COMPUTER INC.": ("icons/nd/laptop.svg", "ASUS Device"),
        "BIZLINK TECHNOLOGY, INC.": ("icons/nd/laptop.svg", "Bizlink Device"),
        "Hon Hai Precision": ("icons/nd/laptop.svg", "Foxconn Device"),
        "Micro-Star INTL CO., LTD.": ("icons/nd/laptop.svg", "MSI Device"),
        
        # Device type fallbacks - use proper icons from our database
        "server": ("icons/nd/server.svg", "Server"),
        "endpoint": ("icons/nd/laptop.svg", "Endpoint"), 
        "fortigate": ("icons/FG-100F_101F.svg", "FortiGate 100F"),
        "fortiswitch": ("icons/FSW-124E.svg", "FortiSwitch 124E"),
    }
    
    # Try manufacturer first, then device type
    if manufacturer and manufacturer in icon_mapping:
        return icon_mapping[manufacturer]
    elif device_type and device_type in icon_mapping:
        return icon_mapping[device_type]
    else:
        return ("icons/Application.svg", "Unknown Device")

# Helper to aggregate device details for dashboard using hybrid topology
def get_all_device_details():
    hybrid_service = get_hybrid_topology_service()
    devices = hybrid_service.get_network_devices()
    
    # Enrich with icon information
    enriched_devices = []
    for dev in devices:
        dev_copy = dev.copy()
        # If icon_path not present, try to enrich from DB
        if not dev_copy.get("icon_path"):
            from app.utils.icon_db import get_icon
            
            icon_info = get_icon(manufacturer=dev_copy.get("manufacturer"))
            if not icon_info:
                icon_info = get_icon(device_type=dev_copy.get("device_type"))
            if icon_info:
                dev_copy["icon_path"] = icon_info["icon_path"]
                dev_copy["icon_title"] = icon_info["title"]
        
        enriched_devices.append(dev_copy)
    
    return enriched_devices


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
app.mount("/static", StaticFiles(directory="app/static"), name="static")

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

# 🎨 Route for Icon Management "/icons"
@app.get("/icons", response_class=HTMLResponse)
async def icons_page(request: Request):
    return templates.TemplateResponse("icons.html", {"request": request})


# 📡 API endpoint for topology data
@app.get("/api/topology_data")
async def api_topology_data():
    """
    Returns real network topology data for the Security Fabric-style visualization
    """
    import logging
    logger = logging.getLogger("api_topology_data")
    logger.info("START /api/topology_data endpoint")
    from app.services.fortigate_service import get_interfaces

    # Fetch data with aggressive timeouts to avoid UI hanging
    from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

    interfaces = {}
    switches_data = []
    device_details = []

    # Use hybrid topology service for comprehensive data
    hybrid_service = get_hybrid_topology_service()
    
    try:
        # Get data sequentially for reliability
        try:
            interfaces = get_interfaces()
        except Exception as e:
            logger.warning(f"get_interfaces() failed: {e}")

        try:
            switches_data = hybrid_service.get_comprehensive_topology()
        except Exception as e:
            logger.warning(f"hybrid topology failed: {e}")

        try:
            device_details = get_all_device_details()
        except Exception as e:
            logger.warning(f"get_all_device_details() failed: {e}")

        logger.info(
            f"Hybrid topology -> interfaces: {len(interfaces) if interfaces else 0}, "
            f"switches: {len(switches_data.get('switches', [])) if switches_data else 0}, "
            f"devices: {len(device_details) if device_details else 0}, "
            f"source: {switches_data.get('source', 'unknown') if switches_data else 'none'}"
        )
    except Exception as e:
        logger.warning(f"Sequential fetch failed unexpectedly: {e}")
        # Fall back to defaults
        interfaces = interfaces or {}
        switches_data = switches_data or {"switches": [], "source": "error"}
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
            "iconPath": "icons/FG-100F_101F.svg",
            "iconTitle": "FortiGate 100F"
        }
    })
    
    # Process FortiSwitch data from hybrid service
    switches = switches_data.get("switches", []) if isinstance(switches_data, dict) else []
    data_source = switches_data.get("source", "unknown") if isinstance(switches_data, dict) else "unknown"
    
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
                "name": switch.get("serial", f"FortiSwitch-{i}"),  # Use serial as name for clarity
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
                    "iconPath": "icons/FSW-124E.svg",
                    "iconTitle": "FortiSwitch 124E"
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
        
        # Enhanced device identification with restaurant-specific logic
        restaurant_service = get_restaurant_device_service()
        restaurant_info = restaurant_service.identify_restaurant_device(
            mac=device.get("mac") or device.get("device_mac", ""),
            hostname=device.get("hostname"),
            manufacturer=manufacturer
        )
        
        # Update device type and risk based on restaurant identification
        if restaurant_info.get('restaurant_device', False):
            device_type = restaurant_info.get('device_type', device_type)
            risk_level = restaurant_service.get_device_risk_assessment(restaurant_info)
            display_name = restaurant_info.get('description', display_name)
        
        # Priority for icon resolution: restaurant device -> icon DB -> fallback
        icon_path = device.get("icon_path") or ""
        icon_title = device.get("icon_title") or ""
        
        # Try restaurant-specific icons first
        if restaurant_info.get('restaurant_device', False):
            rest_icon_path, rest_icon_title = restaurant_service.get_restaurant_device_icon_path(restaurant_info)
            icon_path = rest_icon_path
            icon_title = rest_icon_title
        elif not icon_path:
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
            
            # Fallback to simple icon mapping if database lookup fails
            if not icon_path:
                icon_path, icon_title = get_device_icon_fallback(manufacturer, device_type)

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
                "iconPath": icon_path,
                "iconTitle": icon_title,
                # Restaurant-specific information
                "restaurantDevice": restaurant_info.get('restaurant_device', False),
                "deviceCategory": restaurant_info.get('category', 'general'),
                "confidence": restaurant_info.get('confidence', 'low'),
                "restaurantBrands": restaurant_info.get('restaurant_brands', []),
                "securityRisk": restaurant_service.get_device_risk_assessment(restaurant_info) if restaurant_info.get('restaurant_device', False) else 'unknown'
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
    
    # Add metadata about data sources
    topology_data["metadata"] = {
        "data_source": data_source,
        "interfaces_count": len(interfaces) if interfaces else 0,
        "switches_count": len(switches),
        "devices_count": len(device_details) if device_details else 0,
        "enhancement_info": switches_data.get("enhancement_info", {}) if isinstance(switches_data, dict) else {},
        "api_info": switches_data.get("api_info", {}) if isinstance(switches_data, dict) else {}
    }
    
    # Log final topology data being returned
    logger.info(f"Returning topology data: devices={len(topology_data['devices'])}, connections={len(topology_data['connections'])}")
    has_switches = any(d["type"] == "fortiswitch" for d in topology_data["devices"])
    has_endpoints = any(d["type"] in ["endpoint", "server"] for d in topology_data["devices"])
    logger.info(f"Topology composition: switches={has_switches}, endpoints={has_endpoints}, source={data_source}")
        
    logger.info("END /api/topology_data endpoint - returning topology data")
    return topology_data

@app.get("/api/debug/topology")
async def debug_topology():
    """Debug endpoint to check topology data sources"""
    try:
        import logging
        logger = logging.getLogger("debug_topology")
        
        # Test individual services
        hybrid_service = get_hybrid_topology_service()
        
        # Test hybrid topology
        topo_data = hybrid_service.get_comprehensive_topology()
        
        # Test device aggregation
        devices = get_all_device_details()
        
        return {
            "topology_switches": len(topo_data.get("switches", [])),
            "topology_source": topo_data.get("source", "unknown"),
            "aggregated_devices": len(devices),
            "first_device": devices[0] if devices else None,
            "enhancement_info": topo_data.get("monitor_enhancement", {}),
            "errors": topo_data.get("error") or "none"
        }
    except Exception as e:
        return {"error": str(e), "type": "debug_endpoint_error"}

@app.get("/api/debug/monitor")
async def debug_monitor():
    """Debug endpoint to test Monitor API directly"""
    try:
        from app.services.fortigate_monitor_service import get_fortigate_monitor_service
        
        monitor_service = get_fortigate_monitor_service()
        
        # Test detected devices
        devices_result = monitor_service.get_detected_devices()
        
        return {
            "service_status": "working",
            "device_count": len(devices_result.get("devices", [])),
            "active_devices": devices_result.get("active_devices", 0),
            "data_source": devices_result.get("source", "unknown"),
            "first_device": devices_result.get("devices", [{}])[0] if devices_result.get("devices") else None,
            "api_info": devices_result.get("api_info", {}),
            "error": devices_result.get("error", "none")
        }
    except Exception as e:
        return {"error": str(e), "type": "monitor_service_error"}

@app.get("/api/eraser/status")
async def eraser_status():
    return {"enabled": eraser_service.is_enabled()}

@app.get("/api/restaurant/device_summary")
async def restaurant_device_summary():
    """Get summary of restaurant-specific devices identified on the network"""
    try:
        # Get all device details
        devices = get_all_device_details()
        restaurant_service = get_restaurant_device_service()
        
        # Analyze each device for restaurant technology
        device_analysis = []
        category_counts = {}
        brand_counts = {}
        risk_counts = {}
        
        for device in devices:
            mac = device.get("mac") or device.get("device_mac", "")
            hostname = device.get("hostname")
            manufacturer = device.get("manufacturer")
            
            restaurant_info = restaurant_service.identify_restaurant_device(
                mac=mac, hostname=hostname, manufacturer=manufacturer
            )
            
            if restaurant_info.get('restaurant_device', False):
                device_analysis.append({
                    'name': device.get('hostname', 'Unknown'),
                    'mac': mac,
                    'manufacturer': manufacturer,
                    'device_type': restaurant_info.get('device_type'),
                    'category': restaurant_info.get('category'),
                    'confidence': restaurant_info.get('confidence'),
                    'restaurant_brands': restaurant_info.get('restaurant_brands', []),
                    'risk_level': restaurant_service.get_device_risk_assessment(restaurant_info)
                })
                
                # Count by category
                category = restaurant_info.get('category', 'unknown')
                category_counts[category] = category_counts.get(category, 0) + 1
                
                # Count by restaurant brand
                for brand in restaurant_info.get('restaurant_brands', []):
                    brand_counts[brand] = brand_counts.get(brand, 0) + 1
                
                # Count by risk level
                risk = restaurant_service.get_device_risk_assessment(restaurant_info)
                risk_counts[risk] = risk_counts.get(risk, 0) + 1
        
        return {
            "summary": {
                "total_devices": len(devices),
                "restaurant_devices": len(device_analysis),
                "restaurant_percentage": round((len(device_analysis) / len(devices) * 100), 1) if devices else 0
            },
            "categories": category_counts,
            "restaurant_brands": brand_counts,
            "risk_levels": risk_counts,
            "devices": device_analysis
        }
    except Exception as e:
        return {"error": str(e), "type": "restaurant_analysis_error"}



# Icon Management API Endpoints
@app.get("/api/icons/browse")
async def browse_icons(
    manufacturer: str = None,
    device_type: str = None, 
    limit: int = 50,
    offset: int = 0
):
    """Browse available icons with filtering"""
    from app.utils.icon_db import browse_icons as db_browse_icons
    return db_browse_icons(manufacturer, device_type, limit, offset)

@app.get("/api/icons/search")  
async def search_icons(q: str, limit: int = 20):
    """Search icons by title or tags"""
    from app.utils.icon_db import search_icons as db_search_icons
    return db_search_icons(q, limit)

@app.post("/api/eraser/export")
async def eraser_export(payload: dict):
    if not eraser_service.is_enabled():
        raise HTTPException(status_code=501, detail="Eraser AI integration not enabled")
    return eraser_service.export_topology(payload)

# Redis Session Management Endpoints
@app.get("/api/session/health")
async def session_health():
    """Get health status of Redis session management"""
    try:
        redis_manager = get_redis_session_manager()
        session_manager = get_fortigate_redis_session_manager()
        
        redis_health = redis_manager.health_check()
        session_health = session_manager.health_check()
        
        return {
            "redis": redis_health,
            "session_manager": session_health,
            "timestamp": redis_health.get("timestamp")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.get("/api/session/info")
async def session_info():
    """Get information about current sessions"""
    try:
        redis_manager = get_redis_session_manager()
        session_manager = get_fortigate_redis_session_manager()
        
        redis_info = redis_manager.get_session_info()
        current_session = session_manager.get_session_info()
        
        return {
            "redis_sessions": redis_info,
            "current_session": current_session
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session info failed: {str(e)}")

@app.post("/api/session/cleanup")
async def session_cleanup():
    """Manually trigger cleanup of expired sessions"""
    try:
        cleaned_count = cleanup_expired_sessions()
        return {
            "success": True,
            "cleaned_sessions": cleaned_count,
            "message": f"Cleaned up {cleaned_count} expired sessions"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session cleanup failed: {str(e)}")

@app.delete("/api/session/current")
async def logout_current_session():
    """Logout the current FortiGate session"""
    try:
        session_manager = get_fortigate_redis_session_manager()
        session_manager.logout()
        return {
            "success": True,
            "message": "Current session logged out successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")

@app.get("/api/session/test")
async def test_session_auth():
    """Test session authentication with a simple API call"""
    try:
        # Force session authentication (disable token fallback temporarily)
        original_fallback = os.getenv("FORTIGATE_ALLOW_TOKEN_FALLBACK")
        os.environ["FORTIGATE_ALLOW_TOKEN_FALLBACK"] = "false"
        
        from app.services.fortigate_service import fgt_api
        result = fgt_api("monitor/system/status")
        
        # Restore original setting
        if original_fallback is not None:
            os.environ["FORTIGATE_ALLOW_TOKEN_FALLBACK"] = original_fallback
        else:
            os.environ.pop("FORTIGATE_ALLOW_TOKEN_FALLBACK", None)
        
        if "error" in result:
            return {
                "success": False,
                "error": result.get("error"),
                "message": result.get("message", "Authentication test failed")
            }
        else:
            return {
                "success": True,
                "message": "Session authentication working correctly",
                "data": {
                    "endpoint": "monitor/system/status",
                    "response_keys": list(result.keys()) if isinstance(result, dict) else "non-dict response"
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session test failed: {str(e)}")
