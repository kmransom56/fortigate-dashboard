"""
Pydantic models for VLAN management
"""
from pydantic import BaseModel, Field, IPv4Address, IPv4Network, validator
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from ipaddress import ip_network, ip_address

class VLANStatus(str, Enum):
    ACTIVE = "active"
    PLANNED = "planned"
    DEPRECATED = "deprecated"
    MAINTENANCE = "maintenance"

class VLANType(str, Enum):
    DATA = "data"
    VOICE = "voice"
    GUEST = "guest"
    MANAGEMENT = "management"
    STORAGE = "storage"
    MIGRATION = "migration"
    BACKUP = "backup"
    INFRASTRUCTURE = "infrastructure"
    OTHER = "other"

class VLANRoutingProtocol(str, Enum):
    STATIC = "static"
    OSPF = "ospf"
    BGP = "bgp"
    EIGRP = "eigrp"
    RIP = "rip"

class VLANBase(BaseModel):
    """Base VLAN model with common attributes"""
    vlan_id: int = Field(..., ge=1, le=4094, description="VLAN ID (1-4094)")
    name: str = Field(..., max_length=64, description="VLAN name")
    description: Optional[str] = Field(None, max_length=255, description="VLAN description")
    status: VLANStatus = Field(VLANStatus.ACTIVE, description="VLAN status")
    vlan_type: VLANType = Field(VLANType.DATA, description="Type of VLAN")
    site_id: Optional[str] = Field(None, description="Site/building identifier")
    notes: Optional[str] = Field(None, description="Additional notes")

class VLANCreate(VLANBase):
    """Model for creating a new VLAN"""
    network: IPv4Network = Field(..., description="IPv4 network in CIDR notation")
    gateway: IPv4Address = Field(..., description="Default gateway IP address")
    dhcp_server: Optional[IPv4Address] = Field(None, description="DHCP server IP address")
    dns_servers: List[IPv4Address] = Field(
        default_factory=list,
        description="List of DNS server IP addresses"
    )
    routing_protocol: VLANRoutingProtocol = Field(
        VLANRoutingProtocol.STATIC,
        description="Routing protocol used for this VLAN"
    )
    vrf: Optional[str] = Field(None, description="VRF name")
    mtu: int = Field(1500, ge=68, le=9216, description="MTU size")

    @validator('gateway')
    def gateway_must_be_in_network(cls, v, values):
        if 'network' in values and v not in values['network'].hosts():
            raise ValueError('Gateway must be an IP address within the network')
        return v

    @validator('dhcp_server')
    def dhcp_server_must_be_in_network(cls, v, values):
        if v is not None and 'network' in values and v not in values['network'].hosts():
            raise ValueError('DHCP server must be an IP address within the network')
        return v

    @validator('dns_servers')
    def dns_servers_must_be_valid(cls, v, values):
        if 'network' not in values:
            return v
            
        invalid_ips = [str(ip) for ip in v if ip not in values['network'].hosts()]
        if invalid_ips:
            raise ValueError(f'DNS servers must be IP addresses within the network. Invalid: {", ".join(invalid_ips)}')
        return v

class VLANUpdate(BaseModel):
    """Model for updating an existing VLAN"""
    name: Optional[str] = Field(None, max_length=64, description="VLAN name")
    description: Optional[str] = Field(None, max_length=255, description="VLAN description")
    status: Optional[VLANStatus] = Field(None, description="VLAN status")
    vlan_type: Optional[VLANType] = Field(None, description="Type of VLAN")
    site_id: Optional[str] = Field(None, description="Site/building identifier")
    notes: Optional[str] = Field(None, description="Additional notes")
    gateway: Optional[IPv4Address] = Field(None, description="Default gateway IP address")
    dhcp_server: Optional[IPv4Address] = Field(None, description="DHCP server IP address")
    dns_servers: Optional[List[IPv4Address]] = Field(
        None,
        description="List of DNS server IP addresses"
    )
    routing_protocol: Optional[VLANRoutingProtocol] = Field(
        None,
        description="Routing protocol used for this VLAN"
    )
    vrf: Optional[str] = Field(None, description="VRF name")
    mtu: Optional[int] = Field(None, ge=68, le=9216, description="MTU size")

class VLANInDB(VLANBase):
    """VLAN model as stored in the database"""
    id: str = Field(..., description="Unique identifier")
    network: IPv4Network = Field(..., description="IPv4 network in CIDR notation")
    gateway: IPv4Address = Field(..., description="Default gateway IP address")
    dhcp_server: Optional[IPv4Address] = Field(None, description="DHCP server IP address")
    dns_servers: List[IPv4Address] = Field(
        default_factory=list,
        description="List of DNS server IP addresses"
    )
    routing_protocol: VLANRoutingProtocol = Field(
        VLANRoutingProtocol.STATIC,
        description="Routing protocol used for this VLAN"
    )
    vrf: Optional[str] = Field(None, description="VRF name")
    mtu: int = Field(1500, ge=68, le=9216, description="MTU size")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    created_by: str = Field(..., description="User who created the VLAN")
    updated_by: str = Field(..., description="User who last updated the VLAN")

    class Config:
        json_encoders = {
            IPv4Network: str,
            IPv4Address: str
        }

class VLANPortAssignment(BaseModel):
    """Model for assigning a VLAN to a switch port"""
    device_id: str = Field(..., description="Switch/device identifier")
    port_id: str = Field(..., description="Port identifier")
    port_mode: str = Field("access", description="Port mode (access, trunk, general)")
    native_vlan: Optional[int] = Field(None, description="Native VLAN for trunk ports")
    allowed_vlans: Optional[List[int]] = Field(
        None,
        description="List of allowed VLANs for trunk/general mode"
    )
    description: Optional[str] = Field(None, description="Port description")

class VLANUsageStats(BaseModel):
    """Model for VLAN usage statistics"""
    total_ips: int = Field(..., description="Total number of IP addresses in the VLAN")
    used_ips: int = Field(..., description="Number of used IP addresses")
    available_ips: int = Field(..., description="Number of available IP addresses")
    utilization_percent: float = Field(..., description="IP address utilization percentage")
    last_updated: str = Field(..., description="Timestamp of last update")

class VLANSummary(VLANInDB):
    """Extended VLAN model with usage statistics"""
    usage: Optional[VLANUsageStats] = Field(None, description="IP address usage statistics")
    assigned_ports: List[VLANPortAssignment] = Field(
        default_factory=list,
        description="List of ports where this VLAN is assigned"
    )

class VLANSite(BaseModel):
    """Model for a site with VLAN assignments"""
    id: str = Field(..., description="Site identifier")
    name: str = Field(..., description="Site name")
    vlans: List[VLANSummary] = Field(
        default_factory=list,
        description="List of VLANs assigned to this site"
    )

class VLANBulkCreateResponse(BaseModel):
    """Response model for bulk VLAN creation"""
    created: int = Field(..., description="Number of VLANs created")
    skipped: int = Field(..., description="Number of VLANs skipped")
    errors: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of errors encountered during creation"
    )
    vlan_ids: List[str] = Field(
        default_factory=list,
        description="IDs of created VLANs"
    )

class VLANSearchFilter(BaseModel):
    """Model for filtering VLAN searches"""
    vlan_ids: Optional[List[int]] = Field(None, description="Filter by VLAN IDs")
    status: Optional[List[VLANStatus]] = Field(None, description="Filter by status")
    vlan_type: Optional[List[VLANType]] = Field(None, description="Filter by VLAN type")
    site_id: Optional[str] = Field(None, description="Filter by site ID")
    network: Optional[str] = Field(None, description="Filter by network (CIDR notation)")
    vrf: Optional[str] = Field(None, description="Filter by VRF")
    search: Optional[str] = Field(
        None,
        description="Search term (searches name, description, and notes)"
    )
