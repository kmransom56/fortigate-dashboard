"""
Pydantic models for Web Filters
"""
from pydantic import BaseModel, Field, HttpUrl, validator
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from datetime import datetime

class WebFilterAction(str, Enum):
    BLOCK = "block"
    ALLOW = "allow"
    MONITOR = "monitor"
    WARN = "warn"
    AUTHENTICATE = "authenticate"
    QUARANTINE = "quarantine"

class WebFilterCategory(BaseModel):
    """Web filter category model"""
    id: int = Field(..., description="Category ID")
    name: str = Field(..., description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    type: str = Field(..., description="Category type (e.g., 'custom', 'predefined')")

class WebFilterProfile(BaseModel):
    """Web filter profile model"""
    id: str = Field(..., description="Profile ID")
    name: str = Field(..., description="Profile name")
    description: Optional[str] = Field(None, description="Profile description")
    categories: List[WebFilterCategory] = Field(
        default_factory=list, 
        description="List of categories in this profile"
    )
    default_action: WebFilterAction = Field(
        WebFilterAction.BLOCK, 
        description="Default action for uncategorized URLs"
    )
    log_all_url: bool = Field(
        False, 
        description="Whether to log all URL accesses"
    )
    block_page_mode: str = Field(
        "message", 
        description="Block page mode (message, redirect, etc.)"
    )
    block_page_contents: Optional[str] = Field(
        None, 
        description="Custom block page contents (if block_page_mode is 'message')"
    )
    redirect_url: Optional[HttpUrl] = Field(
        None, 
        description="Redirect URL (if block_page_mode is 'redirect')"
    )
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="User who created the profile")
    updated_by: Optional[str] = Field(None, description="User who last updated the profile")

class WebFilterOverride(BaseModel):
    """Web filter override model"""
    id: str = Field(..., description="Override ID")
    name: str = Field(..., description="Override name")
    description: Optional[str] = Field(None, description="Override description")
    status: str = Field("enabled", description="Override status (enabled/disabled)")
    ip: Optional[str] = Field(
        None, 
        description="Source IP address or range (CIDR notation)"
    )
    user: Optional[str] = Field(
        None, 
        description="Username for user-based override"
    )
    user_group: Optional[str] = Field(
        None, 
        description="User group for group-based override"
    )
    profile: str = Field(..., description="Profile ID to apply")
    schedule: Optional[str] = Field(
        "always", 
        description="Schedule when this override is active"
    )
    expires_at: Optional[datetime] = Field(
        None, 
        description="Expiration timestamp for temporary overrides"
    )
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="User who created the override")
    updated_by: Optional[str] = Field(None, description="User who last updated the override")

class WebFilterLogEntry(BaseModel):
    """Web filter log entry model"""
    id: str = Field(..., description="Log entry ID")
    timestamp: datetime = Field(..., description="When the access occurred")
    src_ip: str = Field(..., description="Source IP address")
    user: Optional[str] = Field(None, description="Username (if authenticated)")
    url: HttpUrl = Field(..., description="Accessed URL")
    hostname: str = Field(..., description="Hostname of the accessed URL")
    path: str = Field(..., description="Path of the accessed URL")
    method: str = Field(..., description="HTTP method (GET, POST, etc.)")
    action: WebFilterAction = Field(..., description="Action taken")
    profile: str = Field(..., description="Profile that triggered the action")
    category: Optional[str] = Field(None, description="Category of the URL")
    reason: Optional[str] = Field(None, description="Reason for the action")
    user_agent: Optional[str] = Field(None, description="User agent string")
    referrer: Optional[HttpUrl] = Field(None, description="Referrer URL")
    bytes_sent: Optional[int] = Field(None, description="Bytes sent in response")
    bytes_received: Optional[int] = Field(None, description="Bytes received in request")
    session_id: Optional[str] = Field(None, description="Session ID")

class WebFilterSearchRequest(BaseModel):
    """Request model for searching web filter logs"""
    query: Optional[str] = Field(
        None, 
        description="Search query (searches URL, hostname, username, etc.)"
    )
    start_time: Optional[datetime] = Field(
        None, 
        description="Start time for log search"
    )
    end_time: Optional[datetime] = Field(
        None, 
        description="End time for log search"
    )
    src_ip: Optional[str] = Field(
        None, 
        description="Filter by source IP address"
    )
    user: Optional[str] = Field(
        None, 
        description="Filter by username"
    )
    action: Optional[WebFilterAction] = Field(
        None, 
        description="Filter by action taken"
    )
    category: Optional[str] = Field(
        None, 
        description="Filter by category"
    )
    profile: Optional[str] = Field(
        None, 
        description="Filter by profile ID"
    )
    limit: int = Field(
        100, 
        ge=1, 
        le=1000, 
        description="Maximum number of results to return"
    )
    offset: int = Field(
        0, 
        ge=0, 
        description="Offset for pagination"
    )

class WebFilterSearchResponse(BaseModel):
    """Response model for web filter search"""
    total: int = Field(..., description="Total number of matching records")
    count: int = Field(..., description="Number of records in this response")
    offset: int = Field(..., description="Offset for pagination")
    limit: int = Field(..., description="Maximum number of results per page")
    results: List[WebFilterLogEntry] = Field(
        default_factory=list, 
        description="Matching log entries"
    )

class WebFilterTestRequest(BaseModel):
    """Request model for testing web filter rules"""
    url: HttpUrl = Field(..., description="URL to test")
    src_ip: Optional[str] = Field(
        None, 
        description="Source IP address for testing"
    )
    user: Optional[str] = Field(
        None, 
        description="Username for user-based testing"
    )
    user_group: Optional[str] = Field(
        None, 
        description="User group for group-based testing"
    )
    profile: Optional[str] = Field(
        None, 
        description="Specific profile to test against (default: use matching profile)"
    )

class WebFilterTestResult(BaseModel):
    """Result of a web filter test"""
    url: HttpUrl = Field(..., description="Tested URL")
    action: WebFilterAction = Field(..., description="Action that would be taken")
    profile: Optional[str] = Field(
        None, 
        description="Profile that triggered the action"
    )
    category: Optional[str] = Field(
        None, 
        description="Category of the URL"
    )
    reason: Optional[str] = Field(
        None, 
        description="Reason for the action"
    )
    matched_rules: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="Rules that matched the URL"
    )
    is_overridden: bool = Field(
        False, 
        description="Whether an override affected the result"
    )
    override_details: Optional[Dict[str, Any]] = Field(
        None, 
        description="Details of any applicable override"
    )

class WebFilterBulkUpdateRequest(BaseModel):
    """Request model for bulk updating web filter entries"""
    action: WebFilterAction = Field(..., description="Action to apply")
    urls: List[HttpUrl] = Field(
        ..., 
        min_items=1, 
        description="URLs to update"
    )
    category: Optional[str] = Field(
        None, 
        description="Category to assign (if action is 'categorize')"
    )
    profile: Optional[str] = Field(
        None, 
        description="Profile to apply (if action is 'add-to-profile' or 'remove-from-profile')"
    )
    comment: Optional[str] = Field(
        None, 
        description="Comment for the update"
    )

class WebFilterBulkUpdateResponse(BaseModel):
    """Response model for bulk update operations"""
    total: int = Field(..., description="Total number of URLs processed")
    success: int = Field(..., description="Number of successful updates")
    failed: int = Field(..., description="Number of failed updates")
    errors: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="Details of any errors"
    )

class WebFilterStats(BaseModel):
    """Web filter statistics"""
    total_requests: int = Field(..., description="Total number of requests")
    blocked_requests: int = Field(..., description="Number of blocked requests")
    allowed_requests: int = Field(..., description="Number of allowed requests")
    monitored_requests: int = Field(..., description="Number of monitored requests")
    top_categories: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="Top categories by request count"
    )
    top_blocked_domains: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="Top blocked domains"
    )
    top_users: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="Top users by request count"
    )
    time_series: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="Time series data for graphing"
    )
    time_range: Dict[str, datetime] = Field(
        ..., 
        description="Start and end times for the statistics"
    )
