from fastapi import APIRouter, HTTPException
from app.services.fortigate_service import get_interfaces
from app.services.fortiswitch_service import get_fortiswitches
import logging

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
