""
Pydantic models for FortiGate API
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

class FortiGateStatus(str, Enum):
    UP = "up"
    DOWN = "down"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"

class FortiGateInterface(BaseModel):
    """FortiGate interface model"""
    name: str = Field(..., description="Interface name")
    alias: Optional[str] = Field(None, description="Interface alias/description")
    ip: Optional[str] = Field(None, description="IP address with subnet mask")
    status: FortiGateStatus = Field(FortiGateStatus.UNKNOWN, description="Interface status")
    speed: Optional[str] = Field(None, description="Interface speed")
    mtu: Optional[int] = Field(None, description="MTU size")
    vdom: Optional[str] = Field("root", description="VDOM name")
    type: Optional[str] = Field(None, description="Interface type (physical, vlan, etc.)")

class FortiGateVLAN(BaseModel):
    """FortiGate VLAN model"""
    id: int = Field(..., description="VLAN ID (1-4094)")
    name: str = Field(..., description="VLAN name")
    interface: str = Field(..., description="Parent interface")
    ip: Optional[str] = Field(None, description="IP address with subnet mask")
    status: FortiGateStatus = Field(FortiGateStatus.UNKNOWN, description="VLAN status")
    vdom: Optional[str] = Field("root", description="VDOM name")

class FortiGatePolicy(BaseModel):
    """FortiGate firewall policy model"""
    id: int = Field(..., description="Policy ID")
    name: str = Field(..., description="Policy name")
    srcintf: List[str] = Field(..., description="Source interfaces")
    dstintf: List[str] = Field(..., description="Destination interfaces")
    srcaddr: List[str] = Field(..., description="Source addresses")
    dstaddr: List[str] = Field(..., description="Destination addresses")
    service: List[str] = Field(..., description="Services")
    action: str = Field(..., description="Action (accept/deny)")
    status: str = Field("enable", description="Policy status")
    vdom: Optional[str] = Field("root", description="VDOM name")

class FortiGateVPNStatus(str, Enum):
    UP = "up"
    DOWN = "down"
    NEGOTIATING = "negotiating"
    UNKNOWN = "unknown"

class FortiGateVPNTunnel(BaseModel):
    """FortiGate VPN tunnel model"""
    name: str = Field(..., description="Tunnel name")
    status: FortiGateVPNStatus = Field(FortiGateVPNStatus.UNKNOWN, description="Tunnel status")
    type: str = Field(..., description="Tunnel type (ipsec, ssl, etc.)")
    local_gw: Optional[str] = Field(None, description="Local gateway IP")
    remote_gw: Optional[str] = Field(None, description="Remote gateway IP")
    ike_version: Optional[int] = Field(None, description="IKE version (1 or 2)")
    vdom: Optional[str] = Field("root", description="VDOM name")

class FortiGateSystemStatus(BaseModel):
    """FortiGate system status model"""
    hostname: str = Field(..., description="Device hostname")
    model: str = Field(..., description="Device model")
    version: str = Field(..., description="Firmware version")
    serial: Optional[str] = Field(None, description="Serial number")
    uptime: int = Field(..., description="Uptime in seconds")
    cpu_usage: float = Field(..., description="CPU usage percentage")
    mem_usage: float = Field(..., description="Memory usage percentage")
    disk_usage: float = Field(..., description="Disk usage percentage")
    vdom: Optional[str] = Field("root", description="VDOM name")

class FortiGateLogEntry(BaseModel):
    """FortiGate log entry model"""
    timestamp: datetime = Field(..., description="Log timestamp")
    log_id: int = Field(..., description="Log ID")
    type: str = Field(..., description="Log type (traffic, event, etc.)")
    subtype: Optional[str] = Field(None, description="Log subtype")
    level: str = Field(..., description="Log level (information, warning, error, etc.)")
    msg: str = Field(..., description="Log message")
    src_ip: Optional[str] = Field(None, description="Source IP address")
    dst_ip: Optional[str] = Field(None, description="Destination IP address")
    user: Optional[str] = Field(None, description="User associated with the log entry")
    action: Optional[str] = Field(None, description="Action taken")

class FortiGateCommandRequest(BaseModel):
    """Request model for executing FortiGate commands"""
    command: str = Field(..., description="CLI command to execute")
    vdom: Optional[str] = Field("root", description="VDOM context")
    timeout: int = Field(30, description="Command timeout in seconds")

class FortiGateCommandResponse(BaseModel):
    """Response model for command execution"""
    success: bool = Field(..., description="Command execution status")
    output: str = Field(..., description="Command output")
    error: Optional[str] = Field(None, description="Error message if command failed")
    execution_time: float = Field(..., description="Command execution time in seconds")
