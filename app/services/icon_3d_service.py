"""
3D Icon Service with Eraser AI Integration

Generates 3D icons from 2D SVG files using Eraser AI API.
Provides caching, management, and conversion services for 3D network topology visualization.
"""

import os
import logging
import hashlib
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import asyncio
import aiohttp
from datetime import datetime, timedelta

from .eraser_service import generate_3d_from_image, is_enabled as eraser_enabled

logger = logging.getLogger(__name__)


class Icon3DService:
    """Service for managing 3D icon generation and caching"""

    def __init__(self):
        self.cache_dir = Path("app/static/icons/3d_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Cache file for 3D icon metadata
        self.cache_file = self.cache_dir / "3d_icons_cache.json"
        self.cache_data = self._load_cache()

        # Performance settings
        self.max_concurrent_requests = 5
        self.request_timeout = 30
        self.cache_ttl_days = 30

    def _load_cache(self) -> Dict[str, Any]:
        """Load 3D icon cache from disk"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load 3D icon cache: {e}")

        return {
            "icons": {},
            "last_updated": datetime.now().isoformat(),
            "stats": {
                "total_generated": 0,
                "cache_hits": 0,
                "cache_misses": 0,
                "eraser_requests": 0,
                "fallback_used": 0,
            },
        }

    def _save_cache(self):
        """Save 3D icon cache to disk"""
        try:
            self.cache_data["last_updated"] = datetime.now().isoformat()
            with open(self.cache_file, "w") as f:
                json.dump(self.cache_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save 3D icon cache: {e}")

    def _get_icon_hash(self, svg_path: str) -> str:
        """Generate hash for SVG file for caching"""
        try:
            # Use file path and modification time for hash
            stat = os.stat(svg_path)
            content = f"{svg_path}:{stat.st_mtime}:{stat.st_size}"
            return hashlib.md5(content.encode()).hexdigest()
        except Exception:
            return hashlib.md5(svg_path.encode()).hexdigest()

    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid"""
        try:
            created_at = datetime.fromisoformat(cache_entry.get("created_at", ""))
            return datetime.now() - created_at < timedelta(days=self.cache_ttl_days)
        except Exception:
            return False

    def get_3d_icon_data(
        self, svg_path: str, device_type: str, device_name: str = ""
    ) -> Dict[str, Any]:
        """
        Get 3D icon data for a given SVG file.

        Returns cached data if available, otherwise generates new 3D icon via Eraser AI.
        """
        if not os.path.exists(svg_path):
            logger.warning(f"SVG file not found: {svg_path}")
            return self._get_fallback_3d_data(device_type, device_name)

        icon_hash = self._get_icon_hash(svg_path)

        # Check cache first
        if icon_hash in self.cache_data["icons"]:
            cache_entry = self.cache_data["icons"][icon_hash]
            if self._is_cache_valid(cache_entry):
                self.cache_data["stats"]["cache_hits"] += 1
                logger.debug(f"Cache hit for {svg_path}")
                return cache_entry["data"]

        # Cache miss - generate new 3D icon
        self.cache_data["stats"]["cache_misses"] += 1
        logger.info(f"Generating 3D icon for {svg_path}")

        # Convert SVG to data URL for Eraser AI
        svg_data_url = self._svg_to_data_url(svg_path)
        if not svg_data_url:
            return self._get_fallback_3d_data(device_type, device_name)

        # Generate 3D icon via Eraser AI
        three_d_data = self._generate_3d_icon(svg_data_url, device_type, device_name)

        # Cache the result
        self.cache_data["icons"][icon_hash] = {
            "svg_path": svg_path,
            "device_type": device_type,
            "device_name": device_name,
            "data": three_d_data,
            "created_at": datetime.now().isoformat(),
        }

        self._save_cache()
        return three_d_data

    def _svg_to_data_url(self, svg_path: str) -> Optional[str]:
        """Convert SVG file to data URL"""
        try:
            with open(svg_path, "r", encoding="utf-8") as f:
                svg_content = f.read()

            # Clean and optimize SVG
            svg_content = svg_content.replace("\n", " ").replace("\t", " ")
            while "  " in svg_content:
                svg_content = svg_content.replace("  ", " ")

            # Create data URL
            import base64

            svg_bytes = svg_content.encode("utf-8")
            svg_base64 = base64.b64encode(svg_bytes).decode("utf-8")
            data_url = f"data:image/svg+xml;base64,{svg_base64}"

            return data_url
        except Exception as e:
            logger.error(f"Failed to convert SVG to data URL: {e}")
            return None

    def _generate_3d_icon(
        self, svg_data_url: str, device_type: str, device_name: str
    ) -> Dict[str, Any]:
        """Generate 3D icon using Eraser AI"""
        try:
            self.cache_data["stats"]["eraser_requests"] += 1

            if not eraser_enabled():
                logger.info("Eraser AI disabled, using fallback")
                self.cache_data["stats"]["fallback_used"] += 1
                return self._get_fallback_3d_data(
                    device_type, device_name, svg_data_url
                )

            # Call Eraser AI service
            result = generate_3d_from_image(svg_data_url)

            if result.get("status") == "success":
                logger.info(
                    f"Successfully generated 3D icon via Eraser AI for {device_type}"
                )
                return self._process_eraser_result(
                    result, device_type, device_name, svg_data_url
                )
            elif result.get("status") == "fallback":
                logger.info(f"Eraser AI fallback used for {device_type}")
                self.cache_data["stats"]["fallback_used"] += 1
                return self._get_fallback_3d_data(
                    device_type, device_name, svg_data_url
                )
            else:
                logger.warning(
                    f"Eraser AI generation failed for {device_type}: {result}"
                )
                self.cache_data["stats"]["fallback_used"] += 1
                return self._get_fallback_3d_data(
                    device_type, device_name, svg_data_url
                )

        except Exception as e:
            logger.error(f"Error generating 3D icon: {e}")
            self.cache_data["stats"]["fallback_used"] += 1
            return self._get_fallback_3d_data(device_type, device_name, svg_data_url)

    def _process_eraser_result(
        self,
        result: Dict[str, Any],
        device_type: str,
        device_name: str,
        svg_data_url: str,
    ) -> Dict[str, Any]:
        """Process successful Eraser AI result"""
        three_d_data = {
            "type": "eraser_generated",
            "device_type": device_type,
            "device_name": device_name,
            "original_svg": svg_data_url,
            "created_at": datetime.now().isoformat(),
            "eraser_endpoint": result.get("endpoint", "unknown"),
            "eraser_payload_format": result.get("payload_format", "unknown"),
        }

        # Extract useful data from Eraser response
        if "textureUrl" in result:
            three_d_data["texture_url"] = result["textureUrl"]

        if "modelUrl" in result:
            three_d_data["model_url"] = result["modelUrl"]

        if "imageUrl" in result:
            three_d_data["image_url"] = result["imageUrl"]

        # Add Three.js-compatible data
        three_d_data["threejs"] = {
            "geometry": self._get_3d_geometry(device_type),
            "material": {
                "type": "MeshPhongMaterial",
                "map": three_d_data.get("texture_url", svg_data_url),
                "transparent": True,
                "opacity": 0.9,
                "shininess": 30,
            },
            "scale": self._get_device_scale(device_type),
            "color": self._get_device_color(device_type),
        }

        return three_d_data

    def _get_fallback_3d_data(
        self, device_type: str, device_name: str, svg_data_url: str = None
    ) -> Dict[str, Any]:
        """Get fallback 3D data when Eraser AI is unavailable"""
        fallback_color = self._get_device_color(device_type)
        fallback_texture = svg_data_url or f"/static/icons/{device_type}.svg"

        return {
            "type": "fallback",
            "device_type": device_type,
            "device_name": device_name,
            "original_svg": svg_data_url,
            "created_at": datetime.now().isoformat(),
            "threejs": {
                "geometry": self._get_3d_geometry(device_type),
                "material": {
                    "type": "MeshPhongMaterial",
                    "map": fallback_texture,
                    "color": fallback_color,
                    "transparent": True,
                    "opacity": 0.8,
                    "shininess": 20,
                },
                "scale": self._get_device_scale(device_type),
                "color": fallback_color,
            },
        }

    def _get_3d_geometry(self, device_type: str) -> Dict[str, Any]:
        """Get appropriate 3D geometry for device type"""
        geometries = {
            "fortigate": {
                "type": "BoxGeometry",
                "args": [2, 0.5, 1.5],  # Firewall box shape
                "position": [0, 0.25, 0],
            },
            "fortiswitch": {
                "type": "BoxGeometry",
                "args": [3, 0.3, 0.8],  # Switch box shape
                "position": [0, 0.15, 0],
            },
            "fortiap": {
                "type": "CylinderGeometry",
                "args": [0.3, 0.3, 0.2, 8],  # Access point cylinder
                "position": [0, 0.1, 0],
            },
            "meraki_switch": {
                "type": "BoxGeometry",
                "args": [2.5, 0.3, 0.6],  # Meraki switch
                "position": [0, 0.15, 0],
            },
            "server": {
                "type": "BoxGeometry",
                "args": [1, 2, 1],  # Server tower
                "position": [0, 1, 0],
            },
            "endpoint": {
                "type": "BoxGeometry",
                "args": [0.8, 0.6, 0.8],  # Desktop/laptop
                "position": [0, 0.3, 0],
            },
            "restaurant_pos": {
                "type": "BoxGeometry",
                "args": [1.2, 0.8, 0.3],  # POS terminal
                "position": [0, 0.4, 0],
            },
            "restaurant_camera": {
                "type": "SphereGeometry",
                "args": [0.2, 16, 12],  # Security camera
                "position": [0, 0.2, 0],
            },
        }

        return geometries.get(device_type, geometries["endpoint"])

    def _get_device_scale(self, device_type: str) -> List[float]:
        """Get scale factors for different device types"""
        scales = {
            "fortigate": [1.0, 1.0, 1.0],
            "fortiswitch": [1.2, 1.0, 1.0],
            "fortiap": [0.8, 0.8, 0.8],
            "meraki_switch": [1.1, 1.0, 0.9],
            "server": [0.8, 1.2, 0.8],
            "endpoint": [0.7, 0.7, 0.7],
            "restaurant_pos": [0.9, 1.0, 0.8],
            "restaurant_camera": [0.6, 0.6, 0.6],
        }
        return scales.get(device_type, [1.0, 1.0, 1.0])

    def _get_device_color(self, device_type: str) -> str:
        """Get color for different device types"""
        colors = {
            "fortigate": "#FF6B35",  # Fortinet orange
            "fortiswitch": "#4A90E2",  # Blue
            "fortiap": "#7ED321",  # Green
            "meraki_switch": "#50E3C2",  # Meraki teal
            "server": "#9013FE",  # Purple
            "endpoint": "#757575",  # Gray
            "restaurant_pos": "#FF9800",  # Orange
            "restaurant_camera": "#F44336",  # Red
        }
        return colors.get(device_type, "#757575")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = self.cache_data["stats"].copy()
        stats.update(
            {
                "cached_icons_count": len(self.cache_data["icons"]),
                "cache_size_mb": self._get_cache_size_mb(),
                "last_updated": self.cache_data.get("last_updated"),
                "eraser_enabled": eraser_enabled(),
            }
        )
        return stats

    def _get_cache_size_mb(self) -> float:
        """Calculate cache directory size in MB"""
        try:
            total_size = 0
            for path in self.cache_dir.rglob("*"):
                if path.is_file():
                    total_size += path.stat().st_size
            return round(total_size / (1024 * 1024), 2)
        except Exception:
            return 0.0

    def cleanup_expired_cache(self) -> int:
        """Remove expired cache entries"""
        removed_count = 0
        icons_to_remove = []

        for icon_hash, cache_entry in self.cache_data["icons"].items():
            if not self._is_cache_valid(cache_entry):
                icons_to_remove.append(icon_hash)

        for icon_hash in icons_to_remove:
            del self.cache_data["icons"][icon_hash]
            removed_count += 1

        if removed_count > 0:
            self._save_cache()
            logger.info(f"Removed {removed_count} expired 3D icon cache entries")

        return removed_count

    async def batch_generate_3d_icons(
        self, svg_paths: List[Tuple[str, str, str]]
    ) -> Dict[str, Any]:
        """
        Batch generate 3D icons for multiple SVG files.

        Args:
            svg_paths: List of (svg_path, device_type, device_name) tuples

        Returns:
            Dictionary with results and statistics
        """
        logger.info(f"Starting batch 3D icon generation for {len(svg_paths)} icons")

        semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        results = {}

        async def generate_single_icon(
            svg_path: str, device_type: str, device_name: str
        ):
            async with semaphore:
                try:
                    # Run sync method in thread pool
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None, self.get_3d_icon_data, svg_path, device_type, device_name
                    )
                    return svg_path, result
                except Exception as e:
                    logger.error(f"Failed to generate 3D icon for {svg_path}: {e}")
                    return svg_path, self._get_fallback_3d_data(
                        device_type, device_name
                    )

        # Execute batch generation
        tasks = [
            generate_single_icon(svg_path, device_type, device_name)
            for svg_path, device_type, device_name in svg_paths
        ]

        start_time = time.time()
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        # Process results
        for task_result in completed_tasks:
            if isinstance(task_result, Exception):
                logger.error(f"Batch task failed: {task_result}")
                continue

            svg_path, icon_data = task_result
            results[svg_path] = icon_data

        batch_stats = {
            "total_icons": len(svg_paths),
            "successful": len(results),
            "failed": len(svg_paths) - len(results),
            "duration_seconds": round(end_time - start_time, 2),
            "cache_stats": self.get_cache_stats(),
        }

        logger.info(f"Batch 3D icon generation completed: {batch_stats}")

        return {"results": results, "stats": batch_stats}


# Global service instance
_icon_3d_service = None


def get_3d_icon_service() -> Icon3DService:
    """Get the global 3D icon service instance"""
    global _icon_3d_service
    if _icon_3d_service is None:
        _icon_3d_service = Icon3DService()
    return _icon_3d_service
