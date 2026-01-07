"""
Meraki API endpoints with real Meraki Dashboard integration
"""
import logging
from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from datetime import datetime, timedelta

from ...deps import get_current_active_user
from ...models.meraki import (
    MerakiOrganization,
    MerakiNetwork,
    MerakiDevice,
    MerakiClient,
    MerakiSSID,
    MerakiVLAN,
    MerakiTraffic,
    MerakiAlert,
    MerakiWebhook,
    MerakiClientOverview,
    MerakiDeviceStatus,
    MerakiDeviceType
)
from ...services.meraki import get_meraki_service, MerakiError
from ...models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/organizations", response_model=List[MerakiOrganization])
async def list_organizations(
    current_user: User = Depends(get_current_active_user)
):
    """
    List all Meraki organizations accessible by the API key
    """
    try:
        async with await get_meraki_service() as meraki:
            return await meraki.get_organizations()
            
    except MerakiError as meraki_err:
        logger.error(f"Meraki API error: {str(meraki_err)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error communicating with Meraki: {str(meraki_err)}"
        )
    except Exception as e:
        logger.error(f"Error retrieving organizations: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving organizations: {str(e)}"
        )

@router.get("/networks", response_model=List[MerakiNetwork])
async def list_networks(
    organization_id: str = Query(..., description="Organization ID"),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all networks in an organization
    """
    try:
        async with await get_meraki_service() as meraki:
            # First verify the organization exists and is accessible
            try:
                org = await meraki.get_organization(organization_id)
                logger.debug(f"Found organization: {org.name}")
            except MerakiError as e:
                if "not found" in str(e).lower():
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Organization {organization_id} not found or access denied"
                    )
                raise
                
            # Get all networks for the organization
            networks = await meraki.get_networks(organization_id)
            return networks
            
    except HTTPException:
        raise
    except MerakiError as meraki_err:
        logger.error(f"Meraki API error: {str(meraki_err)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error communicating with Meraki: {str(meraki_err)}"
        )
    except Exception as e:
        logger.error(f"Error retrieving networks: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving networks: {str(e)}"
        )

@router.get("/networks/{network_id}/devices", response_model=List[MerakiDevice])
async def get_network_devices(
    network_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    List all devices in a network
    """
    try:
        async with await get_meraki_service() as meraki:
            # First verify the network exists and is accessible
            try:
                network = await meraki.get_network(network_id)
                logger.debug(f"Found network: {network.name}")
            except MerakiError as e:
                if "not found" in str(e).lower():
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Network {network_id} not found or access denied"
                    )
                raise
                
            # Get all devices for the network
            devices = await meraki.get_devices(network_id)
            return devices
            
    except HTTPException:
        raise
    except MerakiError as meraki_err:
        logger.error(f"Meraki API error: {str(meraki_err)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error communicating with Meraki: {str(meraki_err)}"
        )
    except Exception as e:
        logger.error(f"Error retrieving network devices: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving network devices: {str(e)}"
        )

@router.get("/networks/{network_id}/clients", response_model=List[MerakiClient])
async def get_network_clients(
    network_id: str,
    timespan: int = Query(86400, description="Time range in seconds to look up clients"),
    per_page: int = Query(10, description="Number of entries per page"),
    starting_after: Optional[str] = Query(None, description="A token used to retrieve the next page of results"),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all clients in a network within the specified timespan
    
    Returns a paginated list of clients that have used the network in the timespan.
    """
    try:
        async with await get_meraki_service() as meraki:
            # Get clients with pagination and timespan filter
            filters = {
                'timespan': timespan,
                'per_page': min(per_page, 1000),  # Enforce max page size
            }
            if starting_after:
                filters['starting_after'] = starting_after
                
            clients = await meraki.get_clients(network_id, **filters)
            return clients
            
    except MerakiError as meraki_err:
        logger.error(f"Meraki API error: {str(meraki_err)}")
        if "not found" in str(meraki_err).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Network {network_id} not found or access denied"
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error communicating with Meraki: {str(meraki_err)}"
        )
    except Exception as e:
        logger.error(f"Error retrieving network clients: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving network clients: {str(e)}"
        )

@router.get("/networks/{network_id}/ssids", response_model=List[MerakiSSID])
async def get_network_ssids(
    network_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    List all SSIDs in a network
    """
    try:
        # Mock SSIDs data
        return [
            {
                "number": 0,
                "name": "Corporate Wifi",
                "enabled": True,
                "auth_mode": "wpa2-enterprise",
                "encryption_mode": "wpa2",
                "wpa_encryption_mode": "WPA2 only",
                "visible": True,
                "ip_assignment_mode": "NAT mode",
                "min_bitrate": 11,
                "band_selection": "Dual band operation",
                "per_client_bandwidth_limit_up": 1000,
                "per_client_bandwidth_limit_down": 5000
            },
            {
                "number": 1,
                "name": "Guest Wifi",
                "enabled": True,
                "auth_mode": "wpa2-psk",
                "encryption_mode": "wpa",
                "wpa_encryption_mode": "WPA2 only",
                "visible": True,
                "ip_assignment_mode": "Bridge mode",
                "min_bitrate": 11,
                "band_selection": "5 GHz band only",
                "per_client_bandwidth_limit_up": 1000,
                "per_client_bandwidth_limit_down": 1000
            }
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving SSIDs: {str(e)}"
        )

@router.get("/networks/{network_id}/vlans", response_model=List[MerakiVLAN])
async def get_network_vlans(
    network_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    List all VLANs in a network
    """
    try:
        # Mock VLANs data
        return [
            {
                "id": "10",
                "network_id": network_id,
                "name": "Corporate",
                "subnet": "192.168.10.0/24",
                "appliance_ip": "192.168.10.1",
                "dhcp_handling": "Run a DHCP server"
            },
            {
                "id": "20",
                "network_id": network_id,
                "name": "Guest",
                "subnet": "192.168.20.0/24",
                "appliance_ip": "192.168.20.1",
                "dhcp_handling": "Run a DHCP server"
            }
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving VLANs: {str(e)}"
        )

@router.get("/networks/{network_id}/alerts", response_model=List[MerakiAlert])
async def get_network_alerts(
    network_id: str,
    timespan: int = Query(3600, description="Time range in seconds to look up alerts"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get alerts for a network
    """
    try:
        # Mock alerts data
        return [
            {
                "id": "12345",
                "type": "gatewayDown",
                "network_id": network_id,
                "device_serial": "Q2XX-XXXX-XXXX",
                "device_name": "NYC-MX64",
                "alert_level": "critical",
                "occurred_at": datetime.utcnow() - timedelta(minutes=30),
                "alert_data": {
                    "reason": "Device is unreachable",
                    "url": "https://dashboard.meraki.com/n/12345/nodes/device?serial=Q2XX-XXXX-XXXX"
                }
            },
            {
                "id": "12346",
                "type": "rogueAp",
                "network_id": network_id,
                "alert_level": "warning",
                "occurred_at": datetime.utcnow() - timedelta(hours=1),
                "alert_data": {
                    "ssid": "Free Public Wifi",
                    "channel": 6,
                    "rssi": -65
                }
            }
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving alerts: {str(e)}"
        )

@router.get("/networks/{network_id}/clients/overview", response_model=MerakiClientOverview)
async def get_clients_overview(
    network_id: str,
    timespan: int = Query(86400, description="Time range in seconds to look up clients"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get client overview statistics for a network
    """
    try:
        # Mock client overview data
        return {
            "total": 42,
            "online": 35,
            "offline": 7,
            "by_os": {
                "iOS": 15,
                "Windows": 10,
                "macOS": 8,
                "Android": 7,
                "Other": 2
            },
            "by_device_type": {
                "Smartphone": 20,
                "Laptop": 12,
                "Tablet": 5,
                "IoT": 3,
                "Other": 2
            },
            "by_ssid": {
                "Corporate Wifi": 30,
                "Guest Wifi": 5
            },
            "by_vlan": {
                "10": 30,
                "20": 5
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving client overview: {str(e)}"
        )
