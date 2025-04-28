from fastapi import APIRouter, HTTPException
from app.services.fortigate_service import get_interfaces
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
