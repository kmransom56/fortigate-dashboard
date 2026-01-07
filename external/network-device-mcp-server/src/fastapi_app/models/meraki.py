""
Pydantic models for Meraki API
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from datetime import datetime

class MerakiDeviceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    ALERTING = "alerting"
    DORMANT = "dormant"

class MerakiDeviceType(str, Enum):
    APPLIANCE = "appliance"
    SWITCH = "switch"
    WIRELESS = "wireless"
    SENSOR = "sensor"
    CAMERA = "camera"
    SYSTEMS_MANAGER = "systemsManager"
    CELLULAR_GATEWAY = "cellularGateway"

class MerakiNetwork(BaseModel):
    """Meraki network model"""
    id: str = Field(..., description="Network ID")
    organization_id: str = Field(..., description="Organization ID")
    name: str = Field(..., description="Network name")
    product_types: List[str] = Field(..., description="List of product types")
    time_zone: str = Field(..., description="Time zone")
    tags: List[str] = Field(default_factory=list, description="Network tags")
    enrollment_string: Optional[str] = Field(None, description="Enrollment string")
    is_bound_to_config_template: bool = Field(False, description="Is bound to config template")
    notes: Optional[str] = Field(None, description="Notes")

class MerakiDevice(BaseModel):
    """Meraki device model"""
    serial: str = Field(..., description="Device serial number")
    mac: Optional[str] = Field(None, description="MAC address")
    name: Optional[str] = Field(None, description="Device name")
    model: str = Field(..., description="Device model")
    address: Optional[str] = Field(None, description="Physical address")
    lat: Optional[float] = Field(None, description="Latitude")
    lng: Optional[float] = Field(None, description="Longitude")
    network_id: Optional[str] = Field(None, description="Network ID")
    firmware: Optional[str] = Field(None, description="Firmware version")
    device_type: Optional[MerakiDeviceType] = Field(None, description="Device type")
    tags: List[str] = Field(default_factory=list, description="Tags")

class MerakiClient(BaseModel):
    """Meraki client device model"""
    id: str = Field(..., description="Client ID")
    mac: str = Field(..., description="MAC address")
    description: Optional[str] = Field(None, description="Description")
    ip: Optional[str] = Field(None, description="IP address")
    user: Optional[str] = Field(None, description="Username")
    vlan: Optional[int] = Field(None, description="VLAN")
    switchport: Optional[Dict[str, Any]] = Field(None, description="Switch port details")
    wireless_capabilities: Optional[str] = Field(None, description="Wireless capabilities")
    os: Optional[str] = Field(None, description="Operating system")
    device_type_prediction: Optional[Dict[str, Any]] = Field(None, description="Device type prediction")
    recent_device_serial: Optional[str] = Field(None, description="Recent device serial")
    status: str = Field(..., description="Online status")
    last_seen: Optional[datetime] = Field(None, description="Last seen timestamp")

class MerakiSSID(BaseModel):
    """Meraki SSID model"""
    number: int = Field(..., description="SSID number")
    name: str = Field(..., description="SSID name")
    enabled: bool = Field(..., description="SSID status")
    auth_mode: str = Field(..., description="Authentication mode")
    encryption_mode: str = Field(..., description="Encryption mode")
    wpa_encryption_mode: Optional[str] = Field(None, description="WPA encryption mode")
    visible: bool = Field(..., description="SSID visibility")
    ip_assignment_mode: Optional[str] = Field(None, description="IP assignment mode")
    min_bitrate: Optional[int] = Field(None, description="Minimum bitrate")
    band_selection: Optional[str] = Field(None, description="Band selection")
    per_client_bandwidth_limit_up: Optional[int] = Field(None, description="Upload bandwidth limit per client in Kbps")
    per_client_bandwidth_limit_down: Optional[int] = Field(None, description="Download bandwidth limit per client in Kbps")

class MerakiVLAN(BaseModel):
    """Meraki VLAN model"""
    id: str = Field(..., description="VLAN ID")
    network_id: str = Field(..., description="Network ID")
    name: str = Field(..., description="VLAN name")
    subnet: str = Field(..., description="Subnet")
    appliance_ip: str = Field(..., description="Appliance IP")
    dns_nameservers: Optional[str] = Field(None, description="DNS nameservers")
    dhcp_handling: Optional[str] = Field(None, description="DHCP handling mode")
    dhcp_lease_time: Optional[str] = Field(None, description="DHCP lease time")
    dhcp_boot_options_enabled: Optional[bool] = Field(None, description="DHCP boot options enabled")
    dhcp_boot_next_server: Optional[str] = Field(None, description="DHCP boot next server")
    dhcp_boot_filename: Optional[str] = Field(None, description="DHCP boot filename")

class MerakiTrafficRule(BaseModel):
    """Meraki traffic rule model"""
    comment: Optional[str] = Field(None, description="Rule comment")
    policy: str = Field(..., description="Rule policy (allow/deny)")
    protocol: str = Field(..., description="Protocol (tcp/udp/icmp/any)")
    src_port: Optional[str] = Field(None, description="Source port")
    src_cidr: str = Field(..., description="Source CIDR")
    dest_port: Optional[str] = Field(None, description="Destination port")
    dest_cidr: str = Field(..., description="Destination CIDR")
    syslog_enabled: Optional[bool] = Field(False, description="Enable syslog")

class MerakiAlert(BaseModel):
    """Meraki alert model"""
    id: str = Field(..., description="Alert ID")
    type: str = Field(..., description="Alert type")
    network_id: str = Field(..., description="Network ID")
    device_serial: Optional[str] = Field(None, description="Device serial number")
    device_name: Optional[str] = Field(None, description="Device name")
    alert_level: Optional[str] = Field(None, description="Alert level")
    occurred_at: datetime = Field(..., description="When the alert occurred")
    alert_data: Dict[str, Any] = Field(..., description="Alert data")

class MerakiClientOverview(BaseModel):
    """Meraki client overview model"""
    total: int = Field(..., description="Total clients")
    online: int = Field(..., description="Online clients")
    offline: int = Field(..., description="Offline clients")
    by_os: Dict[str, int] = Field(..., description="Clients by OS")
    by_device_type: Dict[str, int] = Field(..., description="Clients by device type")
    by_ssid: Dict[str, int] = Field(..., description="Clients by SSID")
    by_vlan: Dict[str, int] = Field(..., description="Clients by VLAN")
