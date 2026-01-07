"""
VLAN Management API endpoints
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from fastapi.responses import JSONResponse
from datetime import datetime
import ipaddress

from ...deps import get_current_active_user
from ...models.vlan import (
    VLANCreate,
    VLANUpdate,
    VLANInDB,
    VLANSummary,
    VLANPortAssignment,
    VLANUsageStats,
    VLANSite,
    VLANBulkCreateResponse,
    VLANSearchFilter,
    VLANStatus,
    VLANType,
    VLANRoutingProtocol
)
from ...models.user import User

router = APIRouter()

# Mock data store (replace with database in production)
vlan_db = {}
port_assignments = {}

# Helper functions
def generate_vlan_id() -> str:
    """Generate a unique VLAN ID"""
    return f"vlan_{len(vlan_db) + 1}"

def calculate_usage_stats(network: str) -> VLANUsageStats:
    """Calculate IP address usage statistics"""
    net = ipaddress.IPv4Network(network, strict=False)
    total_ips = net.num_addresses - 2  # Exclude network and broadcast
    used_ips = 10  # Mock value - in reality, this would come from DHCP leases or IPAM
    available_ips = max(0, total_ips - used_ips)
    utilization = (used_ips / total_ips) * 100 if total_ips > 0 else 0
    
    return VLANUsageStats(
        total_ips=total_ips,
        used_ips=used_ips,
        available_ips=available_ips,
        utilization_percent=round(utilization, 2),
        last_updated=datetime.utcnow().isoformat()
    )

@router.post("/vlans", response_model=VLANInDB, status_code=status.HTTP_201_CREATED)
async def create_vlan(
    vlan: VLANCreate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new VLAN
    """
    try:
        # Check if VLAN ID already exists
        for v in vlan_db.values():
            if v.vlan_id == vlan.vlan_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"VLAN with ID {vlan.vlan_id} already exists"
                )
        
        # Create new VLAN
        vlan_id = generate_vlan_id()
        now = datetime.utcnow().isoformat()
        
        vlan_data = VLANInDB(
            id=vlan_id,
            **vlan.dict(),
            created_at=now,
            updated_at=now,
            created_by=current_user.username,
            updated_by=current_user.username
        )
        
        vlan_db[vlan_id] = vlan_data
        return vlan_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating VLAN: {str(e)}"
        )

@router.get("/vlans", response_model=List[VLANSummary])
async def list_vlans(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user)
):
    """
    List all VLANs with pagination
    """
    try:
        # In a real application, this would query the database with pagination
        vlans = list(vlan_db.values())[skip:skip + limit]
        
        # Add usage stats to each VLAN
        result = []
        for vlan in vlans:
            usage = calculate_usage_stats(str(vlan.network))
            assigned_ports = [
                p for p in port_assignments.values() 
                if str(vlan.vlan_id) in [str(vid) for vid in (p.allowed_vlans or [])] or 
                   (p.port_mode == "access" and vlan.vlan_id == p.native_vlan)
            ]
            
            vlan_summary = VLANSummary(
                **vlan.dict(),
                usage=usage,
                assigned_ports=assigned_ports
            )
            result.append(vlan_summary)
            
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving VLANs: {str(e)}"
        )

@router.get("/vlans/{vlan_id}", response_model=VLANSummary)
async def get_vlan(
    vlan_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific VLAN by ID
    """
    try:
        if vlan_id not in vlan_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"VLAN {vlan_id} not found"
            )
            
        vlan = vlan_db[vlan_id]
        usage = calculate_usage_stats(str(vlan.network))
        
        # Find port assignments for this VLAN
        assigned_ports = [
            p for p in port_assignments.values() 
            if str(vlan.vlan_id) in [str(vid) for vid in (p.allowed_vlans or [])] or 
               (p.port_mode == "access" and vlan.vlan_id == p.native_vlan)
        ]
        
        return VLANSummary(
            **vlan.dict(),
            usage=usage,
            assigned_ports=assigned_ports
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving VLAN: {str(e)}"
        )

@router.put("/vlans/{vlan_id}", response_model=VLANInDB)
async def update_vlan(
    vlan_id: str,
    vlan_update: VLANUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a VLAN
    """
    try:
        if vlan_id not in vlan_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"VLAN {vlan_id} not found"
            )
            
        # Get existing VLAN data
        existing_vlan = vlan_db[vlan_id]
        
        # Update fields
        update_data = vlan_update.dict(exclude_unset=True)
        updated_vlan = existing_vlan.copy(update=update_data)
        updated_vlan.updated_at = datetime.utcnow().isoformat()
        updated_vlan.updated_by = current_user.username
        
        # Save updated VLAN
        vlan_db[vlan_id] = updated_vlan
        
        return updated_vlan
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating VLAN: {str(e)}"
        )

@router.delete("/vlans/{vlan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vlan(
    vlan_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a VLAN
    """
    try:
        if vlan_id not in vlan_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"VLAN {vlan_id} not found"
            )
            
        # Check if VLAN is in use
        vlan = vlan_db[vlan_id]
        assigned_ports = [
            p for p in port_assignments.values() 
            if str(vlan.vlan_id) in [str(vid) for vid in (p.allowed_vlans or [])] or 
               (p.port_mode == "access" and vlan.vlan_id == p.native_vlan)
        ]
        
        if assigned_ports:
            port_list = ", ".join([f"{p.device_id}/{p.port_id}" for p in assigned_ports])
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete VLAN {vlan_id} - it is assigned to ports: {port_list}"
            )
            
        # Delete the VLAN
        del vlan_db[vlan_id]
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting VLAN: {str(e)}"
        )

@router.post("/vlans/bulk-create", response_model=VLANBulkCreateResponse)
async def bulk_create_vlans(
    vlans: List[VLANCreate],
    current_user: User = Depends(get_current_active_user)
):
    """
    Create multiple VLANs in a single operation
    """
    response = VLANBulkCreateResponse()
    
    for vlan in vlans:
        try:
            # Check if VLAN ID already exists
            vlan_exists = any(v.vlan_id == vlan.vlan_id for v in vlan_db.values())
            if vlan_exists:
                response.skipped += 1
                response.errors.append({
                    "vlan_id": vlan.vlan_id,
                    "error": f"VLAN with ID {vlan.vlan_id} already exists"
                })
                continue
                
            # Create new VLAN
            vlan_id = generate_vlan_id()
            now = datetime.utcnow().isoformat()
            
            vlan_data = VLANInDB(
                id=vlan_id,
                **vlan.dict(),
                created_at=now,
                updated_at=now,
                created_by=current_user.username,
                updated_by=current_user.username
            )
            
            vlan_db[vlan_id] = vlan_data
            response.created += 1
            response.vlan_ids.append(vlan_id)
            
        except Exception as e:
            response.skipped += 1
            response.errors.append({
                "vlan_id": vlan.vlan_id if hasattr(vlan, 'vlan_id') else 'unknown',
                "error": str(e)
            })
    
    return response

@router.post("/vlans/assign-port", status_code=status.HTTP_200_OK)
async def assign_vlan_to_port(
    assignment: VLANPortAssignment,
    current_user: User = Depends(get_current_active_user)
):
    """
    Assign a VLAN to a switch port
    """
    try:
        # In a real application, this would configure the actual network device
        port_key = f"{assignment.device_id}:{assignment.port_id}"
        port_assignments[port_key] = assignment
        
        return {"status": "success", "message": f"VLAN assigned to port {port_key}"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error assigning VLAN to port: {str(e)}"
        )

@router.get("/vlans/sites/{site_id}", response_model=VLANSite)
async def get_site_vlans(
    site_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all VLANs assigned to a specific site
    """
    try:
        # In a real application, this would query the database
        site_vlans = [v for v in vlan_db.values() if v.site_id == site_id]
        
        # Add usage stats to each VLAN
        vlan_summaries = []
        for vlan in site_vlans:
            usage = calculate_usage_stats(str(vlan.network))
            vlan_summaries.append(VLANSummary(
                **vlan.dict(),
                usage=usage,
                assigned_ports=[]  # This would be populated in a real implementation
            ))
        
        return VLANSite(
            id=site_id,
            name=f"Site {site_id}",  # In a real app, this would come from a sites table
            vlans=vlan_summaries
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving site VLANs: {str(e)}"
        )

@router.post("/vlans/search", response_model=List[VLANSummary])
async def search_vlans(
    filter: VLANSearchFilter,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user)
):
    """
    Search for VLANs based on various filters
    """
    try:
        # Start with all VLANs
        results = list(vlan_db.values())
        
        # Apply filters
        if filter.vlan_ids:
            results = [v for v in results if v.vlan_id in filter.vlan_ids]
            
        if filter.status:
            results = [v for v in results if v.status in filter.status]
            
        if filter.vlan_type:
            results = [v for v in results if v.vlan_type in filter.vlan_type]
            
        if filter.site_id:
            results = [v for v in results if v.site_id == filter.site_id]
            
        if filter.network:
            try:
                target_net = ipaddress.IPv4Network(filter.network, strict=False)
                results = [
                    v for v in results 
                    if ipaddress.IPv4Network(str(v.network), strict=False).overlaps(target_net)
                ]
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid network format. Use CIDR notation (e.g., 192.168.1.0/24)"
                )
                
        if filter.vrf:
            results = [v for v in results if v.vrf == filter.vrf]
            
        if filter.search:
            search_lower = filter.search.lower()
            results = [
                v for v in results
                if (search_lower in v.name.lower() or
                    (v.description and search_lower in v.description.lower()) or
                    (v.notes and search_lower in v.notes.lower()))
            ]
        
        # Apply pagination
        paginated_results = results[skip:skip + limit]
        
        # Add usage stats to each VLAN
        vlan_summaries = []
        for vlan in paginated_results:
            usage = calculate_usage_stats(str(vlan.network))
            vlan_summaries.append(VLANSummary(
                **vlan.dict(),
                usage=usage,
                assigned_ports=[]  # This would be populated in a real implementation
            ))
        
        return vlan_summaries
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching VLANs: {str(e)}"
        )
