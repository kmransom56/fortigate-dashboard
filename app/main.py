import logging
import os
import asyncio
import time
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api import fortigate
from app.services import eraser_service
from app.services.brand_detection_service import get_brand_detection_service
from app.services.fortigate_inventory_service import get_fortigate_inventory_service
from app.services.fortigate_redis_session import get_fortigate_redis_session_manager
from app.services.fortigate_service import get_cloud_status, get_interfaces
from app.services.fortiswitch_service import get_fortiswitches
from app.services.hybrid_topology_service import get_hybrid_topology_service
from app.services.icon_3d_service import get_3d_icon_service
from app.services.organization_service import get_organization_service
from app.services.redis_session_manager import (
    cleanup_expired_sessions,
    get_redis_session_manager,
)
from app.services.restaurant_device_service import get_restaurant_device_service
from app.services.scraped_topology_service import get_scraped_topology_service
from app.services.topology_integration_service import get_topology_integration_service
from app.utils.icon_db import seed_default_icons

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


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


# Route for FortiGate-style topology page
@app.get("/topology-fortigate", response_class=HTMLResponse)
async def topology_fortigate_page(request: Request):
    return templates.TemplateResponse("topology_fortigate.html", {"request": request})


# Route for 3D Force Graph topology
@app.get("/topology-3d-force", response_class=HTMLResponse)
async def topology_3d_force_page(request: Request):
    """Enhanced 3D topology using 3d-force-graph with sprite icons"""
    return templates.TemplateResponse("topology_3d_force.html", {"request": request})


# 📊 Route for Dashboard "/dashboard"
@app.get("/dashboard", response_class=HTMLResponse)
async def show_dashboard(request: Request):
    # Use async versions to avoid blocking
    from app.services.fortigate_service_optimized import get_interfaces_async

    try:
        interfaces = await get_interfaces_async()
    except Exception as e:
        logger.warning(f"Failed to get interfaces async, falling back to sync: {e}")
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


# 🎯 Route for FortiGate Scraped Topology "/topology-fortigate"
@app.get("/topology-fortigate", response_class=HTMLResponse)
async def fortigate_topology_page(request: Request):
    return templates.TemplateResponse("topology_fortigate.html", {"request": request})


# 🎨 Route for Icon Management "/icons"
@app.get("/icons", response_class=HTMLResponse)
async def icons_page(request: Request):
    return templates.TemplateResponse("icons.html", {"request": request})


# 🏢 Route for Enterprise Dashboard "/enterprise"
@app.get("/enterprise", response_class=HTMLResponse)
async def enterprise_page(request: Request):
    return templates.TemplateResponse("enterprise.html", {"request": request})


# 📡 API endpoint for topology data
@app.get("/api/topology_data")
async def api_topology_data():
    """
    Returns real network topology data for the Security Fabric-style visualization
    """
    import logging

    logger = logging.getLogger("api_topology_data")
    logger.info("START /api/topology_data endpoint")
    # Fetch data with aggressive timeouts to avoid UI hanging
    from app.services.fortigate_service import get_interfaces

    interfaces = {}
    switches_data = []
    device_details = []

    # Use optimized hybrid topology service for parallel async calls
    from app.services.hybrid_topology_service_optimized import (
        get_hybrid_topology_service_optimized,
    )
    from app.services.fortigate_service_optimized import get_interfaces_async

    hybrid_service_optimized = get_hybrid_topology_service_optimized()

    # Run all data fetching in parallel for better performance
    try:
        # Parallel async calls
        interfaces_task = get_interfaces_async()
        switches_task = hybrid_service_optimized.get_comprehensive_topology()
        device_details_task = asyncio.get_event_loop().run_in_executor(
            None, get_all_device_details
        )

        # Wait for all tasks to complete
        interfaces_result, switches_result, device_details_result = (
            await asyncio.gather(
                interfaces_task,
                switches_task,
                device_details_task,
                return_exceptions=True,
            )
        )

        # Handle results
        if isinstance(interfaces_result, Exception):
            logger.warning(f"get_interfaces_async() failed: {interfaces_result}")
            interfaces = {}
        else:
            interfaces = interfaces_result or {}
            logger.info(
                f"Successfully retrieved {len(interfaces) if interfaces else 0} interfaces"
            )

        if isinstance(switches_result, Exception):
            logger.warning(f"hybrid topology failed: {switches_result}")
            switches_data = {"switches": [], "source": "error"}
        else:
            switches_data = switches_result or {"switches": [], "source": "error"}
            if switches_data and switches_data.get("switches"):
                logger.info(
                    f"Successfully retrieved {len(switches_data.get('switches', []))} switches"
                )
            else:
                logger.warning("Hybrid topology returned empty switches list")

        if isinstance(device_details_result, Exception):
            logger.warning(f"get_all_device_details() failed: {device_details_result}")
            device_details = []
        else:
            device_details = device_details_result or []
            logger.info(
                f"Successfully retrieved {len(device_details) if device_details else 0} device details"
            )

    except Exception as e:
        logger.error(f"Parallel fetch failed: {e}")
        # Fallback to sequential calls
        try:
            interfaces = await get_interfaces_async()
        except Exception:
            interfaces = get_interfaces()

        try:
            switches_data = await hybrid_service_optimized.get_comprehensive_topology()
        except Exception:
            switches_data = {"switches": [], "source": "error"}

        try:
            device_details = get_all_device_details()
        except Exception:
            device_details = []

    logger.info(
        f"Topology data -> interfaces: {len(interfaces) if interfaces else 0}, "
        f"switches: {len(switches_data.get('switches', [])) if switches_data else 0}, "
        f"devices: {len(device_details) if device_details else 0}, "
        f"source: {switches_data.get('source', 'unknown') if switches_data else 'none'}"
    )

    # Transform data into topology format
    topology_data = {"devices": [], "connections": []}

    # Add FortiGate device
    fortigate_name = os.getenv("FORTIGATE_NAME", "FortiGate-Main")
    topology_data["devices"].append(
        {
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
                "iconTitle": "FortiGate 100F",
            },
        }
    )

    # Process FortiSwitch data from hybrid service
    switches = (
        switches_data.get("switches", []) if isinstance(switches_data, dict) else []
    )
    data_source = (
        switches_data.get("source", "unknown")
        if isinstance(switches_data, dict)
        else "unknown"
    )

    # Lay out switches horizontally under FortiGate, and endpoints below their switch
    switch_y = 280
    switch_x_start = 120
    switch_spacing = 220
    for i, switch in enumerate(switches):
        if isinstance(switch, dict):
            switch_id = f"switch_{i}"

            # Determine switch status and risk
            switch_status = (
                "online" if switch.get("status") == "Authorized" else "warning"
            )
            switch_risk = "low" if switch.get("status") == "Authorized" else "medium"

            topology_data["devices"].append(
                {
                    "id": switch_id,
                    "type": "fortiswitch",
                    "name": switch.get(
                        "serial", f"FortiSwitch-{i}"
                    ),  # Use serial as name for clarity
                    "ip": switch.get("mgmt_ip", "N/A"),
                    "status": switch_status,
                    "risk": switch_risk,
                    "position": {
                        "x": switch_x_start + i * switch_spacing,
                        "y": switch_y,
                    },
                    "details": {
                        "serial": switch.get("serial", "Unknown"),
                        "model": switch.get("model", "FortiSwitch"),
                        "ports": len(switch.get("ports", [])),
                        "status": switch.get("status", "Unknown"),
                        "connectedDevices": len(
                            [
                                d
                                for d in device_details
                                if d.get("switch_serial") == switch.get("serial")
                            ]
                        ),
                        "iconPath": "icons/FSW-124E.svg",
                        "iconTitle": "FortiSwitch 124E",
                    },
                }
            )

            # Add connection from FortiGate to FortiSwitch
            topology_data["connections"].append(
                {"from": "fortigate_main", "to": switch_id}
            )

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
                display_name = (
                    manufacturer.replace(" Corporation", "")
                    .replace(" Inc.", "")
                    .replace(" Inc", "")
                )
        else:
            display_name = (
                f"Device {device.get('mac', '')[-8:]}"
                if device.get("mac")
                else "Unknown Device"
            )

        # Ensure name isn't too long
        if len(display_name) > 15:
            display_name = display_name[:12] + "..."

        # Enhanced device identification with restaurant-specific logic
        restaurant_service = get_restaurant_device_service()
        restaurant_info = restaurant_service.identify_restaurant_device(
            mac=device.get("mac") or device.get("device_mac", ""),
            hostname=device.get("hostname"),
            manufacturer=manufacturer,
        )

        # Update device type and risk based on restaurant identification
        if restaurant_info.get("restaurant_device", False):
            device_type = restaurant_info.get("device_type", device_type)
            risk_level = restaurant_service.get_device_risk_assessment(restaurant_info)
            display_name = restaurant_info.get("description", display_name)

        # Priority for icon resolution: restaurant device -> icon DB -> fallback
        icon_path = device.get("icon_path") or ""
        icon_title = device.get("icon_title") or ""

        # Try restaurant-specific icons first
        if restaurant_info.get("restaurant_device", False):
            rest_icon_path, rest_icon_title = (
                restaurant_service.get_restaurant_device_icon_path(restaurant_info)
            )
            icon_path = rest_icon_path
            icon_title = rest_icon_title
        elif not icon_path:
            try:
                from app.utils.icon_db import get_icon as _get_icon
                from app.utils.icon_db import get_icon_binding as _get_binding

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
                icon_path, icon_title = get_device_icon_fallback(
                    manufacturer, device_type
                )

        topology_data["devices"].append(
            {
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
                    "hostname": device.get("hostname")
                    or device.get("device_name", "N/A"),
                    "iconPath": icon_path,
                    "iconTitle": icon_title,
                    # Restaurant-specific information
                    "restaurantDevice": restaurant_info.get("restaurant_device", False),
                    "deviceCategory": restaurant_info.get("category", "general"),
                    "confidence": restaurant_info.get("confidence", "low"),
                    "restaurantBrands": restaurant_info.get("restaurant_brands", []),
                    "securityRisk": (
                        restaurant_service.get_device_risk_assessment(restaurant_info)
                        if restaurant_info.get("restaurant_device", False)
                        else "unknown"
                    ),
                },
            }
        )

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
                    under = [
                        d
                        for d in topology_data["devices"]
                        if d["id"].startswith("device_")
                        and any(
                            c
                            for c in topology_data["connections"]
                            if c["to"] == d["id"] and c["from"] == switch_id
                        )
                    ]
                    dx = (
                        sx
                        - (len(under) * (device_spacing / 2))
                        + (len(under) * device_spacing)
                    )
                    # Update device position (last appended)
                    topology_data["devices"][-1]["position"] = {
                        "x": dx,
                        "y": device_row_y,
                    }
                    topology_data["connections"].append(
                        {"from": switch_id, "to": device_id}
                    )
                    break

        device_count += 1

    # Add metadata about data sources
    topology_data["metadata"] = {
        "data_source": data_source,
        "interfaces_count": len(interfaces) if interfaces else 0,
        "switches_count": len(switches),
        "devices_count": len(device_details) if device_details else 0,
        "enhancement_info": (
            switches_data.get("enhancement_info", {})
            if isinstance(switches_data, dict)
            else {}
        ),
        "api_info": (
            switches_data.get("api_info", {}) if isinstance(switches_data, dict) else {}
        ),
    }

    # Log final topology data being returned
    logger.info(
        f"Returning topology data: devices={len(topology_data['devices'])}, connections={len(topology_data['connections'])}"
    )
    has_switches = any(d["type"] == "fortiswitch" for d in topology_data["devices"])
    has_endpoints = any(
        d["type"] in ["endpoint", "server"] for d in topology_data["devices"]
    )
    logger.info(
        f"Topology composition: switches={has_switches}, endpoints={has_endpoints}, source={data_source}"
    )

    logger.info("END /api/topology_data endpoint - returning topology data")
    return topology_data


@app.get("/api/scraped_topology")
async def api_scraped_topology():
    """API endpoint for scraped FortiGate topology data"""
    logger = logging.getLogger("api_scraped_topology")

    try:
        logger.info("START /api/scraped_topology endpoint")
        scraped_service = get_scraped_topology_service()
        topology_data = scraped_service.get_topology_data()

        # Check if we got an error in metadata
        metadata = topology_data.get("metadata", {})
        if metadata.get("source") == "error":
            error_msg = metadata.get("error", "Unknown error")
            logger.error(f"Service returned error: {error_msg}")
            # Return error response instead of raising exception - let frontend handle it
            return {
                "devices": [],
                "connections": [],
                "metadata": {
                    "source": "error",
                    "error": error_msg,
                    "device_count": 0,
                    "connection_count": 0,
                },
            }

        logger.info(
            f"Scraped topology data source: {metadata.get('source', 'unknown')}"
        )
        logger.info(f"Device count: {len(topology_data.get('devices', []))}")
        logger.info(f"Connection count: {len(topology_data.get('connections', []))}")

        return topology_data

    except Exception as e:
        # Ensure logger is available even if exception happened early
        try:
            logger.error(f"Error in scraped topology endpoint: {e}", exc_info=True)
        except BaseException:
            # Fallback if logger itself fails
            import sys

            print(f"ERROR in scraped_topology endpoint: {e}", file=sys.stderr)

        # Try to diagnose the issue (non-blocking)
        try:
            await _diagnose_topology_error(str(e))
        except BaseException:
            pass

        # Return error response instead of raising - no mock data per AGENTS.md
        return {
            "devices": [],
            "connections": [],
            "metadata": {
                "source": "error",
                "error": str(e),
                "device_count": 0,
                "connection_count": 0,
            },
        }


async def _diagnose_topology_error(error_msg: str):
    """Diagnose topology errors and attempt to fix common issues"""
    logger = logging.getLogger("topology_diagnostics")
    logger.info(f"Diagnosing topology error: {error_msg}")

    # Check FortiGate connection
    try:
        fortigate_host = os.getenv("FORTIGATE_HOST", "192.168.0.254")
        logger.info(f"Checking FortiGate connection to {fortigate_host}")

        from app.services.fortigate_service import get_interfaces

        interfaces = get_interfaces()
        if interfaces:
            logger.info(
                f"FortiGate connection successful, found {len(interfaces)} interfaces"
            )
        else:
            logger.warning("FortiGate connection successful but no interfaces returned")
    except Exception as e:
        logger.error(f"FortiGate connection failed: {e}")
        logger.info(
            "Possible issues: incorrect FORTIGATE_HOST, authentication failure, or network unreachable"
        )

    # Check Redis connection
    try:
        import redis

        redis_host = os.getenv("REDIS_HOST", "redis")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        r.ping()
        logger.info("Redis connection successful")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        logger.info(
            "Possible issues: Redis not running or incorrect REDIS_HOST/REDIS_PORT"
        )

    # Check hybrid topology service
    try:
        hybrid_service = get_hybrid_topology_service()
        topology = hybrid_service.get_comprehensive_topology()
        if topology and topology.get("switches"):
            logger.info(
                f"Hybrid topology service working, found {len(topology.get('switches', []))} switches"
            )
        else:
            logger.warning("Hybrid topology service working but no switches found")
    except Exception as e:
        logger.error(f"Hybrid topology service failed: {e}")


@app.get("/api/debug/topology")
async def debug_topology():
    """Debug endpoint to check topology data sources"""
    try:
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
            "errors": topo_data.get("error") or "none",
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
            "first_device": (
                devices_result.get("devices", [{}])[0]
                if devices_result.get("devices")
                else None
            ),
            "api_info": devices_result.get("api_info", {}),
            "error": devices_result.get("error", "none"),
        }
    except Exception as e:
        return {"error": str(e), "type": "monitor_service_error"}


@app.get("/api/eraser/status")
async def eraser_status():
    return {"enabled": eraser_service.is_enabled()}


# Organization Management API Endpoints
@app.get("/api/organizations")
async def get_organizations():
    """Get all organizations"""
    try:
        org_service = get_organization_service()
        organizations = org_service.get_all_organizations()

        return {
            "organizations": [
                {
                    "id": org.id,
                    "name": org.name,
                    "brand": org.brand.value,
                    "region": org.region,
                    "location_count": org.location_count,
                    "infrastructure_type": org.infrastructure_type.value,
                    "created_at": org.created_at.isoformat(),
                }
                for org in organizations
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get organizations: {str(e)}"
        )


@app.get("/api/organizations/{org_id}")
async def get_organization(org_id: str):
    """Get specific organization details"""
    try:
        org_service = get_organization_service()
        org = org_service.get_organization(org_id)

        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        return {
            "id": org.id,
            "name": org.name,
            "brand": org.brand.value,
            "region": org.region,
            "location_count": org.location_count,
            "infrastructure_type": org.infrastructure_type.value,
            "created_at": org.created_at.isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get organization: {str(e)}"
        )


@app.get("/api/organizations/{org_id}/locations")
async def get_organization_locations(org_id: str, limit: int = 100, offset: int = 0):
    """Get locations for an organization"""
    try:
        org_service = get_organization_service()
        org = org_service.get_organization(org_id)

        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        locations = org_service.get_organization_locations(org_id, limit, offset)

        return {
            "organization_id": org_id,
            "organization_name": org.name,
            "total_locations": org.location_count,
            "returned_count": len(locations),
            "limit": limit,
            "offset": offset,
            "locations": [
                {
                    "id": loc.id,
                    "store_number": loc.store_number,
                    "name": loc.name,
                    "address": loc.address,
                    "city": loc.city,
                    "state": loc.state,
                    "status": loc.status.value,
                    "infrastructure_type": loc.infrastructure_type.value,
                    "fortigate_ip": loc.fortigate_ip,
                    "fortigate_model": loc.fortigate_model,
                    "switch_count": loc.switch_count,
                    "ap_count": loc.ap_count,
                    "last_discovered": (
                        loc.last_discovered.isoformat() if loc.last_discovered else None
                    ),
                }
                for loc in locations
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get locations: {str(e)}"
        )


@app.get("/api/organizations/{org_id}/discovery_config")
async def get_organization_discovery_config(org_id: str):
    """Get discovery configuration for an organization"""
    try:
        org_service = get_organization_service()
        config = org_service.get_organization_discovery_config(org_id)

        if not config:
            raise HTTPException(status_code=404, detail="Organization not found")

        return config
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get discovery config: {str(e)}"
        )


@app.get("/api/organizations/{org_id}/compliance")
async def get_organization_compliance(org_id: str):
    """Get compliance requirements for an organization"""
    try:
        org_service = get_organization_service()
        compliance = org_service.get_compliance_requirements(org_id)

        if not compliance:
            raise HTTPException(status_code=404, detail="Organization not found")

        return compliance
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get compliance requirements: {str(e)}"
        )


@app.post("/api/organizations/{org_id}/discover")
async def start_organization_discovery(org_id: str, location_limit: int = None):
    """Start device discovery for an organization"""
    try:
        org_service = get_organization_service()
        result = await org_service.discover_organization_devices(org_id, location_limit)

        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to start discovery: {str(e)}"
        )


# Enterprise Topology API Endpoints
@app.get("/api/topology/enterprise")
async def get_enterprise_topology(org_filter: str = None):
    """Get enterprise-wide topology including FortiSwitch and Meraki switches"""
    try:
        hybrid_service = get_hybrid_topology_service()
        topology_data = hybrid_service.get_enterprise_topology(org_filter)
        return topology_data
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get enterprise topology: {str(e)}"
        )


@app.get("/api/meraki/health")
async def meraki_health_check():
    """Check Meraki API connectivity"""
    try:
        from app.services.meraki_service import get_meraki_service

        meraki_service = get_meraki_service()
        health_data = meraki_service.health_check()
        return health_data
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Meraki health check failed: {str(e)}"
        )


# Scanopy Integration API Endpoints
@app.get("/api/scanopy/status")
async def scanopy_status():
    """Check Scanopy server health and availability"""
    try:
        from app.services.scanopy_service import get_scanopy_service

        scanopy_service = get_scanopy_service()
        health_data = await scanopy_service.health_check()
        return health_data
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Scanopy health check failed: {str(e)}"
        )


@app.get("/api/scanopy/hosts")
async def get_scanopy_hosts(organization_id: str = None, network_id: str = None):
    """Get all discovered hosts from Scanopy"""
    try:
        from app.services.scanopy_service import get_scanopy_service

        scanopy_service = get_scanopy_service()
        hosts_data = await scanopy_service.get_hosts(organization_id, network_id)
        return hosts_data
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get Scanopy hosts: {str(e)}"
        )


@app.get("/api/scanopy/host/{ip_address}")
async def get_scanopy_host(ip_address: str):
    """Get specific host details from Scanopy by IP address"""
    try:
        from app.services.scanopy_service import get_scanopy_service

        scanopy_service = get_scanopy_service()
        host_data = await scanopy_service.get_host_by_ip(ip_address)
        if "error" in host_data and host_data.get("error") == "Host not found":
            raise HTTPException(status_code=404, detail=f"Host not found: {ip_address}")
        return host_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get Scanopy host: {str(e)}"
        )


@app.get("/api/scanopy/services")
async def get_scanopy_services(organization_id: str = None):
    """Get all detected services from Scanopy"""
    try:
        from app.services.scanopy_service import get_scanopy_service

        scanopy_service = get_scanopy_service()
        services_data = await scanopy_service.get_services(organization_id)
        return services_data
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get Scanopy services: {str(e)}"
        )


@app.get("/api/scanopy/topology")
async def get_scanopy_topology(organization_id: str = None, network_id: str = None):
    """Get network topology from Scanopy"""
    try:
        from app.services.scanopy_service import get_scanopy_service

        scanopy_service = get_scanopy_service()
        topology_data = await scanopy_service.get_topology(organization_id, network_id)
        return topology_data
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get Scanopy topology: {str(e)}"
        )


@app.post("/api/scanopy/scan")
async def trigger_scanopy_scan(scan_request: dict):
    """Trigger a network scan in Scanopy"""
    try:
        from app.services.scanopy_service import get_scanopy_service

        scanopy_service = get_scanopy_service()
        subnet = scan_request.get("subnet")
        scan_type = scan_request.get("scan_type", "full")

        if not subnet:
            raise HTTPException(status_code=400, detail="subnet is required")

        result = await scanopy_service.trigger_scan(subnet, scan_type)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger scan: {str(e)}")


@app.get("/api/scanopy/networks")
async def get_scanopy_networks(organization_id: str = None):
    """Get all networks from Scanopy"""
    try:
        from app.services.scanopy_service import get_scanopy_service

        scanopy_service = get_scanopy_service()
        networks = await scanopy_service.get_networks(organization_id)
        return {"networks": networks, "count": len(networks)}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get Scanopy networks: {str(e)}"
        )


@app.get("/api/unified/topology")
async def get_unified_topology(organization_id: str = None, network_id: str = None):
    """
    Get unified topology combining FortiGate, Meraki, and Scanopy data

    This endpoint combines:
    - FortiGate/FortiSwitch infrastructure (from hybrid topology)
    - Meraki switches (if configured)
    - Scanopy discovered hosts and services
    """
    try:
        from app.services.hybrid_topology_service_optimized import (
            get_hybrid_topology_service_optimized,
        )
        from app.services.meraki_service import get_meraki_service
        from app.services.scanopy_service import get_scanopy_service

        # Get data from all sources in parallel
        hybrid_service = get_hybrid_topology_service_optimized()
        meraki_service = get_meraki_service()
        scanopy_service = get_scanopy_service()

        # Parallel async calls
        topology_task = hybrid_service.get_comprehensive_topology()
        meraki_task = asyncio.get_event_loop().run_in_executor(
            None, lambda: meraki_service.get_switch_topology_data(organization_id)
        )
        scanopy_hosts_task = scanopy_service.get_hosts(organization_id, network_id)
        scanopy_services_task = scanopy_service.get_services(organization_id)

        # Wait for all tasks
        topology, meraki_data, scanopy_hosts, scanopy_services = await asyncio.gather(
            topology_task,
            meraki_task,
            scanopy_hosts_task,
            scanopy_services_task,
            return_exceptions=True,
        )

        # Handle exceptions
        if isinstance(topology, Exception):
            logger.warning(f"Topology retrieval failed: {topology}")
            topology = {"switches": [], "source": "error"}
        if isinstance(meraki_data, Exception):
            logger.warning(f"Meraki data retrieval failed: {meraki_data}")
            meraki_data = {"switches": [], "error": str(meraki_data)}
        if isinstance(scanopy_hosts, Exception):
            logger.warning(f"Scanopy hosts retrieval failed: {scanopy_hosts}")
            scanopy_hosts = {"hosts": [], "count": 0}
        if isinstance(scanopy_services, Exception):
            logger.warning(f"Scanopy services retrieval failed: {scanopy_services}")
            scanopy_services = {"services": [], "count": 0}

        # Build unified response
        unified_data = {
            "timestamp": datetime.now().isoformat(),
            "infrastructure": {
                "fortigate_switches": {
                    "count": len(topology.get("switches", [])),
                    "switches": topology.get("switches", []),
                    "source": topology.get("source", "unknown"),
                },
                "meraki_switches": {
                    "count": len(meraki_data.get("switches", [])),
                    "switches": meraki_data.get("switches", []),
                },
            },
            "discovered_endpoints": {
                "count": scanopy_hosts.get("count", 0),
                "hosts": scanopy_hosts.get("hosts", []),
            },
            "services_summary": {
                "types": list(
                    set(
                        service.get("name")
                        for host in scanopy_hosts.get("hosts", [])
                        for service in host.get("services", [])
                        if service.get("name")
                    )
                ),
                "count": scanopy_services.get("count", 0),
                "details": {},
            },
        }

        # Group services by type
        for host in scanopy_hosts.get("hosts", []):
            for service in host.get("services", []):
                service_name = service.get("name")
                if service_name:
                    if service_name not in unified_data["services_summary"]["details"]:
                        unified_data["services_summary"]["details"][service_name] = []
                    unified_data["services_summary"]["details"][service_name].append(
                        {
                            "ip": host.get("ip_address"),
                            "hostname": host.get("hostname"),
                            "port": service.get("port"),
                            "protocol": service.get("protocol"),
                        }
                    )

        return unified_data

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get unified topology: {str(e)}"
        )


@app.get("/api/meraki/organizations")
async def get_meraki_organizations():
    """Get Meraki organizations"""
    try:
        from app.services.meraki_service import get_meraki_service

        meraki_service = get_meraki_service()
        orgs = meraki_service.get_organizations()
        return {"organizations": orgs}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get Meraki organizations: {str(e)}"
        )


@app.get("/api/meraki/switches")
async def get_meraki_switches(org_filter: str = None):
    """Get Meraki switches for BWW/Arby's restaurant organizations (FortiGate + Meraki + FortiAP)"""
    try:
        from app.services.meraki_service import get_meraki_service

        meraki_service = get_meraki_service()
        switches_data = meraki_service.discover_restaurant_meraki_switches(org_filter)
        return switches_data
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get Meraki switches: {str(e)}"
        )


@app.get("/api/brand/detect/{ip_address}")
async def detect_brand_and_devices(ip_address: str):
    """Detect restaurant brand and discover associated network devices"""
    try:
        brand_service = get_brand_detection_service()
        detection_result = await brand_service.discover_brand_devices(ip_address)

        return {
            "brand": detection_result.brand.value,
            "location_id": detection_result.location_id,
            "store_number": detection_result.store_number,
            "confidence": detection_result.confidence,
            "infrastructure_type": detection_result.infrastructure_type.value,
            "detected_devices": detection_result.detected_devices,
            "discovery_method": detection_result.discovery_method,
            "expected_infrastructure": brand_service.get_expected_infrastructure(
                detection_result.brand
            ),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Brand detection failed: {str(e)}")


@app.get("/api/brand/topology")
async def get_brand_topology_summary(brand: str = None):
    """Get topology summary filtered by restaurant brand"""
    try:
        brand_service = get_brand_detection_service()
        summary = await brand_service.get_brand_topology_summary(brand)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Brand topology summary failed: {str(e)}"
        )


# FortiGate Inventory API Endpoints
@app.get("/api/fortigate/inventory/summary")
async def get_fortigate_inventory_summary():
    """Get comprehensive FortiGate inventory summary"""
    try:
        inventory_service = get_fortigate_inventory_service()
        summary = inventory_service.get_inventory_summary()
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get inventory summary: {str(e)}"
        )


@app.get("/api/fortigate/locations")
async def get_fortigate_locations(
    brand: str = None, region: str = None, limit: int = 100, offset: int = 0
):
    """Get FortiGate locations with filtering and pagination"""
    try:
        inventory_service = get_fortigate_inventory_service()

        if brand:
            locations = inventory_service.get_locations_by_brand(brand, limit)
        elif region:
            locations = inventory_service.get_locations_by_region(region)
        else:
            locations = inventory_service.get_all_locations(limit, offset)

        # Convert to serializable format
        location_data = []
        for loc in locations:
            location_data.append(
                {
                    "store_number": loc.store_number,
                    "ip_address": loc.ip_address,
                    "brand": loc.brand,
                    "region": loc.region,
                    "mgmt_interface": loc.mgmt_interface,
                    "subnet_mask": loc.subnet_mask,
                    "status": loc.status,
                    "last_seen": loc.last_seen.isoformat() if loc.last_seen else None,
                    "model": loc.model,
                    "firmware": loc.firmware,
                }
            )

        return {
            "locations": location_data,
            "total_count": len(locations),
            "filters": {"brand": brand, "region": region},
            "pagination": {"limit": limit, "offset": offset},
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get FortiGate locations: {str(e)}"
        )


@app.get("/api/fortigate/location/{store_number}")
async def get_fortigate_location(store_number: str):
    """Get specific FortiGate location details"""
    try:
        inventory_service = get_fortigate_inventory_service()
        location = inventory_service.get_location(store_number)

        if not location:
            raise HTTPException(
                status_code=404, detail=f"FortiGate location not found: {store_number}"
            )

        return {
            "store_number": location.store_number,
            "ip_address": location.ip_address,
            "brand": location.brand,
            "region": location.region,
            "mgmt_interface": location.mgmt_interface,
            "subnet_mask": location.subnet_mask,
            "status": location.status,
            "last_seen": location.last_seen.isoformat() if location.last_seen else None,
            "model": location.model,
            "firmware": location.firmware,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get FortiGate location: {str(e)}"
        )


@app.get("/api/fortigate/location/{store_number}/connection")
async def get_fortigate_connection_info(store_number: str):
    """Get connection information for a specific FortiGate"""
    try:
        inventory_service = get_fortigate_inventory_service()
        connection_info = inventory_service.get_fortigate_connection_info(store_number)

        if not connection_info:
            raise HTTPException(
                status_code=404, detail=f"FortiGate not found: {store_number}"
            )

        return connection_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get connection info: {str(e)}"
        )


@app.get("/api/fortigate/search")
async def search_fortigate_locations(q: str, limit: int = 50):
    """Search FortiGate locations by store number, IP, brand, or region"""
    try:
        inventory_service = get_fortigate_inventory_service()
        locations = inventory_service.search_locations(q, limit)

        # Convert to serializable format
        location_data = []
        for loc in locations:
            location_data.append(
                {
                    "store_number": loc.store_number,
                    "ip_address": loc.ip_address,
                    "brand": loc.brand,
                    "region": loc.region,
                    "status": loc.status,
                }
            )

        return {
            "query": q,
            "results": location_data,
            "result_count": len(location_data),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/api/fortigate/discovery/locations")
async def get_discovery_locations(
    brand: str = None, region: str = None, limit: int = 100
):
    """Get FortiGate locations formatted for discovery operations"""
    try:
        inventory_service = get_fortigate_inventory_service()
        discovery_locations = inventory_service.get_locations_for_discovery(
            brand, region, limit
        )

        return {
            "discovery_locations": discovery_locations,
            "total_count": len(discovery_locations),
            "filters": {"brand": brand, "region": region},
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get discovery locations: {str(e)}"
        )


@app.post("/api/fortigate/location/{store_number}/status")
async def update_fortigate_status(store_number: str, status_update: dict):
    """Update FortiGate location status"""
    try:
        inventory_service = get_fortigate_inventory_service()

        status = status_update.get("status", "unknown")
        model = status_update.get("model")
        firmware = status_update.get("firmware")

        # Build update kwargs
        update_kwargs = {}
        if model:
            update_kwargs["model"] = model
        if firmware:
            update_kwargs["firmware"] = firmware

        success = inventory_service.update_location_status(
            store_number, status, **update_kwargs
        )

        if not success:
            raise HTTPException(
                status_code=404, detail=f"FortiGate location not found: {store_number}"
            )

        return {
            "success": True,
            "store_number": store_number,
            "status": status,
            "updated_at": datetime.now().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update status: {str(e)}"
        )


@app.get("/api/enterprise/summary")
async def get_enterprise_summary():
    """Get enterprise-wide summary statistics"""
    try:
        org_service = get_organization_service()
        summary = org_service.get_enterprise_summary()
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get enterprise summary: {str(e)}"
        )


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

            if restaurant_info.get("restaurant_device", False):
                device_analysis.append(
                    {
                        "name": device.get("hostname", "Unknown"),
                        "mac": mac,
                        "manufacturer": manufacturer,
                        "device_type": restaurant_info.get("device_type"),
                        "category": restaurant_info.get("category"),
                        "confidence": restaurant_info.get("confidence"),
                        "restaurant_brands": restaurant_info.get(
                            "restaurant_brands", []
                        ),
                        "risk_level": restaurant_service.get_device_risk_assessment(
                            restaurant_info
                        ),
                    }
                )

                # Count by category
                category = restaurant_info.get("category", "unknown")
                category_counts[category] = category_counts.get(category, 0) + 1

                # Count by restaurant brand
                for brand in restaurant_info.get("restaurant_brands", []):
                    brand_counts[brand] = brand_counts.get(brand, 0) + 1

                # Count by risk level
                risk = restaurant_service.get_device_risk_assessment(restaurant_info)
                risk_counts[risk] = risk_counts.get(risk, 0) + 1

        return {
            "summary": {
                "total_devices": len(devices),
                "restaurant_devices": len(device_analysis),
                "restaurant_percentage": (
                    round((len(device_analysis) / len(devices) * 100), 1)
                    if devices
                    else 0
                ),
            },
            "categories": category_counts,
            "restaurant_brands": brand_counts,
            "risk_levels": risk_counts,
            "devices": device_analysis,
        }
    except Exception as e:
        return {"error": str(e), "type": "restaurant_analysis_error"}


# Icon Management API Endpoints
@app.get("/api/icons/browse")
async def browse_icons(
    manufacturer: str = None, device_type: str = None, limit: int = 50, offset: int = 0
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


# 3D Topology API Endpoints
@app.get("/api/topology_3d_data")
async def api_topology_3d_data():
    """
    Returns 3D topology data with Eraser AI-generated 3D icons
    """
    import logging

    logger = logging.getLogger("api_topology_3d_data")
    logger.info("START /api/topology_3d_data endpoint")

    try:
        # Get the base topology data (same as 2D)
        topology_2d = await api_topology_data()

        if not topology_2d or "devices" not in topology_2d:
            logger.warning("No 2D topology data available")
            return {
                "devices": [],
                "connections": [],
                "metadata": {"error": "No base topology data"},
            }

        # Get 3D icon service
        icon_3d_service = get_3d_icon_service()

        # Convert 2D devices to 3D with enhanced icons
        devices_3d = []
        for device in topology_2d["devices"]:
            device_3d = device.copy()

            # Get device information for 3D icon generation
            device_type = device.get("type", "endpoint")
            device_name = device.get("name", "Unknown Device")
            icon_path = device.get("details", {}).get("iconPath", "")

            # Generate 3D icon data
            if icon_path and icon_path.startswith("icons/"):
                svg_path = f"app/static/{icon_path}"
                try:
                    icon_3d_data = icon_3d_service.get_3d_icon_data(
                        svg_path, device_type, device_name
                    )
                    device_3d["3d_icon"] = icon_3d_data

                    # Add 3D positioning data
                    pos_2d = device.get("position", {"x": 0, "y": 0})
                    device_3d["position_3d"] = {
                        "x": (pos_2d["x"] - 400) / 100,  # Scale and center
                        "y": 0,  # Ground level
                        "z": -(pos_2d["y"] - 300) / 100,  # Convert Y to Z, invert
                    }

                    # Add animation data
                    device_3d["animation"] = {
                        "hover_scale": [1.2, 1.2, 1.2],
                        "click_rotation": [0, 0.5, 0],
                        "status_pulse": device.get("status") != "online",
                    }

                except Exception as e:
                    logger.warning(f"Failed to generate 3D icon for {icon_path}: {e}")
                    # Use fallback 3D data
                    device_3d["3d_icon"] = icon_3d_service._get_fallback_3d_data(
                        device_type, device_name
                    )
                    device_3d["position_3d"] = {
                        "x": (pos_2d["x"] - 400) / 100,
                        "y": 0,
                        "z": -(pos_2d["y"] - 300) / 100,
                    }
            else:
                # No icon path, use basic 3D representation
                device_3d["3d_icon"] = icon_3d_service._get_fallback_3d_data(
                    device_type, device_name
                )
                pos_2d = device.get("position", {"x": 0, "y": 0})
                device_3d["position_3d"] = {
                    "x": (pos_2d["x"] - 400) / 100,
                    "y": 0,
                    "z": -(pos_2d["y"] - 300) / 100,
                }

            devices_3d.append(device_3d)

        # Convert 2D connections to 3D
        connections_3d = []
        for connection in topology_2d.get("connections", []):
            connection_3d = connection.copy()
            connection_3d["3d_properties"] = {
                "line_width": 0.1,
                "color": "#4A90E2",
                "opacity": 0.7,
                "animate_flow": True,
                "flow_speed": 2.0,
            }
            connections_3d.append(connection_3d)

        # Enhanced 3D metadata
        metadata_3d = topology_2d.get("metadata", {}).copy()
        metadata_3d.update(
            {
                "3d_enabled": True,
                "eraser_ai_enabled": eraser_service.is_enabled(),
                "3d_icon_stats": icon_3d_service.get_cache_stats(),
                "camera_position": {"x": 5, "y": 5, "z": 5},
                "camera_target": {"x": 0, "y": 0, "z": 0},
                "lighting": {
                    "ambient_color": "#404040",
                    "directional_color": "#ffffff",
                    "directional_position": {"x": -1, "y": 1, "z": 1},
                },
                "scene_background": "#f0f8ff",
            }
        )

        topology_3d = {
            "devices": devices_3d,
            "connections": connections_3d,
            "metadata": metadata_3d,
        }

        logger.info(
            f"Returning 3D topology data: {len(devices_3d)} devices, {len(connections_3d)} connections"
        )
        logger.info("END /api/topology_3d_data endpoint")

        return topology_3d

    except Exception as e:
        logger.error(f"Error in 3D topology data generation: {e}")
        return {
            "devices": [],
            "connections": [],
            "metadata": {
                "error": str(e),
                "3d_enabled": False,
                "eraser_ai_enabled": eraser_service.is_enabled(),
            },
        }


@app.get("/api/3d_icons/stats")
async def get_3d_icon_stats():
    """Get 3D icon cache statistics"""
    try:
        icon_3d_service = get_3d_icon_service()
        stats = icon_3d_service.get_cache_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get 3D icon stats: {str(e)}"
        )


@app.post("/api/3d_icons/batch_generate")
async def batch_generate_3d_icons(request: dict):
    """Batch generate 3D icons for multiple devices"""
    try:
        icon_3d_service = get_3d_icon_service()

        # Extract SVG paths from request
        svg_paths = request.get("svg_paths", [])
        if not svg_paths:
            raise HTTPException(status_code=400, detail="No SVG paths provided")

        # Convert to required format: [(svg_path, device_type, device_name), ...]
        formatted_paths = []
        for item in svg_paths:
            if isinstance(item, dict):
                formatted_paths.append(
                    (
                        item.get("svg_path", ""),
                        item.get("device_type", "endpoint"),
                        item.get("device_name", "Unknown Device"),
                    )
                )
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                formatted_paths.append(
                    (item[0], item[1], item[2] if len(item) > 2 else "Unknown Device")
                )

        if not formatted_paths:
            raise HTTPException(status_code=400, detail="Invalid SVG paths format")

        # Batch generate icons
        result = await icon_3d_service.batch_generate_3d_icons(formatted_paths)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Batch generation failed: {str(e)}"
        )


@app.post("/api/3d_icons/cleanup")
async def cleanup_3d_icon_cache():
    """Clean up expired 3D icon cache entries"""
    try:
        icon_3d_service = get_3d_icon_service()
        removed_count = icon_3d_service.cleanup_expired_cache()
        return {
            "success": True,
            "removed_entries": removed_count,
            "message": f"Cleaned up {removed_count} expired cache entries",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache cleanup failed: {str(e)}")


@app.get("/api/3d_icons/generate/{device_type}")
async def generate_single_3d_icon(
    device_type: str, svg_path: str = "", device_name: str = ""
):
    """Generate a single 3D icon for testing"""
    try:
        icon_3d_service = get_3d_icon_service()

        # Use default SVG path if none provided
        if not svg_path:
            svg_path = f"app/static/icons/{device_type}.svg"

        if not device_name:
            device_name = f"{device_type.title()} Device"

        icon_3d_data = icon_3d_service.get_3d_icon_data(
            svg_path, device_type, device_name
        )
        return icon_3d_data

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"3D icon generation failed: {str(e)}"
        )


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
            "timestamp": redis_health.get("timestamp"),
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

        return {"redis_sessions": redis_info, "current_session": current_session}
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
            "message": f"Cleaned up {cleaned_count} expired sessions",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session cleanup failed: {str(e)}")


@app.delete("/api/session/current")
async def logout_current_session():
    """Logout the current FortiGate session"""
    try:
        session_manager = get_fortigate_redis_session_manager()
        session_manager.logout()
        return {"success": True, "message": "Current session logged out successfully"}
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
                "message": result.get("message", "Authentication test failed"),
            }
        else:
            return {
                "success": True,
                "message": "Session authentication working correctly",
                "data": {
                    "endpoint": "monitor/system/status",
                    "response_keys": (
                        list(result.keys())
                        if isinstance(result, dict)
                        else "non-dict response"
                    ),
                },
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session test failed: {str(e)}")


# ====================================================================
# Enhanced Topology Integration Endpoints (FortiGate-Visio-Topology)
# ====================================================================


@app.get("/api/enhanced-topology/2d")
async def api_enhanced_topology_2d():
    """
    Get enhanced 2D topology with LLDP, FortiSwitch, and FortiAP data.
    Uses FortiGate-Visio-Topology API for comprehensive network discovery.
    """
    try:
        topology_service = get_topology_integration_service()
        if not topology_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="Enhanced topology integration not available. Ensure FortiGate-Visio-Topology API is running.",
            )

        return topology_service.get_2d_topology_data()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get enhanced 2D topology: {str(e)}"
        )


@app.get("/api/enhanced-topology/3d")
async def api_enhanced_topology_3d():
    """
    Get enhanced 3D topology for 3d-force-graph visualization.
    Includes 3D positioning, colors, and model references.
    """
    try:
        topology_service = get_topology_integration_service()
        if not topology_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="Enhanced topology integration not available. Ensure FortiGate-Visio-Topology API is running.",
            )

        return topology_service.get_3d_topology_data()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get enhanced 3D topology: {str(e)}"
        )


@app.get("/api/enhanced-topology/hybrid")
async def api_enhanced_topology_hybrid():
    """
    Get hybrid topology format compatible with existing dashboard services.
    """
    try:
        topology_service = get_topology_integration_service()
        if not topology_service.is_available():
            raise HTTPException(
                status_code=503, detail="Enhanced topology integration not available"
            )

        return topology_service.get_hybrid_topology_data()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get hybrid topology: {str(e)}"
        )


@app.get("/api/enhanced-topology/statistics")
async def api_enhanced_topology_statistics():
    """
    Get topology statistics including device counts by type.
    """
    try:
        topology_service = get_topology_integration_service()
        return topology_service.get_device_statistics()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get statistics: {str(e)}"
        )


@app.get("/api/enhanced-topology/health")
async def api_enhanced_topology_health():
    """
    Check health of enhanced topology integration.
    """
    topology_service = get_topology_integration_service()
    return {
        "available": topology_service.is_available(),
        "service": "FortiGate-Visio-Topology Integration",
        "timestamp": datetime.now().isoformat(),
    }


# Performance Monitoring Endpoints
@app.get("/api/performance/metrics")
async def get_performance_metrics():
    """Get performance metrics including cache statistics and response times"""
    try:
        from app.services.response_cache_service import get_response_cache_service

        cache_service = get_response_cache_service()
        cache_stats = cache_service.get_stats()

        return {
            "cache": cache_stats,
            "timestamp": datetime.now().isoformat(),
            "optimization_enabled": True,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get performance metrics: {str(e)}"
        )


@app.get("/api/performance/cache/stats")
async def get_cache_stats():
    """Get detailed cache statistics"""
    try:
        from app.services.response_cache_service import get_response_cache_service

        cache_service = get_response_cache_service()
        return cache_service.get_stats()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get cache stats: {str(e)}"
        )


@app.post("/api/teach")
async def teach_recovery_agent(
    error_pattern: str,
    fix_description: str,
    category: str = "general",
    severity: str = "medium",
    auto_remediable: bool = False,
    context: str = None,
):
    """
    Teach the recovery agent a new error fix.

    External agents can use this endpoint to add new error patterns and fixes
    to the knowledge base. This enables the system to learn from new errors
    and improve its self-healing capabilities.

    Args:
        error_pattern: The error pattern to match (e.g., "SSL certificate error")
        fix_description: How to fix this error (e.g., "Regenerate certificate")
        category: Error category (e.g., 'ssl_errors', 'api_errors', 'docker_errors')
        severity: 'low', 'medium', 'high', or 'critical'
        auto_remediable: Whether this can be auto-fixed
        context: Optional additional context about when this fix applies

    Returns:
        Confirmation with knowledge base statistics
    """
    try:
        from extras.magentic_one_integration import NetworkPlatformTools

        tools = NetworkPlatformTools()
        result = tools.train_recovery_agent(
            error_pattern=error_pattern,
            fix_description=fix_description,
            category=category,
            severity=severity,
            auto_remediable=auto_remediable,
            context=context,
        )

        if result.get("success"):
            return result
        else:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to teach recovery agent"),
            )
    except Exception as e:
        logger.error(f"Error teaching recovery agent: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to teach recovery agent: {str(e)}"
        )


@app.post("/api/report-error")
async def report_error(
    error: str,
    category: str = "general",
    device: str = None,
    icon_path: str = None,
    device_type: str = None,
    model: str = None,
):
    """
    Report an error to the AI healer for diagnosis and potential auto-fix.

    This endpoint allows the frontend and other services to report errors
    so the AI healer can detect patterns and suggest or apply fixes.

    Args:
        error: Error message or description
        category: Error category (e.g., 'icon_loading', 'icon_missing', 'api_error')
        device: Device name (if applicable)
        icon_path: Icon path that failed (if applicable)
        device_type: Device type (if applicable)
        model: Device model (if applicable)

    Returns:
        Diagnosis result from AI healer
    """
    try:
        from app.services.ai_healer import get_ai_healer

        healer = get_ai_healer()
        diagnosis = healer.diagnose(error)

        # Log the error for monitoring
        logger.error(
            f"Error reported: {error} (category: {category}, device: {device})"
        )

        return {
            "reported": True,
            "error": error,
            "category": category,
            "diagnosis": diagnosis,
            "suggested_fix": (
                diagnosis["matches_found"][0]["fix"]
                if diagnosis["matches_found"]
                else None
            ),
            "auto_remediable": diagnosis.get("auto_remediable", False),
        }
    except Exception as e:
        logger.error(f"Failed to report error to AI healer: {e}")
        return {
            "reported": False,
            "error": f"Failed to report error: {str(e)}",
        }


@app.post("/api/performance/cache/clear")
async def clear_cache():
    """Clear all cached responses"""
    try:
        from app.services.response_cache_service import get_response_cache_service

        cache_service = get_response_cache_service()
        deleted_count = cache_service.clear_all()
        return {
            "success": True,
            "deleted_items": deleted_count,
            "message": f"Cleared {deleted_count} cached responses",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@app.get("/api/performance/test")
async def performance_test():
    """Test endpoint performance with timing"""
    start_time = time.time()

    try:
        from app.services.hybrid_topology_service_optimized import (
            get_hybrid_topology_service_optimized,
        )

        service = get_hybrid_topology_service_optimized()
        topology = await service.get_comprehensive_topology()

        elapsed_time = time.time() - start_time

        return {
            "success": True,
            "response_time_seconds": round(elapsed_time, 3),
            "switches_count": len(topology.get("switches", [])),
            "source": topology.get("source", "unknown"),
            "optimization": "async_parallel",
        }
    except Exception as e:
        elapsed_time = time.time() - start_time
        return {
            "success": False,
            "error": str(e),
            "response_time_seconds": round(elapsed_time, 3),
        }
