from fastapi import APIRouter, HTTPException, Query
from app.services.fortigate_service import get_interfaces
from app.services.fortiswitch_service import get_fortiswitches
from app.services.mac_vendors import get_vendor_from_mac, refresh_vendor_cache as refresh_cache
import logging
from pydantic import BaseModel
from app.services.fortiswitch_service import get_fortiswitches, change_fortiswitch_ip

class SwitchIPChangeRequest(BaseModel):
    switch_serial: str
    new_ip: str
    new_netmask: str = "255.255.255.0"

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/fortigate/api/interfaces")
async def get_fortigate_interfaces():
    try:
        logger.debug("API endpoint /fortigate/api/interfaces called")
        interfaces = get_interfaces()
        return interfaces
    except Exception as e:
        logger.error(f"Error in /fortigate/api/interfaces endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fortigate/api/switches")
async def get_fortigate_switches():
    try:
        logger.debug("API endpoint /fortigate/api/switches called")
        switches = get_fortiswitches()
        return switches
    except Exception as e:
        logger.error(f"Error in /fortigate/api/switches endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/switches")
async def get_switches():
    """
    Get information about all FortiSwitches.
    """
    try:
        switches = get_fortiswitches()
        return {"success": True, "switches": switches}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/lookup-vendor")
async def lookup_vendor(mac: str = Query(..., description="MAC address to look up")):
    """
    Look up vendor information for a MAC address.
    """
    try:
        # Force online lookup
        vendor = get_vendor_from_mac(mac, use_online_lookup=True)
        if vendor:
            return {"success": True, "vendor": vendor}
        else:
            return {"success": False, "error": "Vendor not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/refresh-vendor-cache")
async def refresh_vendor_cache():
    """
    Refresh the vendor cache by clearing expired entries.
    """
    try:
        refresh_cache()
        return {"success": True, "message": "Vendor cache refreshed successfully"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/fortigate/api/switches/change-ip")
async def change_switch_ip(request: SwitchIPChangeRequest):
    try:
        logger.debug(f"API endpoint /fortigate/api/switches/change-ip called for switch {request.switch_serial}")
        result = change_fortiswitch_ip(
            request.switch_serial,
            request.new_ip,
            request.new_netmask
        )
        
        if not result.get("success", False):
            logger.error(f"Failed to change IP for switch {request.switch_serial}: {result.get('message')}")
            raise HTTPException(status_code=400, detail=result.get("message", "Unknown error"))
            
        return result
    except Exception as e:
        logger.error(f"Error in /fortigate/api/switches/change-ip endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))