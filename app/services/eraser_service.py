import os
import requests
import logging
from typing import Optional, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


def is_enabled() -> bool:
    return os.getenv("ERASER_ENABLED", "false").lower() == "true"


def _api_base() -> Optional[str]:
    return os.getenv("ERASER_API_URL")


def _api_key() -> Optional[str]:
    """Read API key from file or environment variable"""
    # First try to read from file
    api_key_file = os.getenv("ERASER_API_KEY_FILE")
    if api_key_file and os.path.exists(api_key_file):
        try:
            with open(api_key_file, 'r') as f:
                return f.read().strip()
        except Exception as e:
            logger.warning(f"Could not read API key from file {api_key_file}: {e}")
    
    # Fallback to environment variable
    return os.getenv("ERASER_API_KEY")


def export_topology(payload: dict) -> dict:
    """Export or transform via Eraser.

    If an imageUrl is provided, attempt 3D texture generation.
    Otherwise, accept the payload (e.g., full topology) for future export.
    """
    image_url = None
    try:
        image_url = payload.get("imageUrl") if isinstance(payload, dict) else None
    except Exception:
        image_url = None

    if image_url:
        return generate_3d_from_image(image_url)

    # Fallback: acknowledge receipt
    return {"status": "accepted", "message": "Received topology payload"}


def generate_3d_from_image(image_url: str) -> Dict:
    """Send a 2D image to Eraser to generate a 3D asset.

    Returns a dictionary with keys like 'textureUrl' or 'modelUrl'.
    Fallback returns the original image as 'textureUrl' when ERASER is disabled or not configured.
    """
    if not image_url:
        return {"error": "no_image", "message": "image_url is required"}

    if not is_enabled() or not _api_base() or not _api_key():
        # Fallback: simply return the input as a texture to use as a billboard/box
        return {"status": "fallback", "textureUrl": image_url}

    try:
        # Try Eraser API endpoints for 3D generation
        endpoints = [
            "/api/render/prompt",
            "/api/render/elements"
        ]
        
        for endpoint in endpoints:
            try:
                url = _api_base().rstrip("/") + endpoint
                headers = {"Authorization": f"Bearer {_api_key()}", "Content-Type": "application/json"}
                
                # Different payload structures for different endpoints
                if endpoint == "/api/render/prompt":
                    # Eraser prompt-based rendering for 3D texture generation
                    payloads_to_try = [
                        # Format 1: Network device 3D texture generation
                        {
                            "text": f"Generate a 3D texture for this network device icon: {image_url}. Create a realistic 3D material texture that can be applied to a 3D model.",
                            "diagramType": "cloud-architecture-diagram",
                            "mode": "standard",
                            "theme": "dark",
                            "background": False
                        },
                        # Format 2: Simple 3D texture request
                        {
                            "text": f"Convert this network device icon to a 3D texture: {image_url}",
                            "diagramType": "cloud-architecture-diagram",
                            "mode": "standard"
                        },
                        # Format 3: Basic texture generation
                        {
                            "text": f"Create a 3D texture from this image: {image_url}",
                            "mode": "standard"
                        }
                    ]
                    
                    for i, payload in enumerate(payloads_to_try):
                        logger.info(f"Trying prompt payload format {i+1} for {endpoint}: {payload}")
                        res = requests.post(url, json=payload, headers=headers, timeout=15)
                        
                        if res.status_code == 200:
                            data = res.json()
                            return {"status": "success", "endpoint": endpoint, "payload_format": i+1, **data}
                        elif res.status_code != 404:
                            logger.warning(f"Prompt payload format {i+1} failed: {res.status_code} - {res.text[:200]}")
                elif endpoint == "/api/render/elements":
                    # Try Eraser DSL elements for 3D texture generation
                    payloads_to_try = [
                        # Format 1: Network device with 3D styling
                        {
                            "elements": [
                                {
                                    "type": "diagram",
                                    "diagramType": "cloud-architecture-diagram",
                                    "code": f"Device [icon: {image_url}, color: blue, style: 3d]\n\nDevice: Network device with 3D texture"
                                }
                            ],
                            "theme": "dark",
                            "background": False
                        },
                        # Format 2: Simple device representation
                        {
                            "elements": [
                                {
                                    "type": "diagram", 
                                    "diagramType": "cloud-architecture-diagram",
                                    "code": f"NetworkDevice [icon: {image_url}, color: gray]"
                                }
                            ]
                        }
                    ]
                    
                    for i, payload in enumerate(payloads_to_try):
                        logger.info(f"Trying payload format {i+1} for {endpoint}: {payload}")
                        res = requests.post(url, json=payload, headers=headers, timeout=15)
                        
                        if res.status_code == 200:
                            data = res.json()
                            return {"status": "success", "endpoint": endpoint, "payload_format": i+1, **data}
                        elif res.status_code != 404:
                            logger.warning(f"Payload format {i+1} failed: {res.status_code} - {res.text[:200]}")
                else:
                    payload = {"imageUrl": image_url, "output": "texture"}
                    res = requests.post(url, json=payload, headers=headers, timeout=15)
                
                if res.status_code == 200:
                    data = res.json()
                    return {"status": "success", "endpoint": endpoint, **data}
                elif res.status_code == 404:
                    continue  # Try next endpoint
                else:
                    # Log the full error for debugging
                    error_msg = res.text[:500] if res.text else "No response body"
                    logger.warning(f"Eraser API error for {endpoint}: {res.status_code} - {error_msg}")
                    return {"status": "error", "code": res.status_code, "message": error_msg, "endpoint": endpoint}
            except requests.exceptions.Timeout:
                continue  # Try next endpoint
            except requests.exceptions.RequestException:
                continue  # Try next endpoint
        
        # If all endpoints failed, return fallback
        return {"status": "fallback", "textureUrl": image_url, "message": "All API endpoints failed, using fallback"}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}
