from fastapi import APIRouter, HTTPException, Query
from app.services.fortigate_service import get_interfaces
from app.services.fortiswitch_service import get_fortiswitches
from app.services.mac_vendors import get_vendor_from_mac, refresh_vendor_cache as refresh_cache
import logging
from pydantic import BaseModel
from app.services.fortiswitch_service import get_fortiswitches, change_fortiswitch_ip
import requests
from app.services.fortiswitch_service import FORTIGATE_HOST, API_TOKEN

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

@router.get("/api/switches")
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


@router.get("/fortigate/api/arp")
async def get_arp_table():
    """
    Fetch ARP table data from FortiGate.
    """
    try:
        url = f"https://{FORTIGATE_HOST}/api/v2/monitor/network/arp"
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        response = requests.get(url, headers=headers, verify=False)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return response.json()
    except Exception as e:
        logger.error(f"Error fetching ARP table: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fortigate/api/detected-devices")
async def get_detected_devices():
    """
    Fetch detected device data from FortiGate.
    """
    try:
        url = (
            f"https://{FORTIGATE_HOST}/api/v2/monitor/switch-controller/detected-device"
        )
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        response = requests.get(url, headers=headers, verify=False)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return response.json()
    except Exception as e:
        logger.error(f"Error fetching detected devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fortigate/api/system-status")
async def get_system_status():
    """
    Fetch system status information from FortiGate.
    """
    try:
        url = f"https://{FORTIGATE_HOST}/api/v2/monitor/system/status"
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        response = requests.get(url, headers=headers, verify=False)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return response.json()
    except Exception as e:
        logger.error(f"Error fetching system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fortigate/api/switch-port-statistics")
async def get_switch_port_statistics():
    """
    Fetch detailed statistics for FortiSwitch ports.
    """
    try:
        url = f"https://{FORTIGATE_HOST}/api/v2/monitor/switch-controller/port"
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        response = requests.get(url, headers=headers, verify=False)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return response.json()
    except Exception as e:
        logger.error(f"Error fetching switch port statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fortigate/api/device-classification")
async def classify_device(mac: str = Query(..., description="MAC address to classify")):
    """
    Classify a device based on its MAC address.
    """
    try:
        vendor = get_vendor_from_mac(mac)
        if vendor:
            return {"success": True, "vendor": vendor}
        else:
            return {"success": False, "error": "Vendor not found"}
    except Exception as e:
        logger.error(f"Error classifying device: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fortigate/api/firewall-policies")
async def get_firewall_policies():
    """
    Fetch firewall policies from FortiGate.
    """
    try:
        url = f"https://{FORTIGATE_HOST}/api/v2/cmdb/firewall/policy"
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        response = requests.get(url, headers=headers, verify=False)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return response.json()
    except Exception as e:
        logger.error(f"Error fetching firewall policies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fortigate/api/logs")
async def get_logs():
    """
    Fetch logs from FortiGate.
    """
    try:
        url = f"https://{FORTIGATE_HOST}/api/v2/monitor/log/event"
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        response = requests.get(url, headers=headers, verify=False)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return response.json()
    except Exception as e:
        logger.error(f"Error fetching logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/network/arp")
async def get_ipv4_arp_table():
    """
    Get IPv4 ARP table.
    """
    try:
        url = f"https://{FORTIGATE_HOST}/api/v2/monitor/network/arp"
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        response = requests.get(url, headers=headers, verify=False)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return response.json()
    except Exception as e:
        logger.error(f"Error fetching IPv4 ARP table: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/network/lldp/neighbors")
async def get_lldp_neighbors():
    """
    List all active LLDP neighbors.
    """
    try:
        url = f"https://{FORTIGATE_HOST}/api/v2/monitor/network/lldp/neighbors"
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        response = requests.get(url, headers=headers, verify=False)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return response.json()
    except Exception as e:
        logger.error(f"Error fetching LLDP neighbors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/network/lldp/ports")
async def get_lldp_ports():
    """
    List all active LLDP ports.
    """
    try:
        url = f"https://{FORTIGATE_HOST}/api/v2/monitor/network/lldp/ports"
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        response = requests.get(url, headers=headers, verify=False)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return response.json()
    except Exception as e:
        logger.error(f"Error fetching LLDP ports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/network/dns/latency")
async def get_dns_latency():
    """
    Get DNS latency.
    """
    try:
        url = f"https://{FORTIGATE_HOST}/api/v2/monitor/network/dns/latency"
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        response = requests.get(url, headers=headers, verify=False)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return response.json()
    except Exception as e:
        logger.error(f"Error fetching DNS latency: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/network/fortiguard/live-services-latency")
async def get_fortiguard_latency():
    """
    Get latency information for live FortiGuard services.
    """
    try:
        url = f"https://{FORTIGATE_HOST}/api/v2/monitor/network/fortiguard/live-services-latency"
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        response = requests.get(url, headers=headers, verify=False)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return response.json()
    except Exception as e:
        logger.error(f"Error fetching FortiGuard latency: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/network/ddns/servers")
async def get_ddns_servers():
    """
    Get DDNS servers.
    """
    try:
        url = f"https://{FORTIGATE_HOST}/api/v2/monitor/network/ddns/servers"
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        response = requests.get(url, headers=headers, verify=False)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return response.json()
    except Exception as e:
        logger.error(f"Error fetching DDNS servers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/network/ddns/lookup")
async def check_ddns_fqdn_availability():
    """
    Check DDNS FQDN availability.
    """
    try:
        url = f"https://{FORTIGATE_HOST}/api/v2/monitor/network/ddns/lookup"
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        response = requests.get(url, headers=headers, verify=False)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return response.json()
    except Exception as e:
        logger.error(f"Error checking DDNS FQDN availability: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/network/reverse-ip-lookup")
async def reverse_ip_lookup():
    """
    Retrieve the resolved DNS domain name for a given IP address.
    """
    try:
        url = f"https://{FORTIGATE_HOST}/api/v2/monitor/network/reverse-ip-lookup"
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        response = requests.get(url, headers=headers, verify=False)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return response.json()
    except Exception as e:
        logger.error(f"Error performing reverse IP lookup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/network/debug-flow/start")
async def start_debug_flow():
    """
    Start debug flow packet capture.
    """
    try:
        url = f"https://{FORTIGATE_HOST}/api/v2/monitor/network/debug-flow/start"
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        response = requests.post(url, headers=headers, verify=False)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return response.json()
    except Exception as e:
        logger.error(f"Error starting debug flow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/network/debug-flow/stop")
async def stop_debug_flow():
    """
    Stop debug flow packet capture.
    """
    try:
        url = f"https://{FORTIGATE_HOST}/api/v2/monitor/network/debug-flow/stop"
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        response = requests.post(url, headers=headers, verify=False)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return response.json()
    except Exception as e:
        logger.error(f"Error stopping debug flow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/dashboard-data")
async def get_dashboard_data():
    """
    Aggregate data for the unified dashboard.
    """
    try:
        # Fetch data from various endpoints
        interfaces = get_interfaces()
        switches = get_fortiswitches()
        arp_table = await get_arp_table()
        detected_devices = await get_detected_devices()
        system_status = await get_system_status()

        # Combine data into a single response
        dashboard_data = {
            "interfaces": interfaces,
            "switches": switches,
            "arp_table": arp_table,
            "detected_devices": detected_devices,
            "system_status": system_status,
        }

        return {"success": True, "data": dashboard_data}
    except Exception as e:
        logger.error(f"Error aggregating dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
