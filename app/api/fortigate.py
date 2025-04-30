from fastapi import APIRouter, HTTPException
from app.services.fortigate_service import get_interfaces
from app.services.fortiswitch_service import get_fortiswitches
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