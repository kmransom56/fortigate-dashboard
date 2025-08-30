"""
3D Asset Management Service

Manages 3D assets for the topology visualization, including:
- 3D model generation from 2D icons
- Asset caching and optimization
- Fallback 3D representations
- Enhanced visual effects
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import hashlib

from .eraser_service import generate_3d_from_image, is_enabled

logger = logging.getLogger(__name__)

class Asset3DManager:
    """Manages 3D assets for topology visualization"""
    
    def __init__(self, cache_dir="app/data/3d_assets"):
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, "asset_cache.json")
        self.cache = self._load_cache()
        
        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)
    
    def _load_cache(self) -> Dict[str, Any]:
        """Load asset cache from disk"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    logger.info(f"Loaded {len(data)} cached 3D assets")
                    return data
        except Exception as e:
            logger.warning(f"Could not load 3D asset cache: {e}")
        return {}
    
    def _save_cache(self):
        """Save asset cache to disk"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save 3D asset cache: {e}")
    
    def _get_asset_key(self, image_url: str) -> str:
        """Generate a unique key for an asset"""
        return hashlib.md5(image_url.encode()).hexdigest()
    
    def _is_cache_valid(self, asset_data: Dict[str, Any], max_age_hours: int = 24) -> bool:
        """Check if cached asset is still valid"""
        if 'timestamp' not in asset_data:
            return False
        
        cache_time = datetime.fromisoformat(asset_data['timestamp'])
        max_age = timedelta(hours=max_age_hours)
        return datetime.now() - cache_time < max_age
    
    def get_3d_asset(self, image_url: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Get 3D asset for an image, using cache when possible"""
        asset_key = self._get_asset_key(image_url)
        
        # Check cache first
        if not force_refresh and asset_key in self.cache:
            cached_asset = self.cache[asset_key]
            if self._is_cache_valid(cached_asset):
                logger.debug(f"Using cached 3D asset for {image_url}")
                return cached_asset
        
        # Generate new asset
        logger.info(f"Generating 3D asset for {image_url}")
        result = generate_3d_from_image(image_url)
        
        # Add metadata and cache
        asset_data = {
            "image_url": image_url,
            "result": result,
            "timestamp": datetime.now().isoformat(),
            "cache_key": asset_key
        }
        
        self.cache[asset_key] = asset_data
        self._save_cache()
        
        return asset_data
    
    def get_enhanced_3d_properties(self, device_type: str, manufacturer: str = None) -> Dict[str, Any]:
        """Get enhanced 3D properties for different device types"""
        properties = {
            "fortigate": {
                "shape": "box",
                "size": 1.2,
                "color": "#2563eb",
                "material": "metallic",
                "glow": True,
                "rotation_speed": 0.5
            },
            "fortiswitch": {
                "shape": "cylinder", 
                "size": 1.0,
                "color": "#059669",
                "material": "matte",
                "glow": False,
                "rotation_speed": 0.3
            },
            "endpoint": {
                "shape": "sphere",
                "size": 0.8,
                "color": "#7c3aed",
                "material": "plastic",
                "glow": False,
                "rotation_speed": 0.1
            },
            "server": {
                "shape": "box",
                "size": 1.1,
                "color": "#dc2626",
                "material": "metallic",
                "glow": True,
                "rotation_speed": 0.2
            }
        }
        
        # Get base properties
        base_props = properties.get(device_type, properties["endpoint"])
        
        # Enhance with manufacturer-specific properties
        if manufacturer:
            manufacturer_lower = manufacturer.lower()
            if "microsoft" in manufacturer_lower:
                base_props["color"] = "#00a4ef"
                base_props["material"] = "glass"
            elif "apple" in manufacturer_lower:
                base_props["color"] = "#a6b1b7"
                base_props["material"] = "metallic"
            elif "dell" in manufacturer_lower:
                base_props["color"] = "#007db8"
                base_props["material"] = "matte"
        
        return base_props
    
    def get_fallback_3d_representation(self, device_type: str, manufacturer: str = None) -> Dict[str, Any]:
        """Get fallback 3D representation when Eraser is not available"""
        properties = self.get_enhanced_3d_properties(device_type, manufacturer)
        
        return {
            "status": "fallback",
            "type": "enhanced_geometry",
            "properties": properties,
            "textureUrl": None,
            "modelUrl": None
        }
    
    def batch_generate_assets(self, image_urls: List[str]) -> Dict[str, Any]:
        """Generate 3D assets for multiple images"""
        results = {}
        
        for image_url in image_urls:
            try:
                asset_data = self.get_3d_asset(image_url)
                results[image_url] = asset_data
            except Exception as e:
                logger.error(f"Failed to generate asset for {image_url}: {e}")
                results[image_url] = {"error": str(e)}
        
        return results
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_assets = len(self.cache)
        valid_assets = sum(1 for asset in self.cache.values() if self._is_cache_valid(asset))
        
        return {
            "total_cached": total_assets,
            "valid_cached": valid_assets,
            "expired_cached": total_assets - valid_assets,
            "cache_file": self.cache_file,
            "eraser_enabled": is_enabled()
        }
    
    def clear_cache(self):
        """Clear the asset cache"""
        self.cache.clear()
        self._save_cache()
        logger.info("3D asset cache cleared")

# Global instance
_asset_manager = None

def get_3d_asset_manager() -> Asset3DManager:
    """Get global 3D asset manager instance"""
    global _asset_manager
    if _asset_manager is None:
        _asset_manager = Asset3DManager()
    return _asset_manager