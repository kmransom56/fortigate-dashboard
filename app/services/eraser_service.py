import os
import requests
from typing import Optional, Dict


def is_enabled() -> bool:
    return os.getenv("ERASER_ENABLED", "false").lower() == "true"


def _api_base() -> Optional[str]:
    return os.getenv("ERASER_API_URL")


def _api_key() -> Optional[str]:
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
        url = _api_base().rstrip("/") + "/v1/generate-3d"
        headers = {"Authorization": f"Bearer {_api_key()}", "Content-Type": "application/json"}
        payload = {"imageUrl": image_url, "output": "texture"}
        res = requests.post(url, json=payload, headers=headers, timeout=30)
        if res.status_code != 200:
            return {"status": "error", "code": res.status_code, "message": res.text[:200]}
        data = res.json()
        # Expected keys could be 'textureUrl' or 'modelUrl'
        return data
    except Exception as e:
        return {"status": "error", "message": str(e)}
