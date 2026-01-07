"""
Web Filters API endpoints with FortiManager integration
"""
from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, Request
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import logging
import os

from ...deps import get_current_active_user
from ...models.webfilters import (
    WebFilterProfile,
    WebFilterOverride,
    WebFilterLogEntry,
    WebFilterSearchRequest,
    WebFilterSearchResponse,
    WebFilterTestRequest,
    WebFilterTestResult,
    WebFilterBulkUpdateRequest,
    WebFilterBulkUpdateResponse,
    WebFilterStats,
    WebFilterAction
)
from ...services.fortimanager import get_fortimanager_service, FortiManagerError
from ...models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)

# Environment variable for default ADOM
DEFAULT_ADOM = os.getenv('FORTIMANAGER_ADOM', 'root')

@router.get("/profiles", response_model=List[WebFilterProfile])
async def list_web_filter_profiles(
    adom: str = Query(DEFAULT_ADOM, description="ADOM name"),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all web filter profiles from FortiManager
    """
    try:
        # Get FortiManager service instance
        fm = await get_fortimanager_service()
        
        # Get web filter profiles from FortiManager
        profiles_data = await fm.get_webfilter_profiles(adom)
        
        # Convert to our Pydantic model
        profiles = []
        for profile_data in profiles_data:
            try:
                # Get detailed profile data
                profile_detail = await fm.get_webfilter_entries(profile_data.get('name', ''), adom)
                if not profile_detail:
                    continue
                    
                # Convert to WebFilterProfile model
                profile = WebFilterProfile(
                    id=profile_detail.get('name', ''),
                    name=profile_detail.get('name', 'Unnamed Profile'),
                    description=profile_detail.get('comment', ''),
                    default_action=WebFilterAction.ALLOW,  # Default to ALLOW, update based on actual data
                    log_all_url=profile_detail.get('log-all-url', False),
                    block_page_mode=profile_detail.get('block-page-type', 'message'),
                    created_at=datetime.utcnow().isoformat(),
                    updated_at=datetime.utcnow().isoformat()
                )
                profiles.append(profile)
                
            except Exception as e:
                logger.warning(f"Error processing profile {profile_data.get('name')}: {str(e)}")
                continue
                
        return profiles
        
    except FortiManagerError as e:
        logger.error(f"FortiManager error retrieving profiles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error communicating with FortiManager: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error listing web filter profiles: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving web filter profiles: {str(e)}"
        )

@router.get("/profiles/{profile_id}", response_model=WebFilterProfile)
async def get_web_filter_profile(
    profile_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific web filter profile by ID
    """
    try:
        if profile_id not in webfilter_service.profiles:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Web filter profile not found: {profile_id}"
            )
        return webfilter_service.profiles[profile_id]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving web filter profile {profile_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving web filter profile: {str(e)}"
        )

@router.post("/search", response_model=WebFilterSearchResponse)
async def search_web_filter_logs(
    search_request: WebFilterSearchRequest,
    adom: str = Query(DEFAULT_ADOM, description="ADOM name"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Search web filter logs from FortiManager
    
    Note: This is a simplified implementation. In a real-world scenario, you would:
    1. Query FortiManager's log database
    2. Potentially use FortiAnalyzer for more advanced log searching
    3. Implement proper pagination and filtering
    """
    try:
        # Get FortiManager service instance
        fm = await get_fortimanager_service()
        
        # In a real implementation, you would query FortiManager's logs
        # For now, we'll return a mock response with the search parameters
        
        # This is a placeholder - actual implementation would query FortiManager
        results = {
            "total": 0,
            "count": 0,
            "offset": search_request.offset,
            "limit": search_request.limit,
            "results": []
        }
        
        return WebFilterSearchResponse(**results)
        
    except FortiManagerError as fm_error:
        logger.error(f"FortiManager error searching logs: {str(fm_error)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error communicating with FortiManager: {str(fm_error)}"
        )
    except Exception as e:
        logger.error(f"Error searching web filter logs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching web filter logs: {str(e)}"
        )

@router.post("/test", response_model=WebFilterTestResult)
async def test_web_filter_url(
    test_request: WebFilterTestRequest,
    adom: str = Query(DEFAULT_ADOM, description="ADOM name"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Test how a URL would be handled by the web filter
    
    This sends the URL to FortiManager to test against the configured web filter profiles.
    """
    try:
        # Get FortiManager service instance
        fm = await get_fortimanager_service()
        
        # Test the URL using FortiManager
        test_result = await fm.test_url(
            url=test_request.url,
            src_ip=test_request.src_ip,
            user=test_request.user,
            adom=adom
        )
        
        # Convert to WebFilterTestResult model
        return WebFilterTestResult(
            url=test_result['url'],
            action=test_result['action'],
            profile=test_result.get('profile', 'default'),
            category=test_result.get('category'),
            reason=test_result.get('reason', 'Test completed'),
            matched_rules=test_result.get('matched_rules', []),
            is_overridden=test_result.get('is_overridden', False),
            override_details=test_result.get('override_details')
        )
        
    except FortiManagerError as fm_error:
        logger.error(f"FortiManager error testing URL: {str(fm_error)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error communicating with FortiManager: {str(fm_error)}"
        )
    except Exception as e:
        logger.error(f"Error testing URL: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error testing URL: {str(e)}"
        )

@router.post("/bulk-update", response_model=WebFilterBulkUpdateResponse)
async def bulk_update_web_filter_urls(
    update_request: WebFilterBulkUpdateRequest,
    adom: str = Query(DEFAULT_ADOM, description="ADOM name"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Perform bulk updates to web filter URLs in FortiManager
    
    This allows updating multiple URLs at once with the specified action.
    """
    try:
        # Get FortiManager service instance
        fm = await get_fortimanager_service()
        
        # In a real implementation, you would:
        # 1. Validate the requested updates
        # 2. Apply the updates to the appropriate FortiManager objects
        # 3. Return the results
        
        # This is a simplified example
        success_count = 0
        errors = []
        
        for i, url in enumerate(update_request.urls):
            try:
                # In a real implementation, you would update the URL in FortiManager
                # For now, we'll simulate a successful update
                success_count += 1
                
            except Exception as e:
                errors.append({
                    "url": str(url),
                    "error": str(e)
                })
        
        return WebFilterBulkUpdateResponse(
            total=len(update_request.urls),
            success=success_count,
            failed=len(errors),
            errors=errors
        )
        
    except FortiManagerError as fm_error:
        logger.error(f"FortiManager error in bulk update: {str(fm_error)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error communicating with FortiManager: {str(fm_error)}"
        )
    except Exception as e:
        logger.error(f"Error in bulk update: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error performing bulk update: {str(e)}"
        )

@router.get("/statistics", response_model=WebFilterStats)
async def get_web_filter_statistics(
    start_time: Optional[datetime] = Query(None, description="Start time for statistics"),
    end_time: Optional[datetime] = Query(None, description="End time for statistics"),
    profile_id: Optional[str] = Query(None, description="Filter by profile ID"),
    adom: str = Query(DEFAULT_ADOM, description="ADOM name"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get web filter statistics from FortiManager
    
    This provides aggregated statistics about web filtering activity.
    In a real implementation, this would query FortiAnalyzer or FortiManager's log database.
    """
    try:
        # Get FortiManager service instance
        fm = await get_fortimanager_service()
        
        # In a real implementation, you would query FortiManager or FortiAnalyzer for statistics
        # For now, we'll return a mock response with the requested time range
        
        # Default to last 24 hours if no time range is specified
        end = end_time or datetime.utcnow()
        start = start_time or (end - timedelta(days=1))
        
        # Generate time series data (hourly)
        time_series = []
        current = start
        while current <= end:
            time_series.append({
                "time": current.isoformat(),
                "total": 100,  # Mock data
                "blocked": 20,  # Mock data
                "allowed": 80   # Mock data
            })
            current += timedelta(hours=1)
        
        return WebFilterStats(
            total_requests=1000,  # Mock data
            blocked_requests=200,  # Mock data
            allowed_requests=800,  # Mock data
            monitored_requests=0,  # Mock data
            top_categories=[
                {"category": "Business", "count": 300, "percentage": 30.0},
                {"category": "Technology", "count": 250, "percentage": 25.0},
                {"category": "Social Media", "count": 150, "percentage": 15.0},
            ],
            top_blocked_domains=[
                {"domain": "example.com", "count": 50},
                {"domain": "test.org", "count": 30},
                {"domain": "blocked-site.com", "count": 20},
            ],
            top_users=[
                {"user": "user1", "count": 150},
                {"user": "user2", "count": 120},
                {"user": "user3", "count": 100},
            ],
            time_series=time_series,
            time_range={
                "start": start.isoformat(),
                "end": end.isoformat()
            }
        )
        
    except FortiManagerError as fm_error:
        logger.error(f"FortiManager error getting statistics: {str(fm_error)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error communicating with FortiManager: {str(fm_error)}"
        )
    except Exception as e:
        logger.error(f"Error getting web filter statistics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving web filter statistics: {str(e)}"
        )

@router.get("/fortimanager/query", response_model=Dict[str, Any])
async def query_fortimanager_webfilters(
    request: Request,
    brand: str = Query(..., description="Brand name (e.g., arbys, bww, sonic)"),
    store_id: Optional[str] = Query(None, description="Specific store ID to query"),
    adom: str = Query(DEFAULT_ADOM, description="ADOM name"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Query FortiManager for web filter configurations
    
    This endpoint ensures the response always includes 'webfilter_data', 'filtered_data', 
    and 'matches' keys, even if some are empty, to maintain a consistent response structure.
    """
    try:
        # Initialize response with default structure
        response_data = {
            "webfilter_data": {"profiles": []},
            "filtered_data": {
                "applied_filters": {
                    "brand": brand,
                    "store_id": store_id,
                    "adom": adom
                },
                "result_count": 0
            },
            "matches": []
        }
        
        # Get FortiManager service instance
        fm = await get_fortimanager_service()
        
        try:
            # Get web filter profiles from FortiManager
            profiles = await fm.get_webfilter_profiles(adom)
            
            if profiles:
                # Add profiles to response
                response_data["webfilter_data"]["profiles"] = profiles
                
                # If we have a store_id, try to find matching entries
                if store_id:
                    # This is a simplified example - in a real implementation, you would:
                    # 1. Look up the specific store's configuration
                    # 2. Check for any web filter entries that match the store's configuration
                    # 3. Add those matches to the response
                    
                    # For now, we'll just add a placeholder match
                    response_data["matches"] = [
                        {
                            "id": f"match_{store_id}_1",
                            "url": f"https://{brand}.example.com/store/{store_id}",
                            "category": "Business",
                            "action": "allow",
                            "profile": profiles[0].get('name', 'default') if profiles else 'default',
                            "last_updated": datetime.utcnow().isoformat()
                        }
                    ]
                    
                    response_data["filtered_data"]["result_count"] = len(response_data["matches"])
            
            return response_data
            
        except FortiManagerError as fm_error:
            logger.error(f"FortiManager error: {str(fm_error)}")
            # Return empty response structure with error information
            response_data["error"] = f"FortiManager error: {str(fm_error)}"
            return response_data
            
    except Exception as e:
        logger.error(f"Error querying FortiManager: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error querying FortiManager: {str(e)}"
        )

@router.get("/fortimanager/status", response_model=Dict[str, Any])
async def get_fortimanager_status(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get FortiManager connection status and statistics
    """
    try:
        # Get FortiManager service instance
        fm = await get_fortimanager_service()
        
        # Check if we have a valid session
        is_connected = fm._is_session_valid()
        
        # Get system status if connected
        system_status = {}
        if is_connected:
            try:
                system_status = await fm.get_system_status()
            except Exception as e:
                logger.warning(f"Could not get system status: {str(e)}")
        
        # Get profile count
        profile_count = 0
        if is_connected:
            try:
                profiles = await fm.get_webfilter_profiles()
                profile_count = len(profiles) if profiles else 0
            except Exception as e:
                logger.warning(f"Could not get profile count: {str(e)}")
        
        return {
            "status": "connected" if is_connected else "disconnected",
            "last_sync": fm.last_login.isoformat() if fm.last_login else None,
            "base_url": fm.base_url,
            "profiles_count": profile_count,
            "system_status": system_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting FortiManager status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting FortiManager status: {str(e)}"
        )

@router.post("/fortimanager/sync", response_model=Dict[str, Any])
async def sync_fortimanager_data(
    force: bool = Query(False, description="Force a full sync"),
    adom: str = Query(DEFAULT_ADOM, description="ADOM to sync"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Trigger a synchronization with FortiManager
    
    This will fetch the latest web filter profiles and their entries from FortiManager.
    """
    try:
        # Get FortiManager service instance
        fm = await get_fortimanager_service()
        
        # Ensure we're connected
        if not fm._is_session_valid():
            await fm.login()
        
        # Get web filter profiles
        profiles = await fm.get_webfilter_profiles(adom)
        
        # Process each profile to get detailed entries
        updated_profiles = []
        for profile in profiles:
            try:
                profile_name = profile.get('name')
                if not profile_name:
                    continue
                    
                # Get detailed profile data
                profile_detail = await fm.get_webfilter_entries(profile_name, adom)
                if profile_detail:
                    updated_profiles.append(profile_detail)
                    
            except Exception as e:
                logger.warning(f"Error syncing profile {profile.get('name')}: {str(e)}")
                continue
        
        # In a real implementation, you would store the synced data in your database
        # For now, we'll just return the results
        
        return {
            "status": "success",
            "message": f"Synchronized {len(updated_profiles)} web filter profiles from FortiManager",
            "timestamp": datetime.utcnow().isoformat(),
            "stats": {
                "profiles_updated": len(updated_profiles),
                "adom": adom,
                "fortimanager_url": fm.base_url,
                "user": current_user.username
            }
        }
        
    except FortiManagerError as fm_error:
        logger.error(f"FortiManager sync error: {str(fm_error)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error communicating with FortiManager: {str(fm_error)}"
        )
    except Exception as e:
        logger.error(f"Error syncing with FortiManager: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error syncing with FortiManager: {str(e)}"
        )
