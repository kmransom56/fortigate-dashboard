"""
API v1 router configuration
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional

from ..deps import get_current_active_user
from .endpoints import (
    fortimanager,
    fortigate,
    meraki,
    vlans,
    fortiaps,
    utilities,
    dashboard,
    fortianalyzer,
    webfilters,
    ltm
)

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(fortimanager.router, prefix="/fortimanager", tags=["FortiManager"])
api_router.include_router(fortigate.router, prefix="/fortigate", tags=["FortiGate"])
api_router.include_router(meraki.router, prefix="/meraki", tags=["Meraki"])
api_router.include_router(vlans.router, prefix="/vlans", tags=["VLANs"])
api_router.include_router(fortiaps.router, prefix="/fortiaps", tags=["FortiAPs"])
api_router.include_router(utilities.router, prefix="/utilities", tags=["Utilities"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(fortianalyzer.router, prefix="/fortianalyzer", tags=["FortiAnalyzer"])
api_router.include_router(webfilters.router, prefix="/webfilters", tags=["Web Filters"])
api_router.include_router(ltm.router, prefix="/ltm", tags=["LTM Intelligence"])
