""
Pydantic models for FortiManager API
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class FortiManagerInstance(BaseModel):
    """FortiManager instance model"""
    name: str = Field(..., description="Name of the FortiManager instance")
    ip: str = Field(..., description="IP address or hostname of the FortiManager")
    version: str = Field(..., description="Firmware version")
    description: Optional[str] = Field(None, description="Optional description")
    port: int = Field(443, description="Port number (default: 443)")
    verify_ssl: bool = Field(False, description="Verify SSL certificate")

class ADOM(BaseModel):
    """ADOM (Administrative Domain) model"""
    name: str = Field(..., description="Name of the ADOM")
    version: str = Field(..., description="FortiOS version for this ADOM")
    os_version: Optional[str] = Field(None, description="OS version")
    desc: Optional[str] = Field(None, description="Description")
    created: Optional[str] = Field(None, description="Creation timestamp")
    modified: Optional[str] = Field(None, description="Last modified timestamp")

class FortiManagerDevice(BaseModel):
    """FortiManager managed device model"""
    name: str = Field(..., description="Device name")
    ip: str = Field(..., description="IP address")
    model: str = Field(..., description="Device model")
    version: str = Field(..., description="Firmware version")
    adom: str = Field(..., description="ADOM name")
    serial: Optional[str] = Field(None, description="Serial number")
    last_checkin: Optional[str] = Field(None, description="Last check-in time")
    status: Optional[str] = Field(None, description="Device status")

class PolicyPackage(BaseModel):
    """Policy package model"""
    name: str = Field(..., description="Package name")
    type: str = Field(..., description="Package type (e.g., pkg, folder)")
    adom: Optional[str] = Field(None, description="ADOM name")
    package_path: Optional[str] = Field(None, description="Full package path")
    created: Optional[str] = Field(None, description="Creation timestamp")
    modified: Optional[str] = Field(None, description="Last modified timestamp")

class InstallPolicyRequest(BaseModel):
    """Request model for installing a policy package"""
    package_name: str = Field(..., description="Name of the policy package to install")
    target_devices: List[str] = Field(..., description="List of target device names")
    adom: str = Field("root", description="ADOM name")
    vdom: str = Field("root", description="VDOM name")
    flags: Optional[Dict[str, bool]] = Field(
        None,
        description="Installation flags (e.g., {'create_policy_packages': True})"
    )
    description: Optional[str] = Field(None, description="Installation description")

class InstallPolicyResponse(BaseModel):
    """Response model for policy installation"""
    status: str = Field(..., description="Installation status")
    message: Optional[str] = Field(None, description="Status message")
    task_id: Optional[str] = Field(None, description="Task ID for tracking")

class FortiManagerTaskStatus(str, Enum):
    """Task status enum"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class FortiManagerTask(BaseModel):
    """Task model for async operations"""
    task_id: str = Field(..., description="Task ID")
    status: FortiManagerTaskStatus = Field(..., description="Task status")
    progress: int = Field(0, description="Progress percentage (0-100)")
    result: Optional[Dict[str, Any]] = Field(None, description="Task result")
    error: Optional[str] = Field(None, description="Error message if failed")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
