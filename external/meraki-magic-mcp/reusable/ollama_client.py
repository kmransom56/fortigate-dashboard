"""
Ollama Client - Local LLM support without API keys
"""

import requests
import json
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for local Ollama LLM service"""
    
    def __init__(self, base_url: str = None, model: str = None):
        """
        Initialize Ollama client
        
        Args:
            base_url: Ollama API base URL (auto-detected if None)
            model: Model name (auto-detected if None)
        """
        if base_url is None:
            # Try to detect Ollama port (common: 11435, 11434)
            for port in [11435, 11434]:
                try:
                    test_url = f"http://localhost:{port}/api/tags"
                    response = requests.get(test_url, timeout=1)
                    if response.status_code == 200:
                        base_url = f"http://localhost:{port}"
                        break
                except:
                    continue
            if base_url is None:
                base_url = "http://localhost:11434"  # Default fallback
        
        self.base_url = base_url.rstrip('/')
        self.model = model or self._detect_model()
    
    def _detect_model(self) -> str:
        """Auto-detect available model (prefer CodeLLaMA, then LLM)"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                
                # Prefer CodeLLaMA for code tasks
                for name in model_names:
                    if "codellama" in name.lower() or "deepseek-coder" in name.lower() or "qwen2.5-coder" in name.lower():
                        return name
                
                # Then prefer LLM/Llama models
                for name in model_names:
                    if "llm" in name.lower() or "llama" in name.lower():
                        return name
                
                # Use first available model
                if model_names:
                    return model_names[0]
        except Exception as e:
            logger.warning(f"Could not detect Ollama model: {e}")
        
        # Default fallback
        return "codellama:7b"  # Common default for code
    
    def is_available(self) -> bool:
        """Check if Ollama is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except Exception:
            return False
    
    def chat(self, message: str, system_prompt: Optional[str] = None, 
             model: Optional[str] = None) -> Optional[str]:
        """
        Send a chat message to Ollama
        
        Args:
            message: User message
            system_prompt: Optional system prompt
            model: Model to use (uses default if None)
            
        Returns:
            Response text or None if failed
        """
        if not self.is_available():
            logger.error("Ollama is not available")
            return None
        
        model = model or self.model
        
        try:
            payload = {
                "model": model,
                "messages": []
            }
            
            if system_prompt:
                payload["messages"].append({
                    "role": "system",
                    "content": system_prompt
                })
            
            payload["messages"].append({
                "role": "user",
                "content": message
            })
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                # Ollama returns messages in a stream-like format
                if "message" in result:
                    return result["message"].get("content", "")
                elif "response" in result:
                    return result["response"]
            
            logger.error(f"Ollama API error: {response.status_code} - {response.text}")
            return None
            
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            return None
    
    def generate(self, prompt: str, model: Optional[str] = None) -> Optional[str]:
        """
        Generate text from prompt
        
        Args:
            prompt: Input prompt
            model: Model to use (uses default if None)
            
        Returns:
            Generated text or None if failed
        """
        return self.chat(prompt, model=model)
    
    def list_models(self) -> List[str]:
        """List available models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [m.get("name", "") for m in models]
        except Exception:
            pass
        return []
