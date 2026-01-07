"""
FortiGate API endpoints with real FortiGate device integration
"""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request

from ...deps import get_current_active_user
from ...models.fortigate import (
    FortiGateInterface,
    FortiGateVLAN,
    FortiGatePolicy,
    FortiGateVPNTunnel,
    FortiGateSystemStatus,
    FortiGateLogEntry,
    FortiGateCommandRequest,
    FortiGateCommandResponse
)
from ...services.fortigate import get_fortigate_service, FortiGateError
from ...models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/devices", response_model=List[Dict[str, Any]])
async def list_fortigate_devices(
    current_user: User = Depends(get_current_active_user)
):
    """
    List all managed FortiGate devices
    
    Note: In a real implementation, this would query a device inventory service or database.
    For now, it returns a single device based on configuration.
    """
    try:
        # In a real implementation, you would query a device inventory service
        # For now, we'll return the configured FortiGate device
        from ...core.config import settings
        
        if not settings.FORTIGATE_HOST:
            return []
            
        return [{
            "name": settings.FORTIGATE_HOST,
            "ip": settings.FORTIGATE_HOST,
            "api_enabled": True,
            "reachable": True
        }]
        
    except Exception as e:
        logger.error(f"Error retrieving FortiGate devices: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving FortiGate devices: {str(e)}"
        )

@router.get("/{device_name}/status", response_model=FortiGateSystemStatus)
async def get_device_status(
    device_name: str,
    vdom: str = Query("root", description="VDOM name"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get system status of a FortiGate device
    """
    try:
        # Get FortiGate service instance
        async with await get_fortigate_service() as fgt:
            # Get system status
            system_status = await fgt.get_system_status()
            
            # Get HA status
            try:
                ha_status = await fgt.get_system_ha_status()
                if ha_status.get('ha_member'):
                    system_status.ha_status = ha_status['ha_member'][0].get('state', 'unknown')
                    system_status.ha_group = ha_status.get('group_id', 0)
            except Exception as ha_err:
                logger.warning(f"Could not retrieve HA status: {str(ha_err)}")
            
            return system_status
            
    except FortiGateError as fgt_err:
        logger.error(f"FortiGate error getting status: {str(fgt_err)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error communicating with FortiGate: {str(fgt_err)}"
        )
    except Exception as e:
        logger.error(f"Error retrieving device status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving device status: {str(e)}"
        )

@router.get("/{device_name}/interfaces", response_model=List[FortiGateInterface])
async def get_interfaces(
    device_name: str,
    vdom: str = Query("root", description="VDOM name"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all interfaces of a FortiGate device
    
    Returns a list of all interfaces with their current status and configuration.
    """
    try:
        async with await get_fortigate_service() as fgt:
            interfaces = await fgt.get_interfaces()
            return interfaces
            
    except FortiGateError as fgt_err:
        logger.error(f"FortiGate error getting interfaces: {str(fgt_err)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error communicating with FortiGate: {str(fgt_err)}"
        )
    except Exception as e:
        logger.error(f"Error retrieving interfaces: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving interfaces: {str(e)}"
        )

@router.get("/{device_name}/vlans", response_model=List[FortiGateVLAN])
async def get_vlans(
    device_name: str,
    vdom: str = Query("root", description="VDOM name"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all VLANs configured on a FortiGate device
    
    Returns a list of all VLAN interfaces with their configuration.
    """
    try:
        async with await get_fortigate_service() as fgt:
            vlans = await fgt.get_vlans()
            return [vlan for vlan in vlans if vlan.vdom == vdom or not vlan.vdom]
            
    except FortiGateError as fgt_err:
        logger.error(f"FortiGate error getting VLANs: {str(fgt_err)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error communicating with FortiGate: {str(fgt_err)}"
        )
    except Exception as e:
        logger.error(f"Error retrieving VLANs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving VLANs: {str(e)}"
        )

@router.post("/{device_name}/command", response_model=FortiGateCommandResponse)
async def execute_command(
    device_name: str,
    request: FortiGateCommandRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Execute a CLI command on a FortiGate device
    
    Note: This endpoint allows executing arbitrary CLI commands on the FortiGate.
    Use with caution as this can modify the device configuration.
    """
    try:
        # Get FortiGate service instance
        async with await get_fortigate_service() as fgt:
            # Execute the command
            result = await fgt.execute_command(
                command=request.command,
                vdom=request.vdom or "root"
            )
            
            # Log the command execution (without sensitive data)
            logger.info(f"Executed command on {device_name}: {request.command[:100]}...")
            
            return result
            
    except FortiGateError as fgt_err:
        logger.error(f"FortiGate command error: {str(fgt_err)}")
        return FortiGateCommandResponse(
            success=False,
            command=request.command,
            output="",
            error=str(fgt_err),
            execution_time=0.0
        )
    except Exception as e:
        logger.error(f"Error executing command: {str(e)}", exc_info=True)
        return FortiGateCommandResponse(
            success=False,
            command=request.command,
            output="",
            error=str(e),
            execution_time=0.0
        )

@router.get("/{device_name}/vpn/tunnels", response_model=List[FortiGateVPNTunnel])
async def get_vpn_tunnels(
    device_name: str,
    vdom: str = Query("root", description="VDOM name"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all VPN tunnels on a FortiGate device
    
    Returns a list of all configured VPN tunnels with their current status.
    """
    try:
        async with await get_fortigate_service() as fgt:
            # Get all VPN tunnels
            tunnels = await fgt.get_vpn_tunnels()
            
            # Filter by VDOM if specified
            if vdom and vdom.lower() != "root":
                tunnels = [t for t in tunnels if t.vdom == vdom]
                
            return tunnels
            
    except FortiGateError as fgt_err:
        logger.error(f"FortiGate error getting VPN tunnels: {str(fgt_err)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error communicating with FortiGate: {str(fgt_err)}"
        )
    except Exception as e:
        logger.error(f"Error retrieving VPN tunnels: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving VPN tunnels: {str(e)}"
        )

@router.get("/{device_name}/policies", response_model=List[FortiGatePolicy])
async def get_policies(
    device_name: str,
    vdom: str = Query("root", description="VDOM name"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all firewall policies on a FortiGate device
    """
    try:
        # Implementation would go here
        return [
            {
                "id": 1,
                "name": "LAN to WAN",
                "srcintf": ["port2"],
                "dstintf": ["port1"],
                "srcaddr": ["all"],
                "dstaddr": ["all"],
                "service": ["ALL"],
                "action": "accept",
                "status": "enable",
                "vdom": vdom
            },
            {
                "id": 2,
                "name": "Block Malware",
                "srcintf": ["any"],
                "dstintf": ["any"],
                "srcaddr": ["all"],
                "dstaddr": ["all"],
                "service": ["HTTP", "HTTPS", "DNS"],
                "action": "deny",
                "status": "enable",
                "vdom": vdom
            }
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving policies: {str(e)}"
        )
