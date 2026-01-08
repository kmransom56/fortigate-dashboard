"""
PowerInfer & TurboSparse Integration Module

This module provides easy access to PowerInfer and TurboSparse models
for fast local LLM inference (2-5× speedup).

Usage:
    from reusable.powerinfer import get_powerinfer_client, is_powerinfer_available
    
    # Check if PowerInfer is available
    if is_powerinfer_available():
        client = get_powerinfer_client()
        response = client.chat("Hello, how are you?")
"""

import os
from typing import Optional
from .powerinfer_client import PowerInferClient, PowerInferOllamaWrapper


def is_powerinfer_available(
    powerinfer_path: Optional[str] = None,
    model_path: Optional[str] = None
) -> bool:
    """
    Check if PowerInfer is available and ready to use.
    
    Args:
        powerinfer_path: Optional path to PowerInfer executable
        model_path: Optional path to TurboSparse model
        
    Returns:
        True if PowerInfer is available, False otherwise
    """
    # Use environment variables if paths not provided
    if not powerinfer_path:
        powerinfer_path = os.environ.get('POWERINFER_PATH')
    
    if not model_path:
        model_path = os.environ.get('POWERINFER_MODEL_PATH')
    
    # Try direct PowerInfer
    client = PowerInferClient(
        powerinfer_path=powerinfer_path,
        model_path=model_path
    )
    
    if client.is_available():
        return True
    
    # Try via Ollama (TurboSparse models in Ollama)
    wrapper = PowerInferOllamaWrapper()
    return wrapper.is_available()


def get_powerinfer_client(
    powerinfer_path: Optional[str] = None,
    model_path: Optional[str] = None,
    base_url: Optional[str] = None,
    prefer_ollama: bool = True
) -> Optional[PowerInferClient]:
    """
    Get a PowerInfer client instance.
    
    Args:
        powerinfer_path: Optional path to PowerInfer executable
        model_path: Optional path to TurboSparse model
        base_url: Optional PowerInfer API base URL
        prefer_ollama: If True, prefer TurboSparse via Ollama if available
        
    Returns:
        PowerInferClient instance or None if not available
    """
    # Use environment variables if paths not provided
    if not powerinfer_path:
        powerinfer_path = os.environ.get('POWERINFER_PATH')
    
    if not model_path:
        model_path = os.environ.get('POWERINFER_MODEL_PATH')
    
    if not base_url:
        base_url = os.environ.get('POWERINFER_BASE_URL')
    
    # Try via Ollama first if preferred
    if prefer_ollama:
        wrapper = PowerInferOllamaWrapper()
        if wrapper.is_available():
            return wrapper
    
    # Try direct PowerInfer
    client = PowerInferClient(
        powerinfer_path=powerinfer_path,
        model_path=model_path,
        base_url=base_url
    )
    
    if client.is_available():
        return client
    
    # Fallback to Ollama if direct PowerInfer not available
    if not prefer_ollama:
        wrapper = PowerInferOllamaWrapper()
        if wrapper.is_available():
            return wrapper
    
    return None


def list_turbosparse_models() -> list:
    """
    List available TurboSparse models.
    
    Returns:
        List of model paths or names
    """
    models = []
    
    # Check direct PowerInfer models
    client = PowerInferClient()
    direct_models = client.list_models()
    models.extend(direct_models)
    
    # Check TurboSparse models via Ollama
    wrapper = PowerInferOllamaWrapper()
    if wrapper.is_available():
        models.extend(wrapper.turbosparse_models)
    
    return models


def get_powerinfer_info() -> dict:
    """
    Get information about PowerInfer installation and available models.
    
    Returns:
        Dictionary with PowerInfer status information
    """
    info = {
        "powerinfer_available": False,
        "powerinfer_path": None,
        "model_path": None,
        "models_available": [],
        "via_ollama": False,
        "turbosparse_models": []
    }
    
    # Check environment variables
    powerinfer_path = os.environ.get('POWERINFER_PATH')
    model_path = os.environ.get('POWERINFER_MODEL_PATH')
    
    if powerinfer_path:
        info["powerinfer_path"] = powerinfer_path
        if os.path.exists(powerinfer_path):
            info["powerinfer_available"] = True
    
    if model_path:
        info["model_path"] = model_path
        if os.path.exists(model_path):
            info["models_available"].append(model_path)
    
    # Check direct PowerInfer
    client = PowerInferClient(
        powerinfer_path=powerinfer_path,
        model_path=model_path
    )
    
    if client.is_available():
        info["powerinfer_available"] = True
        if client.model_path:
            info["model_path"] = client.model_path
        models = client.list_models()
        info["models_available"].extend(models)
    
    # Check via Ollama
    wrapper = PowerInferOllamaWrapper()
    if wrapper.is_available():
        info["via_ollama"] = True
        info["turbosparse_models"] = wrapper.turbosparse_models
        info["powerinfer_available"] = True
    
    return info
